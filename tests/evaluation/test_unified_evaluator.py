import json
import os

import cv2
import numpy as np
import pytest

from benchmark.evaluation.unified_evaluator import UnifiedQualityEvaluator


@pytest.fixture
def dummy_benchmark_files(tmp_path):
    # Create original raster (10x10)
    raster_path = tmp_path / "orig.png"
    img = np.full((10, 10, 3), 128, dtype=np.uint8)
    cv2.imwrite(str(raster_path), img)

    # Create dummy SVG
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">
        <rect width="10" height="10" fill="gray"/>
    </svg>"""
    svg_path = tmp_path / "out.svg"
    svg_path.write_text(svg_content)

    return str(raster_path), str(svg_path)


def test_unified_evaluator_success(dummy_benchmark_files):
    orig, svg = dummy_benchmark_files

    evaluator = UnifiedQualityEvaluator()

    perf_data = {"wall_clock_time_seconds": 1.23, "peak_memory_bytes": 1048576 * 50}  # 50 MB

    result = evaluator.evaluate(
        image_id="test_001",
        preset="balanced",
        original_raster_path=orig,
        svg_path=svg,
        performance_data=perf_data,
    )

    assert result["image_id"] == "test_001"
    assert result["preset"] == "balanced"
    assert len(result["errors"]) == 0

    # Check nulls are NOT present (all should be calculated)
    for k, v in result["quality"].items():
        assert v is not None

    assert result["complexity"]["path_count"] == 0  # we used rect
    assert result["complexity"]["command_count"] == 0
    assert result["complexity"]["svg_bytes"] > 0

    assert result["performance"]["duration_seconds"] == 1.23
    assert result["performance"]["peak_memory_mb"] == 50.0

    # JSON safe
    json.dumps(result)


def test_unified_evaluator_invalid_svg(dummy_benchmark_files, tmp_path):
    orig, _ = dummy_benchmark_files

    bad_svg = tmp_path / "bad.svg"
    bad_svg.write_text("<svg>broken")

    evaluator = UnifiedQualityEvaluator()

    result = evaluator.evaluate(
        image_id="test_002", preset="high", original_raster_path=orig, svg_path=str(bad_svg)
    )

    # Should not crash, quality metrics should remain None
    assert len(result["errors"]) > 0
    for k, v in result["quality"].items():
        assert v is None
