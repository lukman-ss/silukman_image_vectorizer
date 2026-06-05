"""Batch selection and validation service."""

from __future__ import annotations

import os
import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from PySide6.QtGui import QImageReader

from app.services.image_loader import SUPPORTED_FORMATS


@dataclass(frozen=True)
class BatchFileValidation:
    """Validation result for one selected batch image."""

    file_path: str
    error: Optional[str] = None

    @property
    def file_name(self) -> str:
        return os.path.basename(self.file_path)

    @property
    def is_valid(self) -> bool:
        return self.error is None


def validate_batch_files(file_paths: Iterable[str]) -> list[BatchFileValidation]:
    """Validate every selected batch image without processing it."""
    return [_validate_batch_file(file_path) for file_path in file_paths]


def _validate_batch_file(file_path: str) -> BatchFileValidation:
    extension = os.path.splitext(file_path)[1].lower()
    if extension not in SUPPORTED_FORMATS:
        return BatchFileValidation(file_path, "Unsupported image format.")

    reader = QImageReader(file_path)
    reader.setDecideFormatFromContent(True)
    if not reader.canRead():
        error = reader.errorString() or "Image cannot be read."
        return BatchFileValidation(file_path, error)

    from app.services.image_loader import SUPPORTED_IMAGE_FORMATS
    image_format = bytes(reader.format()).decode("ascii", errors="ignore").upper()
    if image_format not in SUPPORTED_IMAGE_FORMATS:
        return BatchFileValidation(
            file_path,
            f"Unsupported image content format '{image_format or 'Unknown'}'. Accepted: PNG, JPG, JPEG, BMP, WEBP."
        )

    return BatchFileValidation(file_path)


def get_unique_filepath(folder_path: str, filename: str) -> str:
    """Generate a unique file path by appending a counter if the file already exists."""
    base, ext = os.path.splitext(filename)
    if not ext:
        ext = ".svg"
    target_path = os.path.join(folder_path, f"{base}{ext}")
    counter = 1
    while os.path.exists(target_path):
        target_path = os.path.join(folder_path, f"{base}_{counter}{ext}")
        counter += 1
    return target_path


def validate_output_directory(folder_path: str) -> Path:
    """Validate that a batch output folder exists and is writable."""
    output_path = Path(folder_path).expanduser()
    if not output_path.exists() or not output_path.is_dir():
        raise ValueError("Batch output folder does not exist.")
    if not os.access(output_path, os.W_OK):
        raise PermissionError("Batch output folder is not writable.")
    return output_path


def process_batch(
    file_paths: list[str],
    output_dir: str,
    threshold_val: int,
    vector_settings,
    progress_callback=None,
) -> tuple[int, int, dict[str, str]]:
    """Process a list of images through the vectorization and SVG export pipeline.

    Args:
        file_paths: List of absolute file paths to process.
        output_dir: Folder to save the resulting SVG files.
        threshold_val: Threshold value for image processing.
        vector_settings: VectorizationSettings object.
        progress_callback: Optional callable(index, total, filename, success)

    Returns:
        A tuple of (success_count, failed_count, errors_dict)
    """
    from app.core.vectorizer_backend import OpenCVVectorizerBackend, VTracerVectorizerBackend
    from app.services.svg_exporter import export_svg

    output_path = validate_output_directory(output_dir)
    success_count = 0
    failed_count = 0
    errors: dict[str, str] = {}
    total = len(file_paths)

    active_settings = copy.deepcopy(vector_settings)
    if hasattr(active_settings, "threshold_val"):
        active_settings.threshold_val = threshold_val

    is_vtracer = getattr(active_settings, "engine_type", "VTracer") == "VTracer"

    for idx, path in enumerate(file_paths):
        filename = os.path.basename(path)
        base_name, _ = os.path.splitext(filename)
        svg_filename = f"{base_name}_vectorized.svg"
        
        try:
            vector_result = None
            if is_vtracer:
                try:
                    backend = VTracerVectorizerBackend()
                    vector_result = backend.vectorize(path, active_settings)
                except Exception as vt_error:
                    fallback_settings = copy.deepcopy(active_settings)
                    fallback_settings.engine_type = "OpenCV Legacy"
                    try:
                        backend = OpenCVVectorizerBackend()
                        vector_result = backend.vectorize(path, fallback_settings)
                        vector_result.fallback_error = str(vt_error)
                    except Exception as cv_error:
                        raise RuntimeError(
                            f"VTracer failed: {str(vt_error)}. Fallback OpenCV Legacy also failed: {str(cv_error)}"
                        ) from cv_error
            else:
                backend = OpenCVVectorizerBackend()
                vector_result = backend.vectorize(path, active_settings)
            
            # 3. Safe filename handling to avoid overwrite
            unique_path = get_unique_filepath(str(output_path), svg_filename)
            
            # 4. Export SVG
            export_svg(vector_result, unique_path, filename)
            
            success_count += 1
            _report_progress(progress_callback, idx + 1, total, filename, True)
        except Exception as error:
            failed_count += 1
            errors[filename] = str(error)
            _report_progress(progress_callback, idx + 1, total, filename, False)

    return success_count, failed_count, errors


def _report_progress(
    progress_callback,
    index: int,
    total: int,
    filename: str,
    success: bool,
) -> None:
    """Report progress without allowing UI callback failures to stop the batch."""
    if progress_callback is None:
        return
    try:
        progress_callback(index, total, filename, success)
    except Exception:
        pass
