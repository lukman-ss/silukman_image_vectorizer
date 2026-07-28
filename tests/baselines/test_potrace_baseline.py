import json
import os
import numpy as np
import cv2
import pytest

from benchmark.baselines.potrace_baseline import PotraceBaselineRunner


@pytest.fixture
def mock_image(tmp_path):
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    img[2:8, 2:8] = 255 # White square in black background
    img_path = tmp_path / "test.png"
    cv2.imwrite(str(img_path), img)
    return str(img_path)


def test_potrace_skip_category(mock_image, tmp_path):
    runner = PotraceBaselineRunner()
    
    runner.potrace_version = "mock_version"
    
    out_svg = tmp_path / "out.svg"
    result = runner.run(mock_image, str(out_svg), "photograph")
    
    assert "error" in result
    assert "Skipped" in result["error"]
    assert "unfair" in result["error"]


def test_potrace_baseline_execution(mock_image, tmp_path, monkeypatch):
    runner = PotraceBaselineRunner()
    
    # We mock the _run_cli function so we don't actually need potrace installed to pass the unit test.
    def mock_run_cli(bmp_path, svg_path, timeout_sec):
        # Fake creating the SVG file
        with open(svg_path, "w") as f:
            f.write("<svg></svg>")
            
    monkeypatch.setattr(runner, "_run_cli", mock_run_cli)
    
    # Force version so it doesn't fail early if not installed
    runner.potrace_version = "potrace 1.16"
    
    out_svg = tmp_path / "out.svg"
    result = runner.run(mock_image, str(out_svg), "binary_graphic")
    
    assert "error" not in result
    assert result["potrace_version"] == "potrace 1.16"
    assert "performance" in result
    assert result["performance"]["success"] is True
    
    # Preprocessing test: verify it actually tried to process it (mock_run_cli creates out.svg)
    assert os.path.exists(str(out_svg))
    
    json.dumps(result)
