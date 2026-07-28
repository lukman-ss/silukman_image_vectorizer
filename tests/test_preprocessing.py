import cv2
import numpy as np
import pytest

from app.core.preprocessing import (
    apply_background_removal,
    apply_color_quantization,
    apply_grayscale_threshold,
    apply_palette_replacements,
)


def test_apply_background_removal():
    """Test background removal using a small 4x4 array."""
    # Create a 4x4 RGB array, background is white (255, 255, 255), middle is red (0, 0, 255) in BGR
    img = np.full((4, 4, 3), 255, dtype=np.uint8)
    img[1:3, 1:3] = [0, 0, 255]

    result, meta = apply_background_removal(img, tolerance=10.0)

    assert result.shape == (4, 4, 4)  # converted to BGRA
    assert meta["operation"] == "background_removal"

    # Corners should be transparent
    assert result[0, 0, 3] == 0
    assert result[3, 3, 3] == 0

    # Center should be opaque red
    assert result[1, 1, 3] == 255
    assert np.array_equal(result[1, 1, :3], [0, 0, 255])


def test_apply_palette_replacements():
    """Test palette replacements."""
    # 2x2 RGB array, all white
    img = np.full((2, 2, 3), 255, dtype=np.uint8)
    img[0, 0] = [255, 0, 0]  # B=255, G=0, R=0 in BGR, which is Blue

    # Replace Blue (0, 0, 255 in RGB) with Red (255, 0, 0 in RGB)
    replacements = [((0, 0, 255), (255, 0, 0))]

    result, meta = apply_palette_replacements(img, replacements)

    assert meta["pixels_modified"] == 1
    # Check that [0, 0] is now Red (BGR = 0, 0, 255)
    assert np.array_equal(result[0, 0], [0, 0, 255])
    # Ensure it's not modifying in-place
    assert np.array_equal(img[0, 0], [255, 0, 0])


def test_apply_color_quantization():
    """Test K-Means color quantization."""
    # Create a gradient-like 4x4 array
    img = np.zeros((4, 4, 3), dtype=np.uint8)
    for i in range(4):
        for j in range(4):
            img[i, j] = [i * 50, j * 50, 100]

    # Quantize to 2 colors
    result, meta = apply_color_quantization(img, max_colors=2)

    # Should reduce unique colors to at most 2
    unique_colors = np.unique(result.reshape(-1, 3), axis=0)
    assert len(unique_colors) <= 2
    assert meta["actual_colors"] <= 2


def test_apply_grayscale_threshold():
    """Test grayscale conversion and thresholding."""
    img = np.zeros((4, 4, 3), dtype=np.uint8)
    img[0:2, :] = 255  # Top half white
    img[2:4, :] = 0  # Bottom half black

    result, meta = apply_grayscale_threshold(img, threshold_val=127)

    assert result.shape == (4, 4)
    assert np.array_equal(result[0, 0], 255)
    assert np.array_equal(result[3, 3], 0)
    assert meta["operation"] == "grayscale_threshold"
