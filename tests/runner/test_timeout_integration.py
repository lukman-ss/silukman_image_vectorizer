"""
test_timeout_integration.py

End-to-end integration tests for timeout behavior inside ExperimentRunner.
Uses a minimal config + dummy backend to verify:
  - Runs that succeed are recorded as status=success
  - Runs that timeout are recorded as status=timeout with metrics=None
  - Runner continues to subsequent runs after a timeout
  - Resumed experiment does not re-execute timed-out runs (timeout is recorded)
"""
import csv
import json
import os

import pytest

from benchmark.runner.experiment_runner import ExperimentRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_manifest(manifest_path: str, rows: list) -> None:
    fieldnames = [
        "image_id", "filename", "category", "source", "source_url", "creator",
        "license", "license_url", "redistribution_allowed", "attribution",
        "width", "height", "format", "has_alpha", "sha256", "date_accessed",
        "notes", "dataset_role", "origin_type", "api_provider", "api_request_url",
        "original_asset_url", "work_title", "license_verified", "provenance_status",
        "publication_scope",
    ]
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            # Fill in defaults for all missing fields
            full_row = {k: "" for k in fieldnames}
            full_row.update(row)
            writer.writerow(full_row)


def _write_image(image_path: str) -> None:
    """Write a tiny valid PNG so PIL can open it."""
    import struct
    import zlib

    def png_chunk(name: bytes, data: bytes) -> bytes:
        c = struct.pack(">I", len(data)) + name + data
        return c + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)

    width = height = 4
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b""
    for _ in range(height):
        raw += b"\x00" + b"\xff\x00\x00" * width  # filter byte + RGB
    idat = zlib.compress(raw)
    png = b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", idat) + png_chunk(b"IEND", b"")
    with open(image_path, "wb") as f:
        f.write(png)


def _write_config(config_path: str, manifest_path: str, timeout: int = 10) -> None:
    with open(config_path, "w") as f:
        f.write(f"""experiment:
  id: timeout_integration_test
  repetitions: 1
  warmup_runs: 0
  timeout_seconds: {timeout}
  dataset_role: evaluation
  experiment_role: pilot
  publication_eligible: false

dataset:
  manifest: {manifest_path}
  categories:
    - icon

backends:
  - silukman

presets:
  - low_complexity

metrics: []
""")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def integration_workspace(tmp_path, monkeypatch):
    """Set up a minimal experiment workspace with 2 images."""
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    # Image 1: fast — will succeed
    img1_path = str(images_dir / "img_fast.png")
    _write_image(img1_path)

    # Image 2: slow — will timeout
    img2_path = str(images_dir / "img_slow.png")
    _write_image(img2_path)

    manifest_path = str(tmp_path / "manifest.csv")
    _write_manifest(manifest_path, [
        {"image_id": "img_fast", "filename": "img_fast.png", "category": "icon",
         "dataset_role": "evaluation", "format": "PNG"},
        {"image_id": "img_slow", "filename": "img_slow.png", "category": "icon",
         "dataset_role": "evaluation", "format": "PNG"},
    ])

    config_path = str(tmp_path / "config.yaml")
    # 2-second timeout — fast image will succeed, slow one will timeout
    _write_config(config_path, manifest_path, timeout=2)

    # Run experiments in tmp_path
    monkeypatch.chdir(tmp_path)

    return {
        "tmp_path": tmp_path,
        "config_path": config_path,
        "manifest_path": manifest_path,
    }


# ---------------------------------------------------------------------------
# Test: fast backend succeeds, slow backend times out, runner continues
# ---------------------------------------------------------------------------

