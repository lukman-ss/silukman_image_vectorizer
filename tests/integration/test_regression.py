import os

import cv2
import numpy as np
import pytest

from app.config.preset_manager import PresetManager
from app.core.postprocessing import calculate_svg_metrics, parse_and_validate_svg
from app.core.vectorization_service import vectorize_image


@pytest.fixture
def synth_square(tmp_path):
    path = str(tmp_path / "square.png")
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    img[5:15, 5:15] = [255, 255, 255]  # White square
    cv2.imwrite(path, img)
    return path


def test_regression_invariants(synth_square, tmp_path):
    out1 = str(tmp_path / "run1.svg")
    out2 = str(tmp_path / "run2.svg")

    pm = PresetManager.get_instance()
    cfg = pm.get_preset_config("balanced")

    res1 = vectorize_image(synth_square, out1, cfg)
    res2 = vectorize_image(synth_square, out2, cfg)

    assert res1.status == "success"
    assert res2.status == "success"

    # Invariant: Deterministic behavior (if backend supports it, which ours does usually)
    assert res1.output_sha256 == res2.output_sha256

    # Invariant: Valid SVG and non-empty
    with open(out1, "r") as f:
        svg_content = f.read()
    assert len(svg_content) > 100

    # Check parseable
    root = parse_and_validate_svg(svg_content)
    metrics = calculate_svg_metrics(root)

    # Invariant: Path count range
    # A single square might yield a few paths depending on background handling
    assert metrics["path_count"] > 0
    assert metrics["path_count"] < 10

    # Invariant: Dimensions
    # Based on input image size 20x20
    assert "viewBox" in root.attrib or ("width" in root.attrib and "height" in root.attrib)
    if "viewBox" in root.attrib:
        assert "20" in root.attrib["viewBox"]

    # Output size range
    size_bytes = os.path.getsize(out1)
    assert 100 < size_bytes < 50000

    # Expected metadata
    assert "xml" in svg_content.lower() or "<svg" in svg_content.lower()
