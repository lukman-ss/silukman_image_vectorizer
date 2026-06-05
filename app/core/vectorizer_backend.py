from __future__ import annotations
import os
import cv2
import numpy as np
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.config.settings import VectorizationSettings
from app.core.vectorization_engine import VectorResult, vectorize as opencv_vectorize

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

    def vectorize(self, input_path: str, settings: VectorizationSettings, thresholded_array: np.ndarray | None = None) -> VectorResult:
        from app.core.image_pipeline import process_image_pipeline

        if thresholded_array is None:
            # 1. Run the legacy image pipeline to get binary threshold image
            threshold_val = getattr(settings, "threshold_val", 127)
            _, thresholded = process_image_pipeline(input_path, threshold_val)
        else:
            thresholded = thresholded_array

        # 2. Read color image for path colors
        color_array = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
        replacements = getattr(settings, "palette_replacements", [])
        if color_array is not None and replacements:
            from app.services.color_palette import apply_palette_replacements

            color_array = apply_palette_replacements(color_array, replacements)

        # 3. Call legacy vectorize
        return opencv_vectorize(thresholded, settings, color_array)

    def supports_color(self) -> bool:
        return True

    def supports_svg_output(self) -> bool:
        return False

    def get_engine_name(self) -> str:
        return "OpenCV Legacy"


def quantize_image_colors(img: np.ndarray, max_colors: int, preserve_edges: bool = False) -> np.ndarray:
    """Quantize colors of the image (RGB or RGBA) to max_colors using K-Means."""
    if max_colors <= 0:
        return img

    has_alpha = img.shape[2] == 4 if img.ndim == 3 and img.shape[2] >= 3 else False
    if has_alpha:
        alpha = img[:, :, 3]
        foreground = alpha > 0
        color_part = img[:, :, :3]
    else:
        foreground = np.ones(img.shape[:2], dtype=bool)
        color_part = img if img.ndim == 3 else cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    pixels = color_part[foreground].reshape((-1, 3))
    if len(pixels) == 0:
        return img

    max_training_pixels = 100_000
    if len(pixels) > max_training_pixels:
        sample_indices = np.linspace(0, len(pixels) - 1, max_training_pixels, dtype=np.int64)
        training_pixels = pixels[sample_indices]
    else:
        training_pixels = pixels

    unique_training = np.unique(training_pixels, axis=0)
    cluster_count = min(max_colors, len(unique_training))
    if cluster_count <= 1:
        result = img.copy()
        fill_val = unique_training[0] if len(unique_training) > 0 else np.array([0, 0, 0], dtype=np.uint8)
        if has_alpha:
            result[foreground, :3] = fill_val
        else:
            if result.ndim == 3:
                result[foreground] = fill_val
            else:
                result[foreground] = int(np.mean(fill_val))
        return result

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    cv2.setRNGSeed(42)
    _, _, centers = cv2.kmeans(
        training_pixels.astype(np.float32),
        cluster_count,
        None,
        criteria,
        3,
        cv2.KMEANS_PP_CENTERS,
    )
    centers = np.uint8(np.clip(np.rint(centers), 0, 255))

    quantized_labels = np.empty(len(pixels), dtype=np.uint8)
    chunk_size = 50_000
    center_values = centers.astype(np.int32)
    for start in range(0, len(pixels), chunk_size):
        chunk = pixels[start:start + chunk_size].astype(np.int32)
        distances = np.sum((chunk[:, None, :] - center_values[None, :, :]) ** 2, axis=2)
        quantized_labels[start:start + chunk_size] = np.argmin(distances, axis=1)

    result = img.copy()
    label_map = np.full(img.shape[:2], 255, dtype=np.uint8)
    label_map[foreground] = quantized_labels
    kernel_size = 3 if preserve_edges else 5
    filtered_labels = cv2.medianBlur(label_map, kernel_size)
    invalid_filtered = filtered_labels >= cluster_count
    filtered_labels[invalid_filtered] = label_map[invalid_filtered]

    if has_alpha:
        result[foreground, :3] = centers[filtered_labels[foreground]]
    else:
        if result.ndim == 3:
            result[foreground] = centers[filtered_labels[foreground]]
        else:
            gray_centers = np.mean(centers, axis=1).astype(np.uint8)
            result[foreground] = gray_centers[filtered_labels[foreground]]

    return result