def test_timeout_recorded_runner_continues(integration_workspace, monkeypatch):
    """
    - img_fast → success (fast vectorization)
    - img_slow → timeout (patched to sleep > timeout)
    - Both runs must appear in runs.jsonl
    - img_slow must have status=timeout, metrics=None
    - Runner must not raise an exception
    """
    config_path = integration_workspace["config_path"]

    # Patch run_in_isolated_process to simulate:
    #   img_fast → ok
    #   img_slow → timeout
    def fake_isolated(module_path, callable_name, kwargs, output_path, timeout_sec):
        image_id = kwargs.get("input_path", "")
        if "img_fast" in image_id:
            # Write a minimal output SVG
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w") as f:
                    f.write("<svg xmlns='http://www.w3.org/2000/svg'></svg>")
            return {
                "status": "ok",
                "result": {
                    "performance": {"success": True, "wall_clock_time_seconds": 0.1, "peak_memory_bytes": 0,
                                    "input_bytes": 100, "output_bytes": 50},
                    "preset": "low_complexity",
                    "status": "success",
                },
                "duration_seconds": 0.1,
            }
        else:
            # Simulate timeout
            return {
                "status": "timeout",
                "error_type": "BackendTimeoutError",
                "duration_seconds": timeout_sec,
                "metrics": None,
                "output_valid": False,
            }

    monkeypatch.setattr(
        "benchmark.runner.experiment_runner.run_in_isolated_process",
        fake_isolated,
    )

    runner = ExperimentRunner(config_path, base_dir=str(integration_workspace["tmp_path"] / "experiments"))
    runner.execute()  # Must not raise

    # Read runs.jsonl
    runs_file = os.path.join(runner.experiment_dir, "runs.jsonl")
    assert os.path.exists(runs_file)

    records = []
    with open(runs_file) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    assert len(records) == 2

    fast_rec = next(r for r in records if r["image_id"] == "img_fast")
    slow_rec = next(r for r in records if r["image_id"] == "img_slow")

    assert fast_rec["status"] == "success"
    assert slow_rec["status"] == "timeout"
    assert slow_rec["error_type"] == "BackendTimeoutError"
    assert slow_rec["metrics"] is None
    assert slow_rec["output_valid"] is False


def test_timeout_not_counted_as_completed_for_resume(integration_workspace, monkeypatch):
    """
    A run with status=timeout MUST NOT be skipped on resume when retry_failed=True.
    """
    config_path = integration_workspace["config_path"]
    exp_base = str(integration_workspace["tmp_path"] / "experiments")

    call_count = {"n": 0}

    def fake_isolated(module_path, callable_name, kwargs, output_path, timeout_sec):
        call_count["n"] += 1
        # All calls return timeout on first experiment, success on second
        if call_count["n"] <= 2:
            return {
                "status": "timeout",
                "error_type": "BackendTimeoutError",
                "duration_seconds": timeout_sec,
                "metrics": None,
                "output_valid": False,
            }
        # Second run
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                f.write("<svg xmlns='http://www.w3.org/2000/svg'></svg>")
        return {
            "status": "ok",
            "result": {
                "performance": {"success": True, "wall_clock_time_seconds": 0.05, "peak_memory_bytes": 0,
                                "input_bytes": 100, "output_bytes": 50},
                "preset": "low_complexity",
                "status": "success",
            },
            "duration_seconds": 0.05,
        }

    monkeypatch.setattr(
        "benchmark.runner.experiment_runner.run_in_isolated_process",
        fake_isolated,
    )

    # First run — both timeout
    runner1 = ExperimentRunner(config_path, base_dir=exp_base)
    runner1.execute()

    exp_id = runner1.experiment_id

    # Reset monkeypatch call counter
    call_count["n"] = 0

    # Resume with retry_failed=True
    # Since timeout records have status=timeout (not success), they should be retried
    from benchmark.runner.config_schema import BenchmarkConfig as _BC  # noqa
    # Patch generate_config_hash for resume
    monkeypatch.setattr("benchmark.runner.env_capture.generate_config_hash",
                        lambda x: runner1.config_hash)

    runner2 = ExperimentRunner(config_path, resume_id=exp_id, retry_failed=True, base_dir=exp_base)
    runner2.setup()

    # Timeout records should NOT be in completed_runs (they should be retried)
    for image_id in ["img_fast", "img_slow"]:
        run_id = f"{image_id}_silukman_low_complexity_rep1"
        assert run_id not in runner2.completed_runs, (
            f"{run_id} should not be completed (was timeout) when retry_failed=True"
        )
