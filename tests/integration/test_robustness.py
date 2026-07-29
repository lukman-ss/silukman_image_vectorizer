import pytest
import os
import cv2
import numpy as np
import struct
from pathlib import Path
from app.core.vectorization_service import vectorize_image
from app.config.settings import VectorizationConfig

@pytest.fixture
def corrupted_inputs(tmp_path):
    """Fixture that generates various corrupted and invalid input files."""
    paths = {}
    
    # 1. Truncated PNG
    trunc_png = tmp_path / "truncated.png"
    # Write a valid header but cut it off
    valid_png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
    with open(trunc_png, 'wb') as f:
        f.write(valid_png_header)
    paths["truncated_png"] = trunc_png

    # 2. Invalid JPEG
    inv_jpeg = tmp_path / "invalid.jpg"
    with open(inv_jpeg, 'wb') as f:
        f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01')
    paths["invalid_jpeg"] = inv_jpeg

    # 3. Wrong extension (text file named as png)
    wrong_ext = tmp_path / "wrong_ext.png"
    with open(wrong_ext, 'w') as f:
        f.write("This is actually a text file.")
    paths["wrong_ext"] = wrong_ext

    # 4. Empty file
    empty_file = tmp_path / "empty.png"
    with open(empty_file, 'wb') as f:
        pass
    paths["empty_file"] = empty_file

    # 5. Huge declared dimensions (PNG IHDR modification)
    # This creates a tiny file that claims to be 1000000x1000000
    huge_dim = tmp_path / "huge_dim.png"
    width, height = 1000000, 1000000
    # IHDR chunk: Width (4 bytes), Height (4 bytes), Bit depth (1), Color type (1), Comp method (1), Filter (1), Interlace (1)
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    with open(huge_dim, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        f.write(struct.pack(">I", len(ihdr_data)))
        f.write(b'IHDR' + ihdr_data)
        # We don't bother with a valid CRC or actual data, decoding will fail
    paths["huge_dim"] = huge_dim

    # 6. Malformed alpha (4 channels but short data or random noise not matching size)
    malf_alpha = tmp_path / "malf_alpha.png"
    with open(malf_alpha, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' + struct.pack(">IIBBBBB", 10, 10, 8, 6, 0, 0, 0) + b'corrupted_data_here')
    paths["malf_alpha"] = malf_alpha

    # 7. Unsupported format (e.g. standard PDF or weird binary, named .xyz)
    unsupp = tmp_path / "unsupported.xyz"
    with open(unsupp, 'wb') as f:
        f.write(b'%PDF-1.4\n%EOF')
    paths["unsupported"] = unsupp
    
    return paths

@pytest.mark.parametrize("scenario_key", [
    "truncated_png",
    "invalid_jpeg",
    "wrong_ext",
    "empty_file",
    "huge_dim",
    "malf_alpha",
    "unsupported"
])
def test_corrupted_inputs(scenario_key, corrupted_inputs, tmp_path):
    """
    Ensure the application fails safely on corrupted inputs,
    returning a failed result rather than crashing the process.
    """
    input_path = corrupted_inputs[scenario_key]
    output_path = tmp_path / f"out_{scenario_key}.svg"
    config = VectorizationConfig(engine="opencv_legacy")

    result = vectorize_image(str(input_path), str(output_path), config)
    
    assert result.status == "failed"
    assert "error" in result.error.lower() or "fail" in result.error.lower() or "unsupported" in result.error.lower() or "could not" in result.error.lower()
    
    # Ensure no empty/invalid output file was left behind if it failed early
    # (or if it was created, it's cleaned up/managed properly)
    if output_path.exists():
        assert output_path.stat().st_size == 0
