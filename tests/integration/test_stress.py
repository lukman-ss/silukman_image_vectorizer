import pytest
import time
import cv2
import numpy as np
from app.core.vectorization_service import vectorize_image
from app.config.settings import VectorizationConfig

# Stress test dimensions
DIMENSIONS = [512, 1024, 2048, 4096, 8192]


@pytest.fixture
def dummy_large_image(tmp_path):
    """Factory for creating large dummy images."""
    def _create(size):
        path = tmp_path / f"stress_{size}x{size}.png"
        # Create a simple checkerboard pattern or random noise
        # To avoid massive file sizes and compression times, we use a simple pattern
        img = np.zeros((size, size, 3), dtype=np.uint8)
        img[::20, ::20] = [255, 255, 255]  # some white spots
        cv2.imwrite(str(path), img)
        return path
    return _create


@pytest.mark.stress
@pytest.mark.parametrize("size", DIMENSIONS)
def test_large_image_stress(size, dummy_large_image, tmp_path):
    """
    Stress-test vectorization on increasingly large images.
    Measured aspects:
    - runtime
    - success status
    - output complexity (SVG file size)
    - memory (implicitly tested if the process doesn't OOM)
    """
    input_path = dummy_large_image(size)
    output_path = tmp_path / f"out_{size}.svg"
    config = VectorizationConfig(engine_type="OpenCV Legacy")  # Use OpenCV for determinism in CI/stress

    start_time = time.time()

    # Run vectorization (we assume a reasonable timeout inside or via pytest-timeout if configured)
    result = vectorize_image(str(input_path), str(output_path), config)

    duration = time.time() - start_time

    # Assertions
    assert result.status == "success"
    assert output_path.exists()

    svg_size = output_path.stat().st_size
    assert svg_size > 0

    print(f"\nStress Test [{size}x{size}]: Runtime={duration:.2f}s, SVG Size={svg_size} bytes")
