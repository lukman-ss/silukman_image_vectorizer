"""
Tests for publication eligibility, results isolation, and config consistency.
"""
import os
import json
import glob
import yaml
import pytest
import tempfile
from benchmark.analysis.aggregator import BenchmarkAggregator


# ---- Aggregator publication eligibility tests ----

def test_aggregator_rejects_smoke_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_file = os.path.join(tmpdir, "runs.jsonl")
        manifest_file = os.path.join(tmpdir, "manifest.json")

        with open(runs_file, "w") as f:
            f.write('{"status": "success"}\n')

        with open(manifest_file, "w") as f:
            json.dump({
                "publication_eligible": False,
                "dataset_role": "testing_only",
                "experiment_role": "smoke",
            }, f)

        with pytest.raises(ValueError, match="is not publication eligible"):
            BenchmarkAggregator(runs_file)


def test_aggregator_accepts_publication_eligible():
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_file = os.path.join(tmpdir, "runs.jsonl")
        manifest_file = os.path.join(tmpdir, "manifest.json")

        with open(runs_file, "w") as f:
            f.write('{"status": "success"}\n')

        with open(manifest_file, "w") as f:
            json.dump({"publication_eligible": True}, f)

        agg = BenchmarkAggregator(runs_file)
        assert agg.runs_file == runs_file


def test_aggregator_testing_only_rejected():
    """dataset_role=testing_only must be rejected when publication_eligible=false."""
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_file = os.path.join(tmpdir, "runs.jsonl")
        manifest_file = os.path.join(tmpdir, "manifest.json")

        with open(runs_file, "w") as f:
            f.write('{"status": "success"}\n')

        with open(manifest_file, "w") as f:
            json.dump({"publication_eligible": False, "dataset_role": "testing_only"}, f)

        with pytest.raises(ValueError):
            BenchmarkAggregator(runs_file)


# ---- Results isolation tests ----

def test_smoke_results_not_in_root():
    """
    Verify that no experiment directories exist directly in benchmark/results/.
    All experiments must be under smoke/ or evaluation/.
    """
    results_root = "benchmark/results"
    if not os.path.exists(results_root):
        pytest.skip("benchmark/results not found")

    allowed_subdirs = {"smoke", "evaluation", "diversity", "pilot", "scaling_pilot"}
    for entry in os.listdir(results_root):
        full_path = os.path.join(results_root, entry)
        if os.path.isdir(full_path):
            assert entry in allowed_subdirs, (
                f"Unexpected experiment directory in root results: {entry}. "
                "All experiments must be under smoke/, evaluation/, diversity/, pilot/, or scaling_pilot/."
            )


def test_smoke_manifests_not_publication_eligible():
    """All smoke result manifests must have publication_eligible=false."""
    smoke_root = "benchmark/results/smoke"
    if not os.path.exists(smoke_root):
        pytest.skip("No smoke results directory")

    for manifest_path in glob.glob(os.path.join(smoke_root, "*", "manifest.json")):
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert manifest.get("publication_eligible") is False, (
            f"Smoke result {manifest_path} has publication_eligible=True — not allowed."
        )


def test_evaluation_dir_exists():
    """benchmark/results/evaluation/ must exist for future real-world results."""
    assert os.path.isdir("benchmark/results/evaluation"), (
        "benchmark/results/evaluation/ must exist."
    )


# ---- Config consistency tests ----

def test_benchmark_config_repetitions():
    """benchmark-v1.yaml must have repetitions >= 3."""
    config_path = "experiments/configs/benchmark-v1.yaml"
    if not os.path.exists(config_path):
        pytest.skip(f"Config not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    repetitions = data.get("experiment", {}).get("repetitions", 0)
    assert repetitions >= 3, (
        f"benchmark-v1.yaml repetitions={repetitions} must be >= 3 (protocol requirement)"
    )


def test_benchmark_config_warmup():
    """benchmark-v1.yaml must have warmup_runs >= 1."""
    config_path = "experiments/configs/benchmark-v1.yaml"
    if not os.path.exists(config_path):
        pytest.skip(f"Config not found: {config_path}")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    warmup = data.get("experiment", {}).get("warmup_runs", 0)
    assert warmup >= 1, (
        f"benchmark-v1.yaml warmup_runs={warmup} must be >= 1 (protocol requirement)"
    )


def test_manuscript_uses_placeholders_not_hardcoded():
    """
    manuscript.md must not contain hardcoded repetition values like '1 repetitions'
    or '1 measured runs'. These must be replaced with [REPETITION_COUNT] and [WARMUP_COUNT].
    """
    manuscript_path = "paper/manuscript.md"
    if not os.path.exists(manuscript_path):
        pytest.skip("manuscript.md not found")

    with open(manuscript_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for suspicious hardcoded patterns that should be placeholders
    assert "` 1` measured runs" not in content, (
        "Found hardcoded '1 measured runs' in manuscript — use [REPETITION_COUNT]"
    )
    assert "`1` measured repetitions" not in content, (
        "Found hardcoded '1 measured repetitions' in manuscript — use [REPETITION_COUNT]"
    )
    assert "× 1 repetitions`" not in content, (
        "Found hardcoded '× 1 repetitions' in manuscript — use [REPETITION_COUNT]"
    )
    assert "[REPETITION_COUNT]" in content, (
        "manuscript.md must contain [REPETITION_COUNT] placeholder"
    )
    assert "[WARMUP_COUNT]" in content, (
        "manuscript.md must contain [WARMUP_COUNT] placeholder"
    )


# ---- Dataset curator validation ----

def test_dataset_curator_rejects_empty_license():
    """dataset add must reject empty licenses."""
    from app.services.dataset_curator import cmd_add
    import argparse

    args = argparse.Namespace(
        file="nonexistent.png",
        category="icon",
        source_url="https://example.com",
        creator="Test",
        license="",
        license_url="https://example.com/license",
        dry_run=True,
    )
    result = cmd_add(args)
    assert result == 1, "cmd_add must return 1 for empty license"


def test_dataset_curator_rejects_invalid_license():
    """dataset add must reject non-approved licenses."""
    from app.services.dataset_curator import cmd_add
    import argparse

    args = argparse.Namespace(
        file="nonexistent.png",
        category="icon",
        source_url="https://example.com",
        creator="Test",
        license="All Rights Reserved",
        license_url="https://example.com/license",
        dry_run=True,
    )
    result = cmd_add(args)
    assert result == 1, "cmd_add must reject non-approved license"
