import pytest
import xml.etree.ElementTree as ET

from app.core.postprocessing import (
    parse_and_validate_svg,
    calculate_svg_metrics,
    normalize_dimensions,
    optimize_svg,
    replace_svg_palette,
    serialize_deterministic_svg,
    SVG_NS
)


def test_parse_and_validate_svg_success():
    """Verify valid SVG parses correctly."""
    valid_svg = f'<svg xmlns="{SVG_NS}" width="100" height="100"><path d="M0 0 L10 10 Z"/></svg>'
    root = parse_and_validate_svg(valid_svg)
    assert root is not None
    assert root.tag.endswith("svg")


def test_parse_and_validate_svg_empty():
    """Verify empty string raises ValueError."""
    with pytest.raises(ValueError, match="SVG data is empty"):
        parse_and_validate_svg("   \n ")


def test_parse_and_validate_svg_invalid_xml():
    """Verify broken XML raises ValueError."""
    with pytest.raises(ValueError, match="Invalid XML syntax"):
        parse_and_validate_svg('<svg><path d="M0 0 L10 10 Z"')


def test_parse_and_validate_svg_wrong_root():
    """Verify root element validation."""
    with pytest.raises(ValueError, match="Root element is not <svg>"):
        parse_and_validate_svg('<div xmlns="http://www.w3.org/2000/svg"></div>')


def test_calculate_svg_metrics():
    """Verify metrics extraction counts paths and points correctly."""
    svg = f"""<svg xmlns="{SVG_NS}">
        <g>
            <path d="M0 0 L10 10 L20 20 Z" />
            <path d="M5 5 L15 15" />
            <circle cx="5" cy="5" r="5" />
        </g>
    </svg>"""
    root = parse_and_validate_svg(svg)
    metrics = calculate_svg_metrics(root)
    
    assert metrics["path_count"] == 2
    # 2 paths + 1 circle + 1 g + 1 svg = 5 total elements
    assert metrics["total_elements"] == 5
    # First path: M0 0 (2), L10 10 (2), L20 20 (2) -> 6 coords = 3 points
    # Second path: M5 5 (2), L15 15 (2) -> 4 coords = 2 points
    # Total points = 5
    assert metrics["simplified_point_count"] == 5


def test_normalize_dimensions():
    """Verify viewBox is added if missing but width/height exist."""
    svg = f'<svg xmlns="{SVG_NS}" width="800" height="600"></svg>'
    root = parse_and_validate_svg(svg)
    
    assert root.get("viewBox") is None
    root = normalize_dimensions(root)
    assert root.get("viewBox") == "0 0 800 600"


def test_optimize_svg():
    """Verify empty <g> elements are removed."""
    svg = f"""<svg xmlns="{SVG_NS}">
        <g></g>
        <g id="keep"><path d="M0 0" /></g>
        <g><g></g></g>
    </svg>"""
    root = parse_and_validate_svg(svg)
    root = optimize_svg(root)
    
    # Should only have the svg root, the <g id="keep"> and the <path>
    elements = list(root.iter())
    assert len(elements) == 3


def test_replace_svg_palette():
    """Verify palette replacement updates fill and stroke."""
    svg = f"""<svg xmlns="{SVG_NS}">
        <path fill="#FF0000" stroke="#00FF00" d="M0 0" />
    </svg>"""
    root = parse_and_validate_svg(svg)
    
    replacements = [
        ("#FF0000", "#000000"),
        ("#00FF00", "#0000FF")
    ]
    
    root = replace_svg_palette(root, replacements)
    path = list(root)[0]
    
    assert path.get("fill") == "#000000"
    assert path.get("stroke") == "#0000FF"


def test_serialize_deterministic_svg():
    """Verify serialization output format."""
    svg = f'<svg xmlns="{SVG_NS}" width="10" height="10"><path d="M0 0" /></svg>'
    root = parse_and_validate_svg(svg)
    
    output = serialize_deterministic_svg(root)
    assert output.startswith('<?xml version="1.0" encoding="UTF-8"?>\n')
    assert '<path' in output
