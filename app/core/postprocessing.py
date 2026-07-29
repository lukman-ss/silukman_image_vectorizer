import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Tuple
import defusedxml.ElementTree as DET

# Standard SVG Namespace mapping
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def parse_and_validate_svg(svg_data: str) -> ET.Element:
    """Parses an SVG string into an ElementTree, validating its root."""
    if not svg_data or not svg_data.strip():
        raise ValueError("SVG data is empty.")

    try:
        root = DET.fromstring(svg_data)
    except (ET.ParseError, DET.ParseError) as e:
        raise ValueError(f"Invalid XML syntax: {e}")

    # Validation: the root must be an SVG tag (accounting for namespace)
    tag = root.tag.replace(f"{{{SVG_NS}}}", "")
    if tag.lower() != "svg":
        raise ValueError(f"Root element is not <svg>, got <{tag}>")

    return root


def calculate_svg_metrics(root: ET.Element) -> Dict[str, int]:
    """Calculates metrics like path count, element count, and approximate point counts."""
    path_count = 0
    total_elements = 0
    simplified_points = 0

    for element in root.iter():
        total_elements += 1
        tag = element.tag.replace(f"{{{SVG_NS}}}", "")
        if tag.lower() == "path":
            path_count += 1
            # Count coordinates in the 'd' attribute
            d_attr = element.get("d", "")
            if d_attr:
                coords = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", d_attr)
                # Heuristic: 2 coordinates = 1 point
                simplified_points += len(coords) // 2

    return {
        "path_count": path_count,
        "total_elements": total_elements,
        "simplified_point_count": simplified_points,
        "original_point_count": simplified_points * 3,  # Based on old heuristic logic
    }


def normalize_dimensions(root: ET.Element) -> ET.Element:
    """Ensures the SVG has valid width, height, and viewBox."""
    # This is a safe normalization. We don't overwrite if it exists and looks valid.
    w = root.get("width")
    h = root.get("height")
    vb = root.get("viewBox")

    if not vb and w and h:
        root.set("viewBox", f"0 0 {w} {h}")

    return root


def optimize_svg(root: ET.Element) -> ET.Element:
    """
    Safely trims unnecessary empty group elements without altering visual output.
    """
    # Remove empty <g> elements iteratively until clean
    changed = True
    while changed:
        changed = False
        parents = {c: p for p in root.iter() for c in p}
        for g in root.findall(f".//{{{SVG_NS}}}g"):
            # Also consider whitespace-only text as empty
            text_empty = not g.text or not g.text.strip()
            if len(g) == 0 and not g.attrib and text_empty:
                parent = parents.get(g)
                if parent is not None:
                    parent.remove(g)
                    changed = True

    return root


def replace_svg_palette(root: ET.Element, replacements: List[Tuple[str, str]]) -> ET.Element:
    """
    Replaces exact hex colors in fill and stroke attributes.
    Expects format: [("#FFFFFF", "#000000")]
    """
    if not replacements:
        return root

    # Normalize replacements to lower case keys, but keep value case
    normalized_replacements = {old.lower(): new for old, new in replacements}

    for element in root.iter():
        fill = element.get("fill")
        if fill and fill.lower() in normalized_replacements:
            element.set("fill", normalized_replacements[fill.lower()])

        stroke = element.get("stroke")
        if stroke and stroke.lower() in normalized_replacements:
            element.set("stroke", normalized_replacements[stroke.lower()])

    return root


def serialize_deterministic_svg(root: ET.Element) -> str:
    """Serializes the SVG ElementTree to a deterministic string."""
    svg_content = ET.tostring(root, encoding="unicode", short_empty_elements=True)
    if not svg_content.startswith("<?xml"):
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{svg_content}\n'
    return svg_content
