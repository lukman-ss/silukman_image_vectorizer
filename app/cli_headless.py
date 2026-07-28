import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from app.config.preset_manager import PresetManager
from app.config.settings import VectorizationSettings
from app.core.vectorization_service import vectorize_image


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="silukman-vectorizer",
        description="Headless Command Line Interface for Silukman Image Vectorizer.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # GUI Command
    parser_gui = subparsers.add_parser("gui", help="Start the graphical user interface")

    # Presets Command
    parser_presets = subparsers.add_parser("presets", help="List available vectorization presets")
    parser_presets.add_argument("--json", action="store_true", help="Output presets as JSON")

    # Vectorize Command
    parser_vectorize = subparsers.add_parser("vectorize", help="Vectorize a single image")
    parser_vectorize.add_argument("input", help="Path to the input image file")
    parser_vectorize.add_argument("--output", "-o", help="Path to the output SVG file (optional)")
    parser_vectorize.add_argument(
        "--preset", "-p", help="Preset name to use (default: balanced)", default="balanced"
    )
    parser_vectorize.add_argument(
        "--config", "-c", help="Path to custom JSON config file (overrides preset)"
    )
    parser_vectorize.add_argument("--json", action="store_true", help="Output results as JSON")
    parser_vectorize.add_argument(
        "--dry-run", action="store_true", help="Simulate without executing"
    )

    # Batch Command
    parser_batch = subparsers.add_parser("batch", help="Batch vectorize a directory of images")
    parser_batch.add_argument("input_dir", help="Path to the directory containing input images")
    parser_batch.add_argument(
        "--output-dir", "-o", required=True, help="Path to the output directory for SVGs"
    )
    parser_batch.add_argument(
        "--preset", "-p", help="Preset name to use (default: balanced)", default="balanced"
    )
    parser_batch.add_argument(
        "--config", "-c", help="Path to custom JSON config file (overrides preset)"
    )
    parser_batch.add_argument("--json", action="store_true", help="Output results as JSON")
    parser_batch.add_argument(
        "--workers", type=int, default=2, help="Number of parallel workers (default: 2)"
    )
    parser_batch.add_argument(
        "--resume", action="store_true", help="Skip files already present in output"
    )
    parser_batch.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing output files"
    )
    parser_batch.add_argument(
        "--ext", help="Comma-separated extensions to include (e.g., .png,.jpg)"
    )

    # Inspect Command
    parser_inspect = subparsers.add_parser("inspect", help="Inspect an SVG output file")
    parser_inspect.add_argument("input", help="Path to the SVG file to inspect")
    parser_inspect.add_argument("--json", action="store_true", help="Output results as JSON")

    # Benchmark Command
    parser_benchmark = subparsers.add_parser("benchmark", help="Run benchmark experiments")
    benchmark_subs = parser_benchmark.add_subparsers(
        dest="benchmark_command", help="Benchmark subcommands"
    )
    parser_bench_run = benchmark_subs.add_parser("run", help="Run an experiment configuration")
    parser_bench_run.add_argument(
        "--config", "-c", required=True, help="Path to experiment YAML configuration"
    )
    parser_bench_run.add_argument(
        "--resume-id", help="Experiment ID to resume (e.g., 20260728T..._hash)"
    )
    parser_bench_run.add_argument(
        "--retry-failed",
        action="store_true",
        help="If resuming, retry failed runs instead of skipping them",
    )

    parser_bench_agg = benchmark_subs.add_parser(
        "aggregate", help="Aggregate benchmark raw JSONL results"
    )
    parser_bench_agg.add_argument("--input", "-i", required=True, help="Path to runs.jsonl")
    parser_bench_agg.add_argument(
        "--output", "-o", required=True, help="Path to save aggregated summary JSON"
    )

    parser_bench_paired = benchmark_subs.add_parser(
        "paired", help="Run paired comparison between two configs"
    )
    parser_bench_paired.add_argument("--input", "-i", required=True, help="Path to aggregated.json")
    parser_bench_paired.add_argument(
        "--output", "-o", required=True, help="Path to save paired report JSON"
    )
    parser_bench_paired.add_argument(
        "--config-a", required=True, help="Config A (format: backend:preset)"
    )
    parser_bench_paired.add_argument(
        "--config-b", required=True, help="Config B (format: backend:preset)"
    )
    parser_bench_paired.add_argument(
        "--metrics", required=True, help="Comma-separated metrics (e.g. ssim,rmse,edge_f1)"
    )

    parser_bench_pareto = benchmark_subs.add_parser(
        "pareto", help="Run Pareto frontier trade-off analysis"
    )
    parser_bench_pareto.add_argument("--input", "-i", required=True, help="Path to aggregated.json")
    parser_bench_pareto.add_argument(
        "--output", "-o", required=True, help="Path to save pareto report JSON"
    )

    parser_bench_cat = benchmark_subs.add_parser("category", help="Run Category analysis")
    parser_bench_cat.add_argument("--input", "-i", required=True, help="Path to aggregated.json")
    parser_bench_cat.add_argument(
        "--output", "-o", required=True, help="Path to save category report JSON"
    )

    parser_bench_fail = benchmark_subs.add_parser("failure", help="Run Failure analysis")
    parser_bench_fail.add_argument("--input", "-i", required=True, help="Path to runs.jsonl")
    parser_bench_fail.add_argument(
        "--output", "-o", required=True, help="Path to save failure report JSON"
    )

    parser_bench_tabs = benchmark_subs.add_parser(
        "generate-tables", help="Generate CSV/MD/LaTeX tables"
    )
    parser_bench_tabs.add_argument("--exp-dir", required=True, help="Path to experiment directory")

    parser_bench_plots = benchmark_subs.add_parser(
        "generate-plots", help="Generate publication plots"
    )
    parser_bench_plots.add_argument("--exp-dir", required=True, help="Path to experiment directory")

    parser_bench_report = benchmark_subs.add_parser(
        "report", help="Generate automatic comprehensive report"
    )
    parser_bench_report.add_argument("--run", required=True, help="Path to experiment directory")

    return parser


