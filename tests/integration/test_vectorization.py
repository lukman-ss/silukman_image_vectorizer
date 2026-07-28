import os

import cv2
import numpy as np
import pytest

from app.config.preset_manager import PresetManager
from app.config.settings import VectorizationSettings
from app.core.exceptions import ExportError, InvalidInputError, ProcessingError
from app.core.vectorization_service import vectorize_image


@pytest.fixture
def preset_manager():
    return PresetManager.get_instance()


@pytest.fixture
def synth_images(tmp_path):
    images = {}

    # PNG RGB
    png_path = str(tmp_path / "rgb.png")
    img = np.zeros((10, 10, 3), dtype=np.uint8)
    img[2:8, 2:8] = [0, 0, 255]  # Red square
    cv2.imwrite(png_path, img)
    images["png"] = png_path

    # JPEG RGB
    jpg_path = str(tmp_path / "rgb.jpg")
    cv2.imwrite(jpg_path, img)
    images["jpeg"] = jpg_path

    # PNG RGBA
    rgba_path = str(tmp_path / "rgba.png")
    img_rgba = np.zeros((10, 10, 4), dtype=np.uint8)
    img_rgba[2:8, 2:8] = [0, 0, 255, 255]  # Red square, fully opaque
    img_rgba[0:2, 0:2] = [0, 0, 0, 0]  # Transparent corner
    cv2.imwrite(rgba_path, img_rgba)
    images["rgba"] = rgba_path

    # Monochrome (Grayscale 1-channel)
    mono_path = str(tmp_path / "mono.png")
    img_mono = np.zeros((10, 10), dtype=np.uint8)
    img_mono[2:8, 2:8] = 255  # White square
    cv2.imwrite(mono_path, img_mono)
    images["mono"] = mono_path

    # Invalid image
    inv_path = str(tmp_path / "invalid.png")
    with open(inv_path, "wb") as f:
        f.write(b"Not an image")
    images["invalid"] = inv_path

    # Empty file
    empty_path = str(tmp_path / "empty.png")
    with open(empty_path, "wb") as f:
        pass
    images["empty"] = empty_path

    # Unicode and spaces
    uni_path = str(tmp_path / "unicode_ä_ space.png")
    cv2.imwrite(uni_path, img)
    images["unicode"] = uni_path

    return images


def get_config(pm, preset="balanced"):
    return pm.get_preset_config(preset)


def test_png_to_svg(preset_manager, synth_images, tmp_path):
    out = str(tmp_path / "out_png.svg")
    res = vectorize_image(synth_images["png"], out, get_config(preset_manager))
    assert res.status == "success"
    assert os.path.exists(out)


def test_jpeg_to_svg(preset_manager, synth_images, tmp_path):
    out = str(tmp_path / "out_jpg.svg")
    res = vectorize_image(synth_images["jpeg"], out, get_config(preset_manager))
    assert res.status == "success"
    assert os.path.exists(out)


def test_rgba_to_svg(preset_manager, synth_images, tmp_path):
    out = str(tmp_path / "out_rgba.svg")
    res = vectorize_image(synth_images["rgba"], out, get_config(preset_manager))
    assert res.status == "success"
    assert os.path.exists(out)


def test_monochrome_to_svg(preset_manager, synth_images, tmp_path):
    out = str(tmp_path / "out_mono.svg")
    res = vectorize_image(synth_images["mono"], out, get_config(preset_manager))
    assert res.status == "success"
    assert os.path.exists(out)


def test_invalid_image(preset_manager, synth_images, tmp_path):
    out = str(tmp_path / "out_inv.svg")
    with pytest.raises(InvalidInputError):
        vectorize_image(synth_images["invalid"], out, get_config(preset_manager))


def test_empty_image(preset_manager, synth_images, tmp_path):
    out = str(tmp_path / "out_emp.svg")
    with pytest.raises(InvalidInputError):
        vectorize_image(synth_images["empty"], out, get_config(preset_manager))


def test_unicode_and_space_path(preset_manager, synth_images, tmp_path):
    out = str(tmp_path / "out_ö output.svg")
    res = vectorize_image(synth_images["unicode"], out, get_config(preset_manager))
    assert res.status == "success"
    assert os.path.exists(out)


def test_output_directory_not_exists(preset_manager, synth_images, tmp_path):
    out = str(tmp_path / "new_folder" / "subfolder" / "out.svg")
    with pytest.raises(ExportError):
        vectorize_image(synth_images["png"], out, get_config(preset_manager))


def test_preset_loading_integration(preset_manager, synth_images, tmp_path):
    out = str(tmp_path / "out_low.svg")
    res = vectorize_image(synth_images["png"], out, get_config(preset_manager, "low_complexity"))
    assert res.status == "success"
    assert os.path.exists(out)
