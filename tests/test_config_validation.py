import pytest
import yaml
import tempfile
from pathlib import Path
from benchmark.runner.config_schema import BenchmarkConfig, ConfigError

def test_full_benchmark_requires_3_repetitions():
    config = {
        "experiment": {
            "id": "test",
            "repetitions": 2,
            "warmup_runs": 1,
            "experiment_role": "full_benchmark",
            "dataset_role": "evaluation"
        },
        "dataset": {"manifest": "real_world.csv"},
        "backends": ["silukman"],
        "presets": ["default"]
    }
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        filepath = f.name
    
    with pytest.raises(ConfigError, match="repetitions must be at least 3 for full_benchmark"):
        BenchmarkConfig.from_yaml(filepath)


def test_full_benchmark_requires_1_warmup():
    config = {
        "experiment": {
            "id": "test",
            "repetitions": 3,
            "warmup_runs": 0,
            "experiment_role": "full_benchmark",
            "dataset_role": "evaluation"
        },
        "dataset": {"manifest": "real_world.csv"},
        "backends": ["silukman"],
        "presets": ["default"]
    }
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        filepath = f.name
    
    with pytest.raises(ConfigError, match="warmup_runs must be at least 1 for full_benchmark"):
        BenchmarkConfig.from_yaml(filepath)


def test_full_benchmark_rejects_testing_only():
    config = {
        "experiment": {
            "id": "test",
            "repetitions": 3,
            "warmup_runs": 1,
            "experiment_role": "full_benchmark",
            "dataset_role": "testing_only"
        },
        "dataset": {"manifest": "real_world.csv"},
        "backends": ["silukman"],
        "presets": ["default"]
    }
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        filepath = f.name
    
    with pytest.raises(ConfigError, match="dataset_role cannot be testing_only for full_benchmark"):
        BenchmarkConfig.from_yaml(filepath)


def test_publication_eligible_rejects_synthetic():
    config = {
        "experiment": {
            "id": "test",
            "repetitions": 3,
            "warmup_runs": 1,
            "experiment_role": "full_benchmark",
            "dataset_role": "evaluation",
            "publication_eligible": True
        },
        "dataset": {"manifest": "benchmark/datasets/synthetic/dataset_manifest.csv"},
        "backends": ["silukman"],
        "presets": ["default"]
    }
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        filepath = f.name
    
    with pytest.raises(ConfigError, match="publication_eligible cannot be true with a synthetic dataset manifest"):
        BenchmarkConfig.from_yaml(filepath)