def _load_settings(preset_name: str, config_path: Optional[str] = None) -> VectorizationSettings:
    if config_path:
        return VectorizationSettings.from_json(config_path)

    preset_manager = PresetManager.get_instance()
    try:
        return preset_manager.get_preset_config(preset_name)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_gui() -> int:
    try:
        from app.cli import main as gui_main

        return gui_main()
    except Exception as e:
        print(f"Failed to start GUI: {e}", file=sys.stderr)
        return 1


def cmd_presets(args: argparse.Namespace) -> int:
    preset_manager = PresetManager.get_instance()
    presets = preset_manager.get_available_presets()

    if args.json:
        data = []
        for name in presets:
            try:
                config = preset_manager.get_preset_config(name)
                data.append({"name": name, "config": json.loads(config.to_json())})
            except Exception:
                pass
        print(json.dumps(data, indent=2))
    else:
        print("Available Presets:")
        for name in presets:
            print(f"  - {name}")
    return 0


def cmd_vectorize(args: argparse.Namespace) -> int:
    input_path = args.input
    output_path = args.output
    if not output_path:
        base, _ = os.path.splitext(input_path)
        output_path = f"{base}_vectorized.svg"

    settings = _load_settings(args.preset, args.config)

    if args.dry_run:
        engine = settings.engine_type
        config_dump = json.loads(settings.to_json())
        out_exists = os.path.exists(output_path)

        info = {
            "mode": "dry-run",
            "input_path": input_path,
            "output_path": output_path,
            "preset_used": args.preset,
            "backend": engine,
            "overwrite_policy": "Overwrite existing" if out_exists else "Create new",
            "preprocessing": [
                f"Grayscale threshold: {settings.threshold_val}",
                f"Remove BG: {settings.remove_background}",
            ],
            "configuration": config_dump,
        }

        if args.json:
            print(json.dumps(info, indent=2))
        else:
            print("--- DRY RUN ---")
            print(f"Input: {input_path}")
            print(f"Output: {output_path} ({'Will overwrite' if out_exists else 'New file'})")
            print(f"Preset: {args.preset or 'custom'}")
            print(f"Backend: {engine}")
            print("Preprocessing:")
            for p in info["preprocessing"]:
                print(f"  - {p}")
            print("Final Configuration:")
            print(json.dumps(config_dump, indent=2))
            print("--- END DRY RUN ---")
        return 0

    try:
        result = vectorize_image(input_path, output_path, settings)
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e), "success": False}, indent=2))
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.json:
        print(result.to_json())
    else:
        if result.status == "success":
            print(f"Success! Vectorized {input_path} to {output_path}")
            print(f"Paths: {result.path_count}, Elements: {result.element_count}")
            print(f"Duration: {result.duration_seconds:.2f}s")
            if getattr(result, "warnings", None):
                print("Warnings:")
                for w in result.warnings:
                    print(f"  - {w}")
        else:
            print(f"Failed: {result.error_message}")
            return 1

    return 0 if result.status == "success" else 1


