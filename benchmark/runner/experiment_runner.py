import csv
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


from benchmark.baselines.backends import (
    InkscapeBackend,
    PotraceBackend,
    SilukmanBackend,
    VTracerBackend,
)
from benchmark.evaluation.unified_evaluator import UnifiedQualityEvaluator
from benchmark.runner.config_schema import BenchmarkConfig
from benchmark.runner.env_capture import capture_environment, get_git_info
from app.core.logging import logger


class ExperimentRunner:
    def __init__(
        self,
        config_path: str,
        resume_id: Optional[str] = None,
        retry_failed: bool = False,
        base_dir: str = "experiments",
    ):
        self.config_path = config_path
        self.config = BenchmarkConfig.from_yaml(config_path)
        self.retry_failed = retry_failed
        self.base_dir = base_dir

        from benchmark.runner.env_capture import generate_config_hash

        self.config_hash = generate_config_hash(self.config_path)

        self.experiment_id = self._setup_experiment_id(resume_id)  # type: ignore[arg-type] # complex typing/external library
        self.experiment_dir = os.path.join(self.base_dir, self.experiment_id)

        self.runs_file = os.path.join(self.experiment_dir, "runs.jsonl")
        self.summary_file = os.path.join(self.experiment_dir, "summary.json")
        self.manifest_copy = os.path.join(self.experiment_dir, "manifest.json")
        self.logs_dir = os.path.join(self.experiment_dir, "logs")
        self.outputs_dir = os.path.join(self.experiment_dir, "outputs")

        self.backends = self._initialize_backends()
        self.evaluator = UnifiedQualityEvaluator(temp_dir=os.path.join(self.experiment_dir, "tmp"))

        # Tracking states
        self.completed_runs: Set[str] = set()

    def _initialize_backends(self) -> dict:
        registry = {
            "silukman": SilukmanBackend(),
            "vtracer": VTracerBackend(),
            "potrace": PotraceBackend(timeout=self.config.experiment.timeout_seconds),
            "inkscape": InkscapeBackend(timeout=self.config.experiment.timeout_seconds),
        }

        active_backends = {}
        for b_name in self.config.backends:
            b_name = b_name.lower()
            if b_name not in registry:
                logger.warning(f"Unknown backend '{b_name}'. Skipping.", extra={"backend": b_name})
                continue

            backend = registry[b_name]
            if not backend.is_available():
                logger.warning(f"Backend '{b_name}' is not available on this system. Skipping.", extra={"backend": b_name})
                continue

            active_backends[b_name] = backend

        if not active_backends:
            raise RuntimeError("No valid backends available to run.")

        return active_backends

    def _setup_experiment_id(self, resume_id: str) -> str:
        if resume_id:
            exp_dir = os.path.join(self.base_dir, resume_id)
            if not os.path.exists(exp_dir):
                raise ValueError(f"Cannot resume: Experiment directory '{exp_dir}' does not exist.")

            # Extract config hash from the ID or check manifest (ID format: timestamp_name_sha_hash)
            parts = resume_id.split("_")
            if len(parts) >= 4:
                old_hash = parts[-1]
                if old_hash != self.config_hash:
                    raise ValueError(
                        f"Config hash mismatch! Original: {old_hash}, Current: {self.config_hash}. Cannot resume with modified config."
                    )
            return resume_id

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        exp_name = self.config.experiment.id
        git_info = get_git_info()
        short_sha = git_info.get("short_commit", "unknown")

        return f"{timestamp}_{exp_name}_{short_sha}_{self.config_hash}"

    def _load_dataset(self) -> List[dict]:
        manifest_path = self.config.dataset.manifest
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Dataset manifest not found: {manifest_path}")

        dataset = []
        category_counts = {}
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cat = row.get("category")
                if (
                    row.get("dataset_role") == self.config.experiment.dataset_role
                    and cat in self.config.dataset.categories
                ):
                    if self.config.dataset.max_samples_per_category > 0:
                        if category_counts.get(cat, 0) >= self.config.dataset.max_samples_per_category:
                            continue
                        category_counts[cat] = category_counts.get(cat, 0) + 1
                    
                    dataset.append(row)
        return dataset

    def _run_warmups(self, test_image: str):
        if self.config.experiment.warmup_runs <= 0:
            return

        logger.info("Running warm-ups...")
        # Warmup uses the first preset
        preset = self.config.presets[0]
        for name, backend in self.backends.items():
            for _ in range(self.config.experiment.warmup_runs):
                tmp_out = os.path.join(self.experiment_dir, "tmp", f"warmup_{name}.svg")
                try:
                    backend.vectorize(test_image, tmp_out, preset)
                except Exception:
                    pass

    def _get_run_id(self, image_id: str, backend_name: str, preset: str, rep: int) -> str:
        return f"{image_id}_{backend_name}_{preset}_rep{rep}"

    def _load_completed_runs(self):
        if os.path.exists(self.runs_file):
            valid_lines = []
            with open(self.runs_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        run_id = data.get("run_id")
                        status = data.get("status")
                        if run_id:
                            # Skip adding to completed if retry_failed is true and status was failed
                            if self.retry_failed and status == "failed":
                                continue
                            self.completed_runs.add(run_id)
                        valid_lines.append(line)
                    except json.JSONDecodeError:
                        logger.warning("Detected truncated or invalid JSONL line during resume recovery. Ignoring line.")

            # Rewrite clean runs if we recovered from truncation
            with open(self.runs_file, "w", encoding="utf-8") as f:
                for v in valid_lines:
                    f.write(v)

    def setup(self):
        is_resume = os.path.exists(self.experiment_dir)

        os.makedirs(self.experiment_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.outputs_dir, exist_ok=True)

        if is_resume:
            self._load_completed_runs()

            # Append resume event to manifest (load and rewrite)
            if os.path.exists(self.manifest_copy):
                with open(self.manifest_copy, "r", encoding="utf-8") as f:
                    manifest_data = json.load(f)

                resumes = manifest_data.get("resumed_at", [])
                resumes.append(datetime.now(timezone.utc).isoformat())
                manifest_data["resumed_at"] = resumes

                with open(self.manifest_copy, "w", encoding="utf-8") as f:
                    json.dump(manifest_data, f, indent=2)
            return

        # Save experiment config + system info as manifest
        manifest_data = {
            "experiment_id": self.experiment_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "environment": capture_environment(),
            "resumed_at": [],
            "experiment_config": {
                "id": self.config.experiment.id,
                "repetitions": self.config.experiment.repetitions,
                "dataset_split": self.config.dataset.split,
                "active_backends": list(self.backends.keys()),
            },
        }

        with open(self.manifest_copy, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        self._load_completed_runs()

    def execute(self):
        self.setup()

        dataset = self._load_dataset()
        if not dataset:
            logger.info("Dataset empty for the given filters.")
            return

        base_img_dir = os.path.dirname(self.config.dataset.manifest)

        # Try to find a valid image for warmup
        test_img = os.path.join(base_img_dir, dataset[0]["file_path"])
        self._run_warmups(test_img)

        total_tasks = (
            len(dataset)
            * len(self.backends)
            * len(self.config.presets)
            * self.config.experiment.repetitions
        )
        completed = 0
        success_count = 0
        fail_count = 0

        logger.info(f"Starting execution: {total_tasks} total tasks.", extra={"experiment_id": self.experiment_id})

        with open(self.runs_file, "a", encoding="utf-8") as rf:
            for item in dataset:
                image_id = item["image_id"]
                category = item["category"]
                input_path = os.path.join(base_img_dir, item["file_path"])

                for b_name, backend in self.backends.items():
                    for preset in self.config.presets:
                        for rep in range(1, self.config.experiment.repetitions + 1):
                            run_id = self._get_run_id(image_id, b_name, preset, rep)

                            if run_id in self.completed_runs:
                                completed += 1
                                continue

                            logger.info(f"[{completed+1}/{total_tasks}] Running {run_id} ...", extra={
                                "run_id": run_id, "experiment_id": self.experiment_id,
                                "image_id": image_id, "backend": b_name, "preset": preset
                            })

                            output_filename = f"{run_id}.svg"
                            output_path = os.path.join(self.outputs_dir, output_filename)

                            # 1. Run Vectorization
                            vectorize_result = backend.vectorize(
                                input_path, output_path, preset, category=category
                            )

                            # Check if skipped or failed
                            err1 = vectorize_result.get("error") or ""
                            err2 = vectorize_result.get("performance", {}).get("error") or ""
                            is_skipped = str(err1).startswith("Skipped") or str(err2).startswith(
                                "Skipped"
                            )

                            from app.core.result import calculate_file_hash

                            input_hash = item.get("sha256") or calculate_file_hash(input_path)

                            base_record = {
                                "experiment_id": self.experiment_id,
                                "run_id": run_id,
                                "repetition": rep,
                                "image_id": image_id,
                                "category": category,
                                "backend": b_name,
                                "preset": preset,
                                "config_hash": self.config_hash,
                                "input_hash": input_hash,
                                "output_hash": None,
                                "status": "unknown",
                                "errors": [],
                                "environment_reference": "manifest.json",
                            }

                            # 2. Evaluation
                            if not is_skipped and vectorize_result.get("performance", {}).get(
                                "success", False
                            ):
                                eval_record = self.evaluator.evaluate(
                                    image_id=image_id,
                                    preset=preset,
                                    original_raster_path=input_path,
                                    svg_path=output_path,
                                    performance_data=vectorize_result.get("performance"),
                                )

                                base_record.update(eval_record)
                                base_record["status"] = "success"
                                base_record["output_hash"] = (
                                    calculate_file_hash(output_path)
                                    if os.path.exists(output_path)
                                    else None
                                )
                                base_record["vectorize_metadata"] = {
                                    k: v for k, v in vectorize_result.items() if k != "performance"
                                }
                                success_count += 1
                            else:
                                # Failed or skipped
                                base_record["status"] = "skipped" if is_skipped else "failed"
                                err = vectorize_result.get("error") or vectorize_result.get(
                                    "performance", {}
                                ).get("error")
                                if err:
                                    base_record["errors"].append(err)
                                if not is_skipped:
                                    fail_count += 1
                                logger.error(f"Run {run_id} failed", extra={
                                    "run_id": run_id, "experiment_id": self.experiment_id,
                                    "image_id": image_id, "backend": b_name, "preset": preset,
                                    "error_category": base_record["error_type"] if "error_type" in base_record else "VectorizationError"
                                })

                            # Save to runs (Immutable record format)
                            rf.write(json.dumps(base_record) + "\n")
                            rf.flush()
                            self.completed_runs.add(run_id)
                            completed += 1

        self.generate_summary()

    def generate_summary(self):
        summary: Dict[str, Any] = {"total_runs": len(self.completed_runs), "backend_stats": {}}

        with open(self.runs_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    b_name = data.get("backend")
                    if not b_name:
                        continue

                    if b_name not in summary["backend_stats"]:
                        summary["backend_stats"][b_name] = {"success": 0, "failed": 0, "skipped": 0}

                    if data.get("status") == "skipped":
                        summary["backend_stats"][b_name]["skipped"] += 1
                    elif data.get("status") == "failed" or len(data.get("errors", [])) > 0:
                        summary["backend_stats"][b_name]["failed"] += 1
                    else:
                        summary["backend_stats"][b_name]["success"] += 1
                except json.JSONDecodeError:
                    pass

        with open(self.summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"Experiment completed. Summary saved to {self.summary_file}")
