import json

import numpy as np

from benchmark.evaluation.edge_metrics import EdgeMetricsCalculator


def test_edge_metrics_identical():
    calc = EdgeMetricsCalculator()

    # Create a 50x50 image with a white square in the middle
    img1 = np.zeros((50, 50, 3), dtype=np.uint8)
    img1[10:40, 10:40] = 255

    img2 = img1.copy()

    result = calc.calculate(img1, img2)

    # F1 should be 1.0
    assert abs(result["f1"] - 1.0) < 1e-6
    assert abs(result["precision"] - 1.0) < 1e-6
    assert abs(result["recall"] - 1.0) < 1e-6

    if result["parameters"]["compute_distance_transform"]:
        assert abs(result["mean_distance_error"] - 0.0) < 1e-6

    json.dumps(result)


def test_edge_metrics_shifted():
    calc = EdgeMetricsCalculator()

    img1 = np.zeros((50, 50, 3), dtype=np.uint8)
    img1[10:40, 10:40] = 255

    # Shifted by 2 pixels right and down
    img2 = np.zeros((50, 50, 3), dtype=np.uint8)
    img2[12:42, 12:42] = 255

    result = calc.calculate(img1, img2)

    # Because edges are 1 pixel thin usually, a 2 pixel shift means NO overlap
    # F1 should be very low (close to 0)
    assert result["f1"] < 0.1

    # But distance transform should reflect the 2 pixel shift (approx 2.0 to 2.8 distance)
    assert 1.0 < result["mean_distance_error"] < 3.0


def test_edge_metrics_no_edges():
    calc = EdgeMetricsCalculator()

    # Completely solid image, no edges
    img1 = np.zeros((50, 50, 3), dtype=np.uint8)
    img2 = np.zeros((50, 50, 3), dtype=np.uint8)

    result = calc.calculate(img1, img2)

    # If both have no edges, Precision, Recall and F1 should safely default to 1.0
    assert abs(result["f1"] - 1.0) < 1e-6

    if result["parameters"]["compute_distance_transform"]:
        assert abs(result["mean_distance_error"] - 0.0) < 1e-6