class VTracerVectorizerBackend(VectorizerBackend):
    """Primary vectorization backend using Visioncortex VTracer."""

    def vectorize(
        self,
        input_path: str,
        settings: VectorizationSettings,
        thresholded_array: np.ndarray | None = None,
    ) -> VectorResult:
        if not VTRACER_AVAILABLE or vtracer is None:
            raise RuntimeError("VTracer dependency is missing. Fallback to OpenCV Legacy or install vtracer.")

        if not input_path:
            raise ValueError("VTracer requires a source image path.")
        source_path = Path(input_path)
        if not source_path.exists() or not source_path.is_file():
            raise ValueError("VTracer source image file does not exist.")

        temp_file = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
        temp_file_path = temp_file.name
        temp_file.close()

        actual_input_path = input_path
        temp_input_png_path = None

        try:
            need_bg_removal = getattr(settings, "remove_background", False)
            need_quantization = getattr(settings, "color_mode", "Unlimited colors") == "Custom colors"
            replacements = getattr(settings, "palette_replacements", [])
            need_palette_replacement = bool(replacements)

            if need_bg_removal or need_quantization or need_palette_replacement:
                img = cv2.imread(str(source_path), cv2.IMREAD_UNCHANGED)
                if img is None:
                    raise ValueError("Failed to read image for preprocessing.")

                # Apply background removal first if requested
                if need_bg_removal:
                    try:
                        # Convert grayscale (2D) or single-channel color to 3D BGR
                        if img.ndim == 2:
                            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                        elif img.ndim == 3 and img.shape[2] == 1:
                            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

                        if img.ndim != 3 or img.shape[2] not in (3, 4):
                            raise ValueError("Image must be converted to BGR/BGRA color array for background removal.")

                        if img.shape[2] == 3:
                            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)

                        h, w = img.shape[:2]
                        corners = [
                            img[0, 0, :3],
                            img[0, w - 1, :3],
                            img[h - 1, 0, :3],
                            img[h - 1, w - 1, :3]
                        ]
                        bg_color = np.mean(corners, axis=0)

                        diff = np.linalg.norm(img[:, :, :3].astype(np.float32) - bg_color.astype(np.float32), axis=2)
                        bg_mask = diff < getattr(settings, "bg_tolerance", 20.0)
                        img[bg_mask, 3] = 0
                    except Exception as e:
                        raise RuntimeError(f"Background removal failed: {str(e)}") from e

                if need_palette_replacement:
                    try:
                        from app.services.color_palette import apply_palette_replacements

                        img = apply_palette_replacements(img, replacements)
                    except Exception as e:
                        raise RuntimeError(f"Palette replacement failed: {str(e)}") from e

                # Apply color quantization to limit maximum colors
                if need_quantization:
                    try:
                        color_count = getattr(settings, "color_count", 8)
                        preserve_edges = getattr(settings, "preserve_edges", False)
                        img = quantize_image_colors(img, color_count, preserve_edges)
                    except Exception as e:
                        raise RuntimeError(f"Color quantization failed: {str(e)}") from e

                temp_input_png = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                temp_input_png_path = temp_input_png.name
                temp_input_png.close()

                if not cv2.imwrite(temp_input_png_path, img):
                    raise RuntimeError("Failed to write temporary preprocessed image.")
                actual_input_path = temp_input_png_path

            # Map settings to vtracer parameters
            kwargs = {}
            vt_settings = getattr(settings, "vtracer", None) or settings
            
            # colormode
            colormode = getattr(vt_settings, "colormode", "color")
            if colormode not in ("color", "binary"):
                colormode = "color"
            kwargs["colormode"] = colormode

            # hierarchical
            hierarchical = getattr(vt_settings, "hierarchical", "stacked")
            if hierarchical not in ("stacked", "cutout"):
                hierarchical = "stacked"
            kwargs["hierarchical"] = hierarchical

            # mode
            mode = getattr(vt_settings, "mode", "spline")
            if mode not in ("spline", "polygon", "none"):
                mode = "spline"
            kwargs["mode"] = mode

            # filter speckle
            kwargs["filter_speckle"] = _clamp_int(getattr(vt_settings, "filter_speckle", 4), 0, 1024)

            # color precision
            kwargs["color_precision"] = _clamp_int(getattr(vt_settings, "color_precision", 6), 1, 8)

            # layer difference
            kwargs["layer_difference"] = _clamp_int(getattr(vt_settings, "layer_difference", 16), 0, 255)

            # corner threshold
            kwargs["corner_threshold"] = _clamp_int(getattr(vt_settings, "corner_threshold", 60), 0, 180)

            # length threshold
            kwargs["length_threshold"] = _clamp_float(getattr(vt_settings, "length_threshold", 4.0), 3.5, 10.0)

            # max iterations
            kwargs["max_iterations"] = _clamp_int(getattr(vt_settings, "max_iterations", 10), 1, 100)

            # path precision
            kwargs["path_precision"] = _clamp_int(getattr(vt_settings, "path_precision", 8), 0, 16)

            # Execute convert using actual_input_path
            vtracer.convert_image_to_svg_py(actual_input_path, temp_file_path, **kwargs)

            # Read back generated SVG data
            with open(temp_file_path, "r", encoding="utf-8") as f:
                svg_data = f.read()
            if not svg_data.strip():
                raise RuntimeError("VTracer generated an empty SVG document.")

            # Retrieve dimensions using PIL to avoid full image decoding
            from PIL import Image
            try:
                with Image.open(source_path) as img_pil:
                    w, h = img_pil.size
            except Exception:
                img_dims = cv2.imread(str(source_path))
                h, w = (img_dims.shape[0], img_dims.shape[1]) if img_dims is not None else (400, 400)

            # Parse path counts and point count heuristics
            path_d_matches = re.findall(r"""<path[^>]*\sd=(["'])(.*?)\1""", svg_data, flags=re.IGNORECASE | re.DOTALL)
            path_count = len(path_d_matches)
            simplified_points = 0
            for _, d in path_d_matches:
                coords = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", d)
                simplified_points += len(coords) // 2

            original_points = simplified_points * 3

            result = VTracerVectorResult(
                paths=[],
                image_width=w,
                image_height=h,
                original_point_count=original_points,
                simplified_point_count=simplified_points,
                svg_data=svg_data,
                _path_count=path_count
            )
            return result

        finally:
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass
            if temp_input_png_path and os.path.exists(temp_input_png_path):
                try:
                    os.remove(temp_input_png_path)
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
