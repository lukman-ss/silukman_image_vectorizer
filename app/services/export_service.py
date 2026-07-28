"""Service for exporting vector results to SVG files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from app.core.vectorization_engine import VectorResult
from app.services.image_loader import ImageInfo
from app.services.svg_exporter import export_svg


class ExportService:
    """Handles SVG export business logic, path building, and error wrapping."""

    def build_default_export_path(self, image_info: Optional[ImageInfo]) -> str:
        """Construct a suggested SVG output path next to the source image."""
        if not image_info:
            return ""
        dir_name = os.path.dirname(image_info.file_path)
        base_name, _ = os.path.splitext(image_info.file_name)
        return os.path.join(dir_name, f"{base_name}_vectorized.svg")

    def export_svg_file(
        self,
        vector_result: VectorResult,
        file_path: str,
        source_name: Optional[str] = None,
    ) -> Path:
        """Export vector result to an SVG file.

        Args:
            vector_result: The vectorization output.
            file_path: Target file path string.
            source_name: Original image filename for metadata embedding.

        Returns:
            The actual path where the SVG was written.

        Raises:
            ValueError: If the path is invalid.
            OSError: If the file cannot be written.
        """
        return export_svg(vector_result, file_path, source_filename=source_name)
