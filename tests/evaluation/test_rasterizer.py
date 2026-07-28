import os
import tempfile
from pathlib import Path

import pytest
from PySide6.QtGui import QImage

from benchmark.evaluation.rasterizer import SVGRasterizer


@pytest.fixture
def sample_svg(tmp_path):
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
        <rect width="100" height="100" fill="red"/>
        <circle cx="50" cy="50" r="40" fill="blue" opacity="0.5"/>
    </svg>"""
    svg_file = tmp_path / "test.svg"
    svg_file.write_text(svg_content)
    return str(svg_file)


def test_rasterizer_success(sample_svg, tmp_path):
    rasterizer = SVGRasterizer()
    out_png = str(tmp_path / "out.png")

    result = rasterizer.rasterize(sample_svg, out_png, 100, 100)

    assert result["success"] is True
    assert result["backend"] == "PySide6.QtSvg"
    assert result["output_width"] == 100
    assert result["output_height"] == 100
    assert os.path.exists(out_png)

    # Verify dimensions
    img = QImage(out_png)
    assert img.width() == 100
    assert img.height() == 100


def test_rasterizer_file_not_found(tmp_path):
    rasterizer = SVGRasterizer()
    out_png = str(tmp_path / "out.png")

    result = rasterizer.rasterize("nonexistent.svg", out_png, 100, 100)

    assert result["success"] is False
    assert "File not found" in result["error"]


def test_rasterizer_invalid_svg(tmp_path):
    invalid_svg = tmp_path / "invalid.svg"
    invalid_svg.write_text("<svg>broken")

    rasterizer = SVGRasterizer()
    out_png = str(tmp_path / "out.png")

    result = rasterizer.rasterize(str(invalid_svg), out_png, 100, 100)

    assert result["success"] is False
    assert "Invalid SVG format" in result["error"]
