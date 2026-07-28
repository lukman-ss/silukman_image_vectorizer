import json
import os

import cv2
import numpy as np
import pytest

from benchmark.baselines.inkscape_baseline import InkscapeBaselineRunner


@pytest.fixture
def mock_image(tmp_path):
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    img_path = tmp_path / "test.png"
    cv2.imwrite(str(img_path), img)
    return str(img_path)


def test_inkscape_skip_if_not_installed(mock_image, tmp_path, monkeypatch):
    runner = InkscapeBaselineRunner()

    # Force not installed
    runner.inkscape_version = "not_installed"

    out_svg = tmp_path / "out.svg"
    result = runner.run(mock_image, str(out_svg))

    assert "error" in result
    assert "Skipped" in result["error"]


def test_inkscape_baseline_execution(mock_image, tmp_path, monkeypatch):
    runner = InkscapeBaselineRunner()

    # Mock CLI execution
    def mock_run_cli(input_path, output_path, timeout_sec):
        # Fake SVG creation
        with open(output_path, "w") as f:
            f.write("<svg></svg>")

    monkeypatch.setattr(runner, "_run_cli", mock_run_cli)
    runner.inkscape_version = "Inkscape 1.3.2"

    out_svg = tmp_path / "out.svg"
    result = runner.run(mock_image, str(out_svg))

    assert "error" not in result
    assert result["inkscape_version"] == "Inkscape 1.3.2"
    assert "performance" in result
    assert result["performance"]["success"] is True
    assert "GUI preferences fallback" in result["configuration_note"]

    assert os.path.exists(str(out_svg))
    json.dumps(result)
