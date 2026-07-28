import pytest
from app.config.preset_manager import PresetManager
from benchmark.runner.config_schema import BenchmarkConfig

def test_preset_loading():
    pm = PresetManager.get_instance()
    presets = pm.get_available_presets()
    assert "balanced" in presets
    assert "low_complexity" in presets
    assert "high_fidelity" in presets
    
    balanced = pm.get_preset_config("balanced")
    assert hasattr(balanced, "colormode")
    assert hasattr(balanced, "hierarchical")
    assert hasattr(balanced, "mode")
    assert hasattr(balanced, "filter_speckle")
    assert hasattr(balanced, "color_precision")
    assert hasattr(balanced, "layer_difference")
    assert hasattr(balanced, "corner_threshold")
    assert hasattr(balanced, "length_threshold")
    assert hasattr(balanced, "max_iterations")
    assert hasattr(balanced, "splice_threshold")
    assert hasattr(balanced, "path_precision")

def test_config_validation(tmp_path):
    valid_yaml = """
experiment:
  id: "test-123"
  repetitions: 1
dataset:
  manifest: "dataset.csv"
  split: "test"
backends:
  - silukman
presets:
  - balanced
metrics:
  - ssim
"""
    cfg_file = tmp_path / "valid.yaml"
    cfg_file.write_text(valid_yaml)
    
    cfg = BenchmarkConfig.from_yaml(str(cfg_file))
    assert cfg.experiment.id == "test-123"
    assert cfg.dataset.manifest == "dataset.csv"
    assert "silukman" in cfg.backends
    assert "balanced" in cfg.presets
    assert "ssim" in cfg.metrics

