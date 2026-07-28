import json
import numpy as np

from benchmark.evaluation.histogram_metrics import HistogramMetricsCalculator


def test_histogram_identical():
    calc = HistogramMetricsCalculator()
    
    # 10x10 gradient image
    img1 = np.zeros((10, 10, 3), dtype=np.uint8)
    for i in range(10):
        img1[:, i, :] = i * 25
        
    img2 = img1.copy()
    
    result = calc.calculate(img1, img2)
    
    assert abs(result["aggregate_correlation"] - 1.0) < 1e-7
    assert result["aggregate_bhattacharyya"] < 1e-7
    
    # Check JSON serializability
    json.dumps(result)


def test_histogram_different():
    calc = HistogramMetricsCalculator()
    
    # img1 is mostly dark
    img1 = np.full((10, 10, 3), 10, dtype=np.uint8)
    
    # img2 is mostly bright
    img2 = np.full((10, 10, 3), 200, dtype=np.uint8)
    
    result = calc.calculate(img1, img2)
    
    # They should not correlate well and Bhattacharyya distance should be high (closer to 1.0)
    assert result["aggregate_correlation"] < 0.5
    assert result["aggregate_bhattacharyya"] > 0.5


def test_histogram_spatially_invariant():
    """
    Proves the limitation documented: histogram is spatially invariant.
    """
    calc = HistogramMetricsCalculator()
    
    img1 = np.zeros((2, 2, 3), dtype=np.uint8)
    img1[0, 0] = [255, 0, 0]
    img1[0, 1] = [0, 255, 0]
    img1[1, 0] = [0, 0, 255]
    img1[1, 1] = [128, 128, 128]
    
    # Same pixels, different positions
    img2 = np.zeros((2, 2, 3), dtype=np.uint8)
    img2[1, 1] = [255, 0, 0]
    img2[0, 0] = [0, 255, 0]
    img2[0, 1] = [0, 0, 255]
    img2[1, 0] = [128, 128, 128]
    
    result = calc.calculate(img1, img2)
    
    # Even though images look completely different structurally, histogram is identical
    assert result["aggregate_correlation"] == 1.0
    assert result["aggregate_bhattacharyya"] == 0.0
