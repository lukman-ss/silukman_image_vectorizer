from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.config.settings import VectorizationSettings
from app.core.vectorization_engine import VectorResult
from app.core.vectorization_engine import vectorize as opencv_vectorize

# Safe import handling for vtracer
try:
    import vtracer

    VTRACER_AVAILABLE = True
except ImportError:
    vtracer = None
    VTRACER_AVAILABLE = False


@dataclass
class VTracerVectorResult(VectorResult):
    """Subclass of VectorResult that wraps raw SVG string from vtracer."""

    svg_data: str = ""
    _path_count: int = 0

    @property
    def path_count(self) -> int:
        return self._path_count


class VectorizerBackend:
    """Abstract/base class representing a vectorization engine backend."""

    def vectorize(
        self,
        input_path: str,
        settings: VectorizationSettings,
        thresholded_array: np.ndarray | None = None,
    ) -> VectorResult:
        """Run the vectorization on the input file and return VectorResult."""
        raise NotImplementedError

    def supports_color(self) -> bool:
        """Return True if backend supports full-color vectorization."""
        raise NotImplementedError

    def supports_svg_output(self) -> bool:
        """Return True if backend natively outputs SVG strings."""
        raise NotImplementedError

    def get_engine_name(self) -> str:
        """Return the user-friendly name of the engine."""
        raise NotImplementedError


class OpenCVVectorizerBackend(VectorizerBackend):
    """Legacy vectorization backend using OpenCV contour detection and Douglas-Peucker."""

    def vectorize(
        self,
        input_path: str,
        settings: VectorizationSettings,
        thresholded_array: np.ndarray | None = None,
    ) -> VectorResult:
        if thresholded_array is None:
            # We assume grayscale thresholding was already done by preprocessing and saved to input_path,
            # or we do it here if missing. Actually, since we orchestrate it, if it's missing we just read and threshold.
            img_data = np.fromfile(input_path, np.uint8)
            gray = cv2.imdecode(img_data, cv2.IMREAD_GRAYSCALE) if img_data.size > 0 else None
            threshold_val = getattr(settings, "threshold_val", 127)
            if gray is not None:
                _, thresholded = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY)
            else:
                raise ValueError("Failed to read image for OpenCV vectorization")
        else:
            thresholded = thresholded_array

        # Read color image for path colors (it is already preprocessed in input_path)
        img_data_color = np.fromfile(input_path, np.uint8)
        color_array = cv2.imdecode(img_data_color, cv2.IMREAD_UNCHANGED) if img_data_color.size > 0 else None

        # Call legacy vectorize
        return opencv_vectorize(thresholded, settings, color_array)

    def supports_color(self) -> bool:
        return True

    def supports_svg_output(self) -> bool:
        return False

    def get_engine_name(self) -> str:
        return "OpenCV Legacy"


class VTracerVectorizerBackend(VectorizerBackend):
    """Primary vectorization backend using Visioncortex VTracer."""

    def vectorize(
        self,
        input_path: str,
        settings: VectorizationSettings,
        thresholded_array: np.ndarray | None = None,
    ) -> VectorResult:
        if not VTRACER_AVAILABLE or vtracer is None:
            raise RuntimeError(
                "VTracer dependency is missing. Fallback to OpenCV Legacy or install vtracer."
            )

        if not input_path:
            raise ValueError("VTracer requires a source image path.")
        source_path = Path(input_path)
        if not source_path.exists() or not source_path.is_file():
            raise ValueError("VTracer source image file does not exist.")

        temp_file = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
        temp_file_path = temp_file.name
        temp_file.close()

        try:
            # Map settings to vtracer parameters
            kwargs = {}
            vt_settings = getattr(settings, "vtracer", None) or settings

            kwargs["colormode"] = getattr(vt_settings, "colormode", "color")
            kwargs["hierarchical"] = getattr(vt_settings, "hierarchical", "stacked")
            kwargs["mode"] = getattr(vt_settings, "mode", "spline")
            kwargs["filter_speckle"] = _clamp_int(
                getattr(vt_settings, "filter_speckle", 4), 0, 1024
            )
            kwargs["color_precision"] = _clamp_int(getattr(vt_settings, "color_precision", 6), 1, 8)
            kwargs["layer_difference"] = _clamp_int(
                getattr(vt_settings, "layer_difference", 16), 0, 255
            )
            kwargs["corner_threshold"] = _clamp_int(
                getattr(vt_settings, "corner_threshold", 60), 0, 180
            )
            kwargs["length_threshold"] = _clamp_float(
                getattr(vt_settings, "length_threshold", 4.0), 3.5, 10.0
            )
            kwargs["max_iterations"] = _clamp_int(
                getattr(vt_settings, "max_iterations", 10), 1, 100
            )
            kwargs["splice_threshold"] = _clamp_int(
                getattr(vt_settings, "splice_threshold", 45), 0, 180
            )
            kwargs["path_precision"] = _clamp_int(getattr(vt_settings, "path_precision", 8), 0, 16)

            # Execute convert
            vtracer.convert_image_to_svg_py(input_path, temp_file_path, **kwargs)

            # Read back generated SVG data
            with open(temp_file_path, "r", encoding="utf-8") as f:
                svg_data = f.read()
            if not svg_data.strip():
                raise RuntimeError("VTracer generated an empty SVG document.")

            # Retrieve dimensions
            from PIL import Image

            try:
                with Image.open(source_path) as img_pil:
                    w, h = img_pil.size
            except Exception:
                img_data_dims = np.fromfile(str(source_path), np.uint8)
                img_dims = cv2.imdecode(img_data_dims, cv2.IMREAD_COLOR) if img_data_dims.size > 0 else None
                h, w = (
                    (img_dims.shape[0], img_dims.shape[1]) if img_dims is not None else (400, 400)
                )

            # Parse path counts and point count heuristics using postprocessing
            from app.core.postprocessing import calculate_svg_metrics, parse_and_validate_svg

            try:
                root = parse_and_validate_svg(svg_data)
                metrics = calculate_svg_metrics(root)
                path_count = metrics["path_count"]
                simplified_points = metrics["simplified_point_count"]
                original_points = metrics["original_point_count"]
            except ValueError as e:
                raise RuntimeError(f"VTracer generated invalid SVG: {e}")

            result = VTracerVectorResult(
                paths=[],
                image_width=w,
                image_height=h,
                original_point_count=original_points,
                simplified_point_count=simplified_points,
                svg_data=svg_data,
                _path_count=path_count,
            )
            return result

        finally:
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass

    def supports_color(self) -> bool:
        return True

    def supports_svg_output(self) -> bool:
        return True

    def get_engine_name(self) -> str:
        return "VTracer"


def _clamp_int(value, minimum: int, maximum: int) -> int:
    """Convert a value to int and clamp it to the supported range."""
    return max(minimum, min(maximum, int(value)))


def _clamp_float(value, minimum: float, maximum: float) -> float:
    """Convert a value to float and clamp it to the supported range."""
    return max(minimum, min(maximum, float(value)))
