"""Service for validating user inputs and file paths."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from app.services.batch_processor import BatchFileValidation, validate_batch_files

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


class ValidationService:
    """Centralizes all validation logic. Returns error strings or None on success."""

    def validate_image_path(self, path: str) -> Optional[str]:
        """Returns None if valid, or a human-readable error message."""
        if not path:
            return "No file path provided."
        p = Path(path)
        if not p.exists():
            return f"File not found: {p.name}"
        if not p.is_file():
            return f"Not a file: {p.name}"
        if p.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            return f"Unsupported file format: {p.suffix}. Supported: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}"
        return None

    def validate_export_path(self, path: str) -> Optional[str]:
        """Returns None if valid output path, or a human-readable error message."""
        if not path:
            return "No output path provided."
        p = Path(path)
        if not p.parent.exists():
            return f"Output directory does not exist: {p.parent}"
        if not os.access(p.parent, os.W_OK):
            return f"Output directory is not writable: {p.parent}"
        return None

    def validate_batch_files(self, paths: list[str]) -> list[BatchFileValidation]:
        """Delegate batch file validation and return structured results."""
        return validate_batch_files(paths)
