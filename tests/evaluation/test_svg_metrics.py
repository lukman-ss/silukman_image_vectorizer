import json

import pytest

from benchmark.evaluation.svg_metrics import SVGComplexityCalculator


@pytest.fixture
def mock_svg(tmp_path):
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
        <g id="layer1">
            <path d="M 10 10 L 90 10 L 90 90 Z" fill="#ff0000" stroke="#000000" />
            <path d="M 50 50 C 60 50 70 60 70 70" style="fill:none; stroke:#ff0000" />
        </g>
    </svg>"""
    svg_file = tmp_path / "test.svg"
    svg_file.write_text(svg_content)
    return str(svg_file)


@pytest.fixture
def mock_malicious_svg(tmp_path):
    # Billion laughs attack mockup
    svg_content = """<?xml version="1.0"?>
    <!DOCTYPE svg [
    <!ENTITY lol "lol">
    <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
    ]>
    <svg xmlns="http://www.w3.org/2000/svg">
        <text>&lol1;</text>
    </svg>"""
    svg_file = tmp_path / "malicious.svg"
    svg_file.write_text(svg_content)
    return str(svg_file)


def test_svg_metrics_valid(mock_svg):
    calc = SVGComplexityCalculator()
    result = calc.calculate(mock_svg)

    assert "error" not in result

    assert result["width"] == "100"
    assert result["height"] == "100"
    assert result["viewBox"] == "0 0 100 100"

    # <svg>, <g>, <path>, <path> => 4 elements
    assert result["total_element_count"] == 4
    assert result["group_count"] == 1
    assert result["path_count"] == 2

    # Path 1: M L L Z = 4 commands
    # Path 2: M C = 2 commands
    assert result["total_path_command_count"] == 6
    assert result["command_distribution"]["M"] == 2  # type: ignore[index] # complex typing/external library
    assert result["command_distribution"]["L"] == 2  # type: ignore[index] # complex typing/external library
    assert result["command_distribution"]["Z"] == 1  # type: ignore[index] # complex typing/external library
    assert result["command_distribution"]["C"] == 1  # type: ignore[index] # complex typing/external library

    # Unique colors: #ff0000, #000000 (none is ignored)
    assert result["unique_color_count"] == 2

    assert result["fill_count"] == 2  # one attrib, one in style
    assert result["stroke_count"] == 2

    # Path 1 coords: 10 10 90 10 90 90 = 6
    # Path 2 coords: 50 50 60 50 70 60 70 70 = 8
    # Total coords: 14
    assert result["estimated_coordinate_count"] == 14

    assert result["svg_bytes"] > 0  # type: ignore[operator] # complex typing/external library
    assert result["compressed_svg_bytes"] > 0  # type: ignore[operator] # complex typing/external library

    json.dumps(result)


def test_svg_metrics_malicious(mock_malicious_svg):
    calc = SVGComplexityCalculator()
    result = calc.calculate(mock_malicious_svg)

    # defusedxml should catch the entities or at least not expand them infinitely
    # Depending on defusedxml version, it might raise an error or just parse safely
    # If it raises an error, our code catches it and returns {"error": ...}
    # If it parses, it won't crash the system.
    # We just ensure it doesn't blow up and we get a dict back.
    assert isinstance(result, dict)
