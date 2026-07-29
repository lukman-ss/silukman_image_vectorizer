import datetime
import os
import tempfile
import time
import uuid
from pathlib import Path

import cv2

from app.config.settings import VectorizationSettings
from app.core.exceptions import InputImageError, PreprocessingError, VectorizationError, SvgValidationError, ConfigurationError
from app.core.result import VectorizationResult, calculate_file_hash


def vectorize_image(
    input_path: str,
    output_path: str,
    config: VectorizationSettings,
) -> VectorizationResult:
    """Core function to convert an image to an SVG vector file.

    Args:
        input_path: Path to the source raster image.
        output_path: Path where the SVG should be saved.
        config: VectorizationSettings instance.

    Returns:
        VectorizationResult containing process statistics and final state.
    """
    from app.core.postprocessing import calculate_svg_metrics, parse_and_validate_svg
    from app.core.preprocessing import apply_grayscale_threshold, preprocess_image
    from app.core.vectorizer_backend import (
        OpenCVVectorizerBackend,
        VectorizerBackend,
        VTracerVectorizerBackend,
    )
    from app.services.svg_exporter import export_svg, normalize_svg_path

    # Initialization
    run_id = str(uuid.uuid4())
    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    start_time_perf = time.perf_counter()
    warnings = []

    # Base Result Template
    result = VectorizationResult(
        run_id=run_id,
        started_at=started_at,
        input_path=input_path,
        configuration=config.to_dict() if hasattr(config, "to_dict") else vars(config),
        status="failed",  # Defaults to failed, updated at the end
    )

    # Input Validation & Metadata
    if not os.path.exists(input_path):
        result.error_type = "InputImageError"
        result.error_message = "Input file not found."
        _finalize_result(result, start_time_perf)
        raise InputImageError(f"Input file not found: {input_path}")

    try:
        normalized_output_path = normalize_svg_path(output_path)
    except Exception as e:
        result.error_type = "VectorizationError"
        result.error_message = f"Invalid output path: {str(e)}"
        _finalize_result(result, start_time_perf)
        raise VectorizationError(result.error_message)

    result.input_sha256 = calculate_file_hash(input_path)
    result.input_file_size = os.path.getsize(input_path)
    result.input_format = Path(input_path).suffix.lower().lstrip(".") or "unknown"

    import numpy as np
    img_data = np.fromfile(input_path, np.uint8)
    img_info = cv2.imdecode(img_data, cv2.IMREAD_UNCHANGED) if img_data.size > 0 else None
    if img_info is None:
        result.error_type = "InputImageError"
        result.error_message = "Failed to read image or unsupported format."
        _finalize_result(result, start_time_perf)
        raise InputImageError(result.error_message)

    result.input_height, result.input_width = img_info.shape[:2]
    del img_info

    temp_input_png_path = None
    try:
        # 1. Preprocess
        preprocessed_img, preprocessing_log = preprocess_image(input_path, config)
        result.preprocessing_log = preprocessing_log

        temp_input_png = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_input_png_path = temp_input_png.name
        temp_input_png.close()

        if not cv2.imwrite(temp_input_png_path, preprocessed_img):
            raise PreprocessingError("Failed to write temporary preprocessed image.")

        thresholded_array = None
        if config.engine_type != "VTracer":
            thresholded_array, meta = apply_grayscale_threshold(
                preprocessed_img, config.threshold_val
            )
            result.preprocessing_log.append(meta)

        # 2. Vectorize
        backend: VectorizerBackend
        if config.engine_type == "VTracer":
            backend = VTracerVectorizerBackend()
        else:
            backend = OpenCVVectorizerBackend()

        vector_result = backend.vectorize(temp_input_png_path, config, thresholded_array)

        if getattr(vector_result, "fallback_error", None):
            warnings.append(
                f"VTracer failed, fell back to OpenCV Legacy. Error: {vector_result.fallback_error}"
            )

    except Exception as e:
        result.error_type = type(e).__name__
        result.error_message = str(e)
        _finalize_result(result, start_time_perf)
        raise PreprocessingError(f"Vectorization failed: {str(e)}") from e
    finally:
        if temp_input_png_path and os.path.exists(temp_input_png_path):
            try:
                os.remove(temp_input_png_path)
            except OSError:
                pass

    # 3. Export
    try:
        source_name = Path(input_path).name
        final_output_path = export_svg(
            vector_result, str(normalized_output_path), source_filename=source_name
        )
    except Exception as e:
        result.error_type = "VectorizationError"
        result.error_message = str(e)
        _finalize_result(result, start_time_perf)
        raise VectorizationError(f"Failed to export SVG: {str(e)}") from e

    # 4. Finalize Success
    result.output_path = str(final_output_path)
    result.output_file_size = os.path.getsize(final_output_path)
    result.output_sha256 = calculate_file_hash(str(final_output_path))
    result.warnings = warnings

    # Calculate SVG metrics securely from the written file
    try:
        with open(final_output_path, "r", encoding="utf-8") as f:
            svg_data = f.read()
        svg_root = parse_and_validate_svg(svg_data)
        metrics = calculate_svg_metrics(svg_root)
        result.path_count = metrics["path_count"]
        result.element_count = metrics["total_elements"]
        result.estimated_command_count = metrics["simplified_point_count"]
    except Exception as e:
        result.warnings.append(f"Failed to parse SVG metrics: {str(e)}")

    result.status = "success"
    _finalize_result(result, start_time_perf)

    # Optionally save the JSON sidecar if it is considered best practice,
    # but the API allows the caller to decide. We will just return it.
    return result


def _finalize_result(result: VectorizationResult, start_time_perf: float) -> None:
    """Helper to finalize timestamps and durations before returning."""
    end_time_perf = time.perf_counter()
    result.duration_seconds = end_time_perf - start_time_perf
    result.finished_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
