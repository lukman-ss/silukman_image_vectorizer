import os
from pathlib import Path

import pytest

from app.config.settings import VectorizationSettings
from app.core.exceptions import ExportError, InvalidInputError, ProcessingError
from app.core.vectorization_service import vectorize_image


@pytest.fixture
def sample_image(tmp_path):
    """Provide a simple dummy image for testing."""
    import cv2
    import numpy as np

    img_path = tmp_path / "test_image.png"
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    # Add a white square in the middle
    img[25:75, 25:75] = [255, 255, 255]
    cv2.imwrite(str(img_path), img)
    return str(img_path)


def test_vectorize_image_success(sample_image, tmp_path):
    output_path = tmp_path / "output.svg"
    config = VectorizationSettings(engine_type="OpenCV Legacy")

    result = vectorize_image(
        input_path=sample_image,
        output_path=str(output_path),
        config=config,
    )

    assert result.status == "success"
    assert result.input_path == sample_image
    assert result.output_path == str(output_path)
    assert result.input_width == 100
    assert result.input_height == 100
    assert result.input_format == "png"
    assert result.duration_seconds > 0
    assert result.output_file_size > 0
    assert result.input_sha256 is not None
    assert result.output_sha256 is not None
    assert os.path.exists(output_path)


def test_vectorize_image_invalid_input(tmp_path):
    output_path = tmp_path / "output.svg"
    config = VectorizationSettings()

    with pytest.raises(InvalidInputError):
        vectorize_image(
            input_path=str(tmp_path / "non_existent.png"),
            output_path=str(output_path),
            config=config,
        )


def test_vectorize_image_invalid_output(sample_image):
    config = VectorizationSettings()

    with pytest.raises(ExportError):
        vectorize_image(
            input_path=sample_image,
            output_path="/invalid/path/output.svg",
            config=config,
        )