def cmd_batch(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if args.resume and args.overwrite:
        print("Error: --resume and --overwrite are mutually exclusive.", file=sys.stderr)
        return 1

    if not input_dir.is_dir():
        print(f"Error: Input directory {input_dir} does not exist.", file=sys.stderr)
        return 1

    outputs_dir = output_dir / "outputs"
    logs_dir = output_dir / "logs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    settings = _load_settings(args.preset, args.config)
    with open(output_dir / "config.json", "w") as f:
        f.write(settings.to_json())

    if args.ext:
        supported_exts = {ext.strip().lower() for ext in args.ext.split(",")}
    else:
        supported_exts = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}

    files = sorted(
        [f for f in input_dir.iterdir() if f.is_file() and f.suffix.lower() in supported_exts]
    )

    if not files:
        print(f"No supported image files found in {input_dir}.", file=sys.stderr)
        return 0

    manifest = [str(f.resolve()) for f in files]
    with open(output_dir / "manifest.json", "w") as f:
        json.dump({"files": manifest, "count": len(manifest)}, f, indent=2)

    import concurrent.futures
    import threading
    import traceback

    runs_path = output_dir / "runs.jsonl"

    # Resume logic
    processed_files = set()
    if args.resume and runs_path.exists():
        with open(runs_path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    processed_files.add(data.get("input_path"))
                except json.JSONDecodeError:
                    pass

    results = []
    success_count = 0
    fail_count = 0
    lock = threading.Lock()

    def process_file(file_path: Path):
        out_path = outputs_dir / f"{file_path.stem}_vectorized.svg"
        log_path = logs_dir / f"{file_path.stem}.log"

        str_in = str(file_path.resolve())
        if args.resume and str_in in processed_files:
            return {"input_path": str_in, "status": "skipped", "reason": "resume"}

        if out_path.exists() and not args.overwrite and not args.resume:
            return {"input_path": str_in, "status": "skipped", "reason": "exists"}

        try:
            result = vectorize_image(str_in, str(out_path), settings)
            res_dict = json.loads(result.to_json())
            res_dict["status"] = "success" if result.status == "success" else "failed"
            return res_dict
        except Exception as e:
            with open(log_path, "w") as log_f:
                log_f.write(traceback.format_exc())
            return {"input_path": str_in, "status": "failed", "error_message": str(e)}

    if not args.json:
        print(f"Starting batch process: {len(files)} files, {args.workers} workers")

    # We append to runs.jsonl (if not appending, we would rewrite it, but for robust experimental runs append is better).
    # Since we support overwrite/resume, we open in append mode.
    runs_mode = "a" if args.resume else "w"

    with open(runs_path, runs_mode) as runs_file:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_file = {executor.submit(process_file, f): f for f in files}

            for i, future in enumerate(concurrent.futures.as_completed(future_to_file)):
                file_path = future_to_file[future]
                try:
                    data = future.result()
                    with lock:
                        if data["status"] == "success":
                            success_count += 1
                        elif data["status"] == "failed":
                            fail_count += 1

                        if data["status"] != "skipped":
                            runs_file.write(json.dumps(data) + "\n")
                            runs_file.flush()
                            results.append(data)

                        if not args.json:
                            print(f"[{i+1}/{len(files)}] {file_path.name}: {data['status']}")
                except Exception as exc:
                    with lock:
                        fail_count += 1
                        print(f"[{i+1}/{len(files)}] {file_path.name}: CRITICAL ERROR {exc}")

    summary = {
        "total_processed": success_count + fail_count,
        "success": success_count,
        "failed": fail_count,
    }
    with open(output_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"Batch processing complete.")
        print(f"Success: {success_count}, Failed: {fail_count}")
        print(f"Outputs written to {outputs_dir}")

    return 0 if fail_count == 0 else 1


def cmd_inspect(args: argparse.Namespace) -> int:
    input_path = args.input

    try:
        from app.core.postprocessing import calculate_svg_metrics, parse_and_validate_svg

        with open(input_path, "r", encoding="utf-8") as f:
            svg_data = f.read()

        root = parse_and_validate_svg(svg_data)
        metrics = calculate_svg_metrics(root)

        width = root.get("width", "unknown")
        height = root.get("height", "unknown")
        viewbox = root.get("viewBox", "unknown")

        output_metrics = {
            "is_valid_xml": True,
            "is_valid_svg_root": True,
            "width": width,
            "height": height,
            "viewbox": viewbox,
            "path_count": metrics.get("path_count", 0),
            "element_count": metrics.get("total_elements", 0),
        }

        if args.json:
            print(json.dumps(output_metrics, indent=2))
        else:
            print(f"SVG Inspection for: {input_path}")
            print(f"  Valid XML: {output_metrics['is_valid_xml']}")
            print(f"  Valid SVG Root: {output_metrics['is_valid_svg_root']}")
            print(f"  Dimensions: {width}x{height}")
            print(f"  Path Count: {output_metrics['path_count']}")
            print(f"  Total Elements: {output_metrics['element_count']}")
            print(f"  ViewBox: {viewbox}")
        return 0
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e), "success": False}, indent=2))
        else:
            print(f"Inspect Error: {e}", file=sys.stderr)
        return 1


