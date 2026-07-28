import json
import pytest

from app.config.settings import VectorizationConfig, VectorizationSettings


def test_default_config():
    """Verify default config instantiates without validation errors."""
    config = VectorizationConfig()
    assert config.engine_type == "VTracer"
    assert config.colormode == "color"
    assert config.color_precision == 6
    assert config.splice_threshold == 45


def test_invalid_choices():
    """Verify validation catches invalid enum-like string choices."""
    with pytest.raises(ValueError, match="Invalid value for engine_type"):
        VectorizationConfig(engine_type="UnknownEngine")
        
    with pytest.raises(ValueError, match="Invalid value for colormode"):
        VectorizationConfig(colormode="grayscale")


def test_invalid_ranges():
    """Verify validation catches out-of-range numeric values."""
    with pytest.raises(ValueError, match="Must be between"):
        VectorizationConfig(color_count=300)
        
    with pytest.raises(ValueError, match="Must be between"):
        VectorizationConfig(corner_threshold=200)
        
    with pytest.raises(ValueError, match="Must be between"):
        VectorizationConfig(path_precision=-1)


def test_json_roundtrip():
    """Verify config can be serialized to and from JSON losslessly."""
    config = VectorizationConfig(
        engine_type="OpenCV Legacy",
        color_precision=8,
        corner_threshold=45,
        palette_replacements=[((255, 255, 255), (0, 0, 0))]
    )
    
    json_str = config.to_json()
    assert isinstance(json_str, str)
    
    restored_config = VectorizationConfig.from_json(json_str)
    
    assert restored_config.engine_type == "OpenCV Legacy"
    assert restored_config.color_precision == 8
    assert restored_config.corner_threshold == 45
    assert restored_config.palette_replacements == [((255, 255, 255), (0, 0, 0))]
    
    # Fully equivalent
    assert restored_config == config


def test_backward_compatibility():
    """Verify that older VectorizationSettings format can be loaded into the new model."""
    old_settings_dict = {
        "engine_type": "VTracer",
        "min_area": 150.0,
        "vtracer": {
            "colormode": "binary",
            "filter_speckle": 8
        },
        "unknown_legacy_key": "should_be_ignored"
    }
    
    # Should not raise exception about unknown keys
    config = VectorizationConfig.from_dict(old_settings_dict)
    
    assert config.engine_type == "VTracer"
    assert config.min_area == 150.0
    assert config.colormode == "binary"
    assert config.filter_speckle == 8
    
    # Test vtracer property backward compatibility
    assert config.vtracer.colormode == "binary"
    
    # Verify alias works
    assert VectorizationSettings is VectorizationConfig
