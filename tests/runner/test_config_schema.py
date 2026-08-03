import pytest

from benchmark.runner.config_schema import BenchmarkConfig, ConfigError


def test_valid_parallelism(tmp_path):
    config_yaml = """
    experiment:
      id: "test"
      parallelism: 2
    dataset:
      manifest: "dummy.csv"
    backends:
      - name: "inkscape"
    presets:
      - name: "default"
    """
    p = tmp_path / "config.yaml"
    p.write_text(config_yaml)
    config = BenchmarkConfig.from_yaml(str(p))
    assert config.experiment.parallelism == 2


def test_invalid_parallelism_zero(tmp_path):
    config_yaml = """
    experiment:
      id: "test"
      parallelism: 0
    dataset:
      manifest: "dummy.csv"
    backends:
      - name: "inkscape"
    presets:
      - name: "default"
    """
    p = tmp_path / "config.yaml"
    p.write_text(config_yaml)
    with pytest.raises(ConfigError, match="parallelism must be at least 1"):
        BenchmarkConfig.from_yaml(str(p))


def test_invalid_parallelism_negative(tmp_path):
    config_yaml = """
    experiment:
      id: "test"
      parallelism: -1
    dataset:
      manifest: "dummy.csv"
    backends:
      - name: "inkscape"
    presets:
      - name: "default"
    """
    p = tmp_path / "config.yaml"
    p.write_text(config_yaml)
    with pytest.raises(ConfigError, match="parallelism must be at least 1"):
        BenchmarkConfig.from_yaml(str(p))
