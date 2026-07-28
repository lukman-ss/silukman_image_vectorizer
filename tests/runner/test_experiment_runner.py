import json
import os

import pytest

from benchmark.runner.experiment_runner import ExperimentRunner


@pytest.fixture
def dummy_experiment(tmp_path):
    # Setup dummy experiments directory
    exp_dir = tmp_path / "experiments" / "20260728T000000Z_test-exp_abcdef_123456"
    exp_dir.mkdir(parents=True)

    # Create a dummy config
    config_path = tmp_path / "test-config.yaml"
    with open(config_path, "w") as f:
        f.write(
            """
experiment:
  id: test-exp
dataset:
  manifest: foo.csv
backends:
  - silukman
presets:
  - balanced
metrics:
  - mae
        """
        )

    runs_file = exp_dir / "runs.jsonl"
    with open(runs_file, "w") as f:
        # 1 valid run
        f.write(json.dumps({"run_id": "img1_silukman_balanced_rep1", "status": "success"}) + "\n")
        # 1 failed run
        f.write(json.dumps({"run_id": "img2_silukman_balanced_rep1", "status": "failed"}) + "\n")
        # 1 truncated line (simulating crash)
        f.write('{"run_id": "img3_silukm')

    return {
        "exp_dir": exp_dir,
        "config_path": str(config_path),
        "resume_id": "20260728T000000Z_test-exp_abcdef_123456",
        "runs_file": str(runs_file),
    }


def test_resume_filters_completed_runs(dummy_experiment, monkeypatch):
    # Mock config hash to avoid hash mismatch
    monkeypatch.setattr("benchmark.runner.env_capture.generate_config_hash", lambda x: "123456")

    # Change CWD for the test so experiments folder maps correctly
    monkeypatch.chdir(dummy_experiment["exp_dir"].parent.parent)

    runner = ExperimentRunner(
        dummy_experiment["config_path"], dummy_experiment["resume_id"], retry_failed=False
    )
    runner.setup()

    # Should contain img1 and img2, because retry_failed is False (so it considers failed as completed)
    assert "img1_silukman_balanced_rep1" in runner.completed_runs
    assert "img2_silukman_balanced_rep1" in runner.completed_runs

    # Truncated line should be ignored
    assert "img3_silukm" not in runner.completed_runs


def test_resume_retry_failed(dummy_experiment, monkeypatch):
    monkeypatch.setattr("benchmark.runner.env_capture.generate_config_hash", lambda x: "123456")
    monkeypatch.chdir(dummy_experiment["exp_dir"].parent.parent)

    runner = ExperimentRunner(
        dummy_experiment["config_path"], dummy_experiment["resume_id"], retry_failed=True
    )
    runner.setup()

    # Should only contain img1. img2 is failed so it should NOT be in completed_runs (meaning it will be retried)
    assert "img1_silukman_balanced_rep1" in runner.completed_runs
    assert "img2_silukman_balanced_rep1" not in runner.completed_runs


def test_resume_hash_mismatch(dummy_experiment, monkeypatch):
    # Mock a DIFFERENT config hash
    monkeypatch.setattr("benchmark.runner.env_capture.generate_config_hash", lambda x: "badhash")
    monkeypatch.chdir(dummy_experiment["exp_dir"].parent.parent)

    with pytest.raises(ValueError) as exc:
        ExperimentRunner(dummy_experiment["config_path"], dummy_experiment["resume_id"])

    assert "Config hash mismatch!" in str(exc.value)
