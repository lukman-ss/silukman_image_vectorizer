import pytest

from app.config.preset_manager import PresetManager, get_preset
from app.config.settings import VectorizationConfig


def test_preset_manager_loads_available_presets():
    """Verify PresetManager loads the presets.json file."""
    manager = PresetManager.get_instance()
    presets = manager.get_available_presets()
    
    assert "low_complexity" in presets
    assert "balanced" in presets
    assert "high_fidelity" in presets


def test_preset_manager_metadata():
    """Verify PresetManager returns purpose and trade-offs."""
    manager = PresetManager.get_instance()
    info = manager.get_preset_info("low_complexity")
    
    assert "purpose" in info
    assert "trade_off" in info
    assert len(info["purpose"]) > 10
    assert len(info["trade_off"]) > 10


def test_all_presets_are_valid():
    """Verify that every preset in presets.json can be loaded into VectorizationConfig."""
    manager = PresetManager.get_instance()
    presets = manager.get_available_presets()
    
    for preset_name in presets:
        # Should not raise any validation ValueError from __post_init__
        config = manager.get_preset_config(preset_name)
        assert isinstance(config, VectorizationConfig)


def test_get_preset_convenience_function():
    """Verify get_preset() works."""
    config = get_preset("balanced")
    assert config.engine_type == "VTracer"
    assert config.color_count == 24


def test_invalid_preset():
    """Verify asking for an invalid preset raises ValueError."""
    with pytest.raises(ValueError):
        get_preset("non_existent_preset_name")
