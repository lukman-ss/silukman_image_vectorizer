import json
import numpy as np
import pytest

from benchmark.evaluation.pixel_metrics import PixelMetricsCalculator


def test_pixel_metrics_identical_rgb():
    calc = PixelMetricsCalculator()
    
    # 2x2 solid color
    img1 = np.full((2, 2, 3), 128, dtype=np.uint8)
    img2 = np.full((2, 2, 3), 128, dtype=np.uint8)
    
    result = calc.calculate(img1, img2)
    
    assert result["mae"] == 0.0
    assert result["mse"] == 0.0
    assert result["rmse"] == 0.0
    assert result["psnr"] == 100.0
    assert result["normalized_mae"] == 0.0
    
    # Must be JSON safe
    json.dumps(result)


def test_pixel_metrics_different_rgb():
    calc = PixelMetricsCalculator()
    
    img1 = np.full((2, 2, 3), 200, dtype=np.uint8)
    img2 = np.full((2, 2, 3), 100, dtype=np.uint8)
    
    result = calc.calculate(img1, img2)
    
    assert result["mae"] == 100.0
    assert result["mse"] == 10000.0
    assert result["rmse"] == 100.0
    # psnr = 20 * log10(255/100) = 20 * log10(2.55) approx 8.13
    assert 8.0 < result["psnr"] < 8.2
    assert abs(result["normalized_mae"] - (100.0/255.0)) < 1e-6


def test_pixel_metrics_rgba_compositing():
    calc = PixelMetricsCalculator(bg_color=(255, 255, 255))
    
    # img1: Semi-transparent black (0,0,0, 127) -> alpha ~0.5
    # Composited on white (255,255,255) -> ~ (127, 127, 127)
    img1 = np.zeros((2, 2, 4), dtype=np.uint8)
    img1[..., 3] = 127
    
    # img2: Solid gray (127, 127, 127)
    img2 = np.full((2, 2, 3), 127, dtype=np.uint8)
    
    result = calc.calculate(img1, img2)
    
    # Since composited img1 is approx 127, the difference should be near 0
    assert result["mae"] < 1.0


def test_pixel_metrics_size_mismatch():
    calc = PixelMetricsCalculator()
    img1 = np.zeros((2, 2, 3), dtype=np.uint8)
    img2 = np.zeros((3, 3, 3), dtype=np.uint8)
    
    with pytest.raises(ValueError, match="Image dimensions do not match"):
        calc.calculate(img1, img2)
