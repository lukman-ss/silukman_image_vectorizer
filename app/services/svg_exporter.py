"""SVG document builder for in-memory vectorization results."""

from __future__ import annotations

import datetime
import os
import re
import tempfile
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

from app.core.constants import APPLICATION_TITLE
from app.core.vectorization_engine import VectorPath, VectorResult


SVG_NAMESPACE = "http://www.w3.org/2000/svg"


def build_svg_document(vector_result: VectorResult, source_filename: str | None = None) -> str:
    """Convert a vector result into an SVG document string."""
    _validate_vector_result(vector_result)

    width = vector_result.image_width
    height = vector_result.image_height
    root = Element(
        "svg",
        {
            "xmlns": SVG_NAMESPACE,
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
        },
    )

    # Add structured metadata.
    root.append(_build_metadata_element(source_filename))

    for vector_path in vector_result.paths:
        path_data = _build_path_data(vector_path)
        if path_data:
            # Generate hex color string from detected path color tuple (RGB)
            r, g, b = vector_path.color
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            SubElement(
                root,
                "path",
                {
                    "d": path_data,
                    "fill": hex_color,
                    "fill-rule": "evenodd",
                    "stroke": hex_color,
                    "stroke-width": "0.75",
                    "stroke-linejoin": "round",
                },
            )

    svg_content = tostring(root, encoding="unicode", short_empty_elements=True)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{svg_content}\n'


def normalize_svg_path(file_path: str) -> Path:
    """Validate an output path and append the SVG extension when missing."""
    path = Path(file_path).expanduser()
    if not path.name or path.name in {".", ".."}:
        raise ValueError("SVG output filename is required.")
    if path.suffix.lower() != ".svg":
        path = path.with_name(f"{path.name}.svg")

    parent = path.parent
    if not parent.exists():
        raise ValueError("SVG output folder does not exist.")
    if not parent.is_dir():
        raise ValueError("SVG output parent must be a folder.")
    if not os.access(parent, os.W_OK):
        raise PermissionError("SVG output folder is not writable.")
    return path


def export_svg(
    vector_result: VectorResult,
    file_path: str,
    source_filename: str | None = None,
) -> Path:
    """Build and atomically write an SVG document to disk."""
    from app.core.vectorizer_backend import VTracerVectorResult
    output_path = normalize_svg_path(file_path)
    
    if isinstance(vector_result, VTracerVectorResult):
        import xml.etree.ElementTree as ET
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        try:
            root = ET.fromstring(vector_result.svg_data)
            metadata = _build_metadata_element(source_filename)
            root.insert(0, metadata)
            svg_content = ET.tostring(root, encoding="unicode", short_empty_elements=True)
            if not svg_content.startswith("<?xml"):
                svg_content = f'<?xml version="1.0" encoding="UTF-8"?>\n{svg_content}\n'
        except Exception:
            svg_content = _insert_metadata_text(vector_result.svg_data, source_filename)
    else:
        svg_content = build_svg_document(vector_result, source_filename)
        
    _atomic_write_text(output_path, svg_content)
    return output_path


def _atomic_write_text(output_path: Path, content: str) -> None:
    """Write text through a temporary file and atomically replace the target."""
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            temporary_path = Path(temporary_file.name)
        os.replace(temporary_path, output_path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            try:
                temporary_path.unlink()
            except OSError:
                pass


def _build_metadata_element(source_filename: str | None = None) -> Element:
    """Create SVG metadata used by generated and native SVG exports."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata = Element("metadata")
    SubElement(metadata, "app-name").text = APPLICATION_TITLE
    SubElement(metadata, "export-timestamp").text = timestamp
    if source_filename:
        SubElement(metadata, "source-image").text = source_filename
    return metadata


def _insert_metadata_text(svg_data: str, source_filename: str | None = None) -> str:
    """Best-effort metadata insertion for SVG text that cannot be parsed."""
    metadata_text = tostring(_build_metadata_element(source_filename), encoding="unicode")
    match = re.search(r"<svg\b[^>]*>", svg_data, flags=re.IGNORECASE)
    if match is None:
        return svg_data
    insert_at = match.end()
    return f"{svg_data[:insert_at]}\n{metadata_text}\n{svg_data[insert_at:]}"


def _build_path_data(vector_path: VectorPath) -> str:
    """Build a closed compound SVG path from outer and hole contours."""
    if vector_path.point_count == 0:
        return ""

    commands = _build_contour_commands(vector_path.points)
    for hole in vector_path.holes:
        commands.extend(_build_contour_commands(hole))
    return " ".join(commands)


def _build_contour_commands(points) -> list[str]:
    """Build commands for one closed contour."""
    if len(points) == 0:
        return []
    first_x, first_y = points[0]
    commands = [f"M {_format_number(first_x)} {_format_number(first_y)}"]
    commands.extend(
        f"L {_format_number(x)} {_format_number(y)}"
        for x, y in points[1:]
    )
    commands.append("Z")
    return commands


def _format_number(value: float | int) -> str:
    """Format numeric coordinates without unnecessary decimal places."""
    numeric_value = float(value)
    if numeric_value.is_integer():
        return str(int(numeric_value))
    return format(numeric_value, ".6g")


def _validate_vector_result(vector_result: VectorResult) -> None:
    """Validate the minimum data required to construct an SVG document."""
    if not isinstance(vector_result, VectorResult):
        raise TypeError("vector_result must be a VectorResult instance.")
    if vector_result.image_width <= 0 or vector_result.image_height <= 0:
        raise ValueError("Vector result image dimensions must be greater than zero.")
