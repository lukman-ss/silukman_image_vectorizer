import os

import cv2
import numpy as np
import pytest

from benchmark.baselines.vtracer_baseline import VTracerBaselineRunner


@pytest.fixture
def mock_raster(tmp_path):
    img = np.full((10, 10, 3), 128, dtype=np.uint8)
    raster_path = tmp_path / "test.png"
    cv2.imwrite(str(raster_path), img)
    return str(raster_path)


def test_vtracer_baseline(mock_raster, tmp_path):
    runner = VTracerBaselineRunner()

    out_svg = tmp_path / "out.svg"

    # We use 'balanced' which is present in app/config/presets.json
    result = runner.run(mock_raster, str(out_svg), "balanced")

    assert "error" not in result.get("performance", {}) or result["performance"]["error"] is None

    # Check mapping
    assert "vtracer_parameters" in result
    assert "filter_speckle" in result["vtracer_parameters"]
    assert "unmapped_silukman_parameters" in result
    assert "color_count" in result["unmapped_silukman_parameters"]
    assert "engine_type" in result["unmapped_silukman_parameters"]

    assert result["performance"]["success"] is True
    assert result["performance"]["wall_clock_time_seconds"] > 0
    assert result["preset"] == "balanced"

    assert os.path.exists(str(out_svg))