def cmd_benchmark(args: argparse.Namespace) -> int:
    if args.benchmark_command == "run":
        try:
            from benchmark.runner.experiment_runner import ExperimentRunner

            runner = ExperimentRunner(
                config_path=args.config, resume_id=args.resume_id, retry_failed=args.retry_failed
            )
            runner.execute()
            return 0
        except Exception as e:
            print(f"Benchmark Error: {e}", file=sys.stderr)
            return 1
    elif args.benchmark_command == "aggregate":
        try:
            from benchmark.analysis.aggregator import BenchmarkAggregator

            agg = BenchmarkAggregator(args.input)
            agg.save(args.output)
            print(f"Successfully aggregated {args.input} to {args.output}")
            return 0
        except Exception as e:
            print(f"Aggregation Error: {e}", file=sys.stderr)
            return 1
    elif args.benchmark_command == "paired":
        try:
            from benchmark.analysis.paired_analysis import PairedComparison

            ca = tuple(args.config_a.split(":"))
            cb = tuple(args.config_b.split(":"))
            metrics = [m.strip() for m in args.metrics.split(",")]

            comp = PairedComparison(args.input)
            comp.save_report(ca, cb, metrics, args.output)
            print(f"Successfully generated paired comparison report to {args.output}")
            return 0
        except Exception as e:
            print(f"Paired Analysis Error: {e}", file=sys.stderr)
            return 1
    elif args.benchmark_command == "pareto":
        try:
            from benchmark.analysis.pareto_frontier import ParetoFrontier

            pareto = ParetoFrontier(args.input)
            pareto.analyze_tradeoffs(args.output)
            print(f"Successfully generated Pareto frontier report to {args.output}")
            return 0
        except Exception as e:
            print(f"Pareto Analysis Error: {e}", file=sys.stderr)
            return 1
    elif args.benchmark_command == "category":
        try:
            from benchmark.analysis.category_analysis import CategoryAnalyzer

            analyzer = CategoryAnalyzer(args.input)
            analyzer.save_report(args.output)
            print(f"Successfully generated Category analysis report to {args.output}")
            return 0
        except Exception as e:
            print(f"Category Analysis Error: {e}", file=sys.stderr)
            return 1
    elif args.benchmark_command == "failure":
        try:
            from benchmark.analysis.failure_analysis import FailureAnalyzer

            fail_analyzer = FailureAnalyzer(args.input)
            fail_analyzer.save_report(args.output)
            print(f"Successfully generated Failure analysis report to {args.output}")
            return 0
        except Exception as e:
            print(f"Failure Analysis Error: {e}", file=sys.stderr)
            return 1
    elif args.benchmark_command == "generate-tables":
        try:
            from benchmark.analysis.table_generator import TableGenerator

            gen = TableGenerator(args.exp_dir)
            gen.generate_all()
            return 0
        except Exception as e:
            print(f"Table Generation Error: {e}", file=sys.stderr)
            return 1
    elif args.benchmark_command == "generate-plots":
        try:
            from benchmark.analysis.plot_generator import PlotGenerator

            plot_gen = PlotGenerator(args.exp_dir)
            plot_gen.generate_all()
            return 0
        except Exception as e:
            print(f"Plot Generation Error: {e}", file=sys.stderr)
            return 1
    elif args.benchmark_command == "report":
        try:
            from benchmark.analysis.report_generator import ReportGenerator

            rep = ReportGenerator(args.run)
            rep.run()
            return 0
        except Exception as e:
            print(f"Report Generation Error: {e}", file=sys.stderr)
            return 1
    else:
        print("Invalid benchmark command.", file=sys.stderr)
        return 1


def main(args: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 1
        
    as_json = getattr(parsed_args, "json", False)
    from app.core.logging import setup_logger
    logger = setup_logger("silukman", as_json=as_json)
    
    if parsed_args.command == "gui":
        return cmd_gui()
    elif parsed_args.command == "presets":
        return cmd_presets(parsed_args)
    elif parsed_args.command == "vectorize":
        return cmd_vectorize(parsed_args)
    elif parsed_args.command == "batch":
        return cmd_batch(parsed_args)
    elif parsed_args.command == "inspect":
        return cmd_inspect(parsed_args)
    elif parsed_args.command == "benchmark":
        return cmd_benchmark(parsed_args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
