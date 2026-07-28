import json
import numpy as np

from benchmark.evaluation.ssim_metrics import SSIMCalculator


def test_ssim_identical():
    calc = SSIMCalculator()
    
    # 10x10 gradient image
    img1 = np.zeros((10, 10, 3), dtype=np.uint8)
    for i in range(10):
        img1[:, i, :] = i * 25
        
    img2 = img1.copy()
    
    result = calc.calculate(img1, img2)
    
    assert "error" not in result
    assert "ssim" in result
    assert abs(result["ssim"] - 1.0) < 1e-7
    
    # Check JSON serializability
    json.dumps(result)


def test_ssim_different():
    calc = SSIMCalculator()
    
    # img1 is mostly dark
    img1 = np.full((10, 10, 3), 10, dtype=np.uint8)
    
    # img2 is mostly bright
    img2 = np.full((10, 10, 3), 200, dtype=np.uint8)
    
    result = calc.calculate(img1, img2)
    
    assert "error" not in result
    assert "ssim" in result
    assert result["ssim"] < 0.5


def test_ssim_too_small():
    calc = SSIMCalculator()
    
    img1 = np.zeros((5, 5, 3), dtype=np.uint8)
    img2 = np.zeros((5, 5, 3), dtype=np.uint8)
    
    result = calc.calculate(img1, img2)
    
    # Should report an error because min size is < 7, but NOT crash the script
    assert "error" in result
    assert "too small" in result["error"]
    assert "ssim" not in result


def test_ssim_size_mismatch():
    calc = SSIMCalculator()
    
    img1 = np.zeros((10, 10, 3), dtype=np.uint8)
    img2 = np.zeros((12, 12, 3), dtype=np.uint8)
    
    result = calc.calculate(img1, img2)
    
    assert "error" in result
    assert "dimensions do not match" in result["error"]
