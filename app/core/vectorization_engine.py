"""Vectorization engine for converting binary/threshold images into vector paths.

Handles:
- Vector data model (VectorPath, VectorResult)
- Contour detection from binary images
- Contour filtering and simplification
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Vector data model
# ---------------------------------------------------------------------------

@dataclass
class VectorPath:
    """A single detected vector path represented as a sequence of (x, y) points."""
    points: np.ndarray      # shape (N, 2), dtype int32
    area: float             # contour area in pixels
    color: tuple[int, int, int] = (30, 144, 255)
    holes: list[np.ndarray] = field(default_factory=list)

    @property
    def point_count(self) -> int:
        return len(self.points)


@dataclass
class VectorResult:
    """Container for all vector paths detected in an image."""
    paths: list[VectorPath] = field(default_factory=list)
    image_width: int = 0
    image_height: int = 0
    original_point_count: int = 0
    simplified_point_count: int = 0
    fallback_error: str | None = None

    @property
    def path_count(self) -> int:
        return len(self.paths)


# ---------------------------------------------------------------------------
# Vectorization settings
# ---------------------------------------------------------------------------

from app.config.settings import VectorizationSettings


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def vectorize(
    binary_array: np.ndarray,
    settings: VectorizationSettings | None = None,
    color_array: np.ndarray | None = None,
) -> VectorResult:
    """Convert a binary/threshold numpy image array into a VectorResult.

    Args:
        binary_array: Single-channel (H, W) uint8 numpy array (binary image).
        settings: Optional VectorizationSettings; defaults used if None.
        color_array: Optional original BGR image for color quantization & background removal.

    Returns:
        VectorResult containing detected VectorPath objects.

    Raises:
        ValueError: If the input array is invalid.
    """
    if settings is None:
        settings = VectorizationSettings()

    if not isinstance(binary_array, np.ndarray) or binary_array.ndim != 2:
        raise ValueError("binary_array must be a 2D (H x W) single-channel image.")
    if binary_array.size == 0:
        raise ValueError("binary_array must not be empty.")
    if not np.issubdtype(binary_array.dtype, np.number):
        raise ValueError("binary_array must contain numeric pixel values.")
    if not np.isfinite(binary_array).all():
        raise ValueError("binary_array must contain only finite pixel values.")
    if not math.isfinite(settings.min_area) or settings.min_area < 0:
        raise ValueError("min_area must be greater than or equal to zero.")
    if not math.isfinite(settings.approx_tolerance) or settings.approx_tolerance < 0:
        raise ValueError("approx_tolerance must be greater than or equal to zero.")
    if not isinstance(settings.color_count, int) or isinstance(settings.color_count, bool):
        raise ValueError("color_count must be an integer.")
    if settings.color_count < 1:
        raise ValueError("color_count must be greater than zero.")

    height, width = binary_array.shape
    working = np.where(binary_array > 0, 255, 0).astype(np.uint8)
    valid_pixel_mask = np.ones((height, width), dtype=bool)

    # 1. Edge preservation (apply Bilateral Filter if enabled)
    if settings.preserve_edges:
        working = cv2.bilateralFilter(working, 9, 75, 75)

    # 2. Color Quantization & Background Removal
    alpha_mask = None
    if color_array is not None and color_array.ndim == 3 and color_array.shape[:2] == (height, width):
        if color_array.shape[2] == 4:
            alpha_mask = color_array[:, :, 3] > 0
            valid_pixel_mask &= alpha_mask
            target_color_array = color_array[:, :, :3].copy()
        elif color_array.shape[2] == 3:
            target_color_array = color_array.copy()
        else:
            raise ValueError("color_array must have three BGR or four BGRA channels.")

        # Background Removal
        if settings.remove_background:
            # Detect background color from average of the 4 corners
            corners = [
                target_color_array[0, 0],
                target_color_array[0, width - 1],
                target_color_array[height - 1, 0],
                target_color_array[height - 1, width - 1]
            ]
            bg_color = np.mean(corners, axis=0).astype(np.uint8)

            # Mask out background colors based on Euclidean distance and tolerance
            dist = np.linalg.norm(target_color_array.astype(np.float32) - bg_color.astype(np.float32), axis=2)
            bg_mask = dist < settings.bg_tolerance
            foreground_mask = ~bg_mask
            if alpha_mask is not None:
                foreground_mask &= alpha_mask
            working = np.where(foreground_mask, 255, 0).astype(np.uint8)
        elif alpha_mask is not None:
            working[~alpha_mask] = 0

        # Color vectorization must use the original image regions rather than
        # the single binary threshold mask. The mask remains useful for
        # monochrome input and threshold preview, but it would discard most
        # colors and details from photos and artwork.
        color_foreground = valid_pixel_mask.copy()
        if settings.remove_background:
            color_foreground &= foreground_mask

        cluster_count = settings.color_count if settings.color_mode == "Custom colors" else 64
        target_color_array = _quantize_colors(
            target_color_array,
            color_foreground,
            cluster_count,
            preserve_edges=settings.preserve_edges,
        )
        working = np.where(color_foreground, 255, 0).astype(np.uint8)
    else:
        target_color_array = None

    # 3. Optional invert
    if settings.invert:
        working = cv2.bitwise_not(working)
        working[~valid_pixel_mask] = 0

    # 4. Optional smoothing to reduce noise before contour detection
    if settings.smoothing_enabled:
        working = cv2.GaussianBlur(working, (5, 5), 0)
        _, working = cv2.threshold(working, 127, 255, cv2.THRESH_BINARY)
        working[~valid_pixel_mask] = 0

    original_points = 0
    simplified_points = 0
    paths: list[VectorPath] = []

    if (
        target_color_array is not None
        and not settings.remove_background
        and np.all(valid_pixel_mask)
    ):
        foreground_colors = target_color_array[working > 0].reshape(-1, 3)
        if len(foreground_colors):
            colors, counts = np.unique(foreground_colors, axis=0, return_counts=True)
            blue, green, red = colors[np.argmax(counts)]
            canvas_points = np.array(
                [[0, 0], [width, 0], [width, height], [0, height]],
                dtype=np.int32,
            )
            paths.append(
                VectorPath(
                    points=canvas_points,
                    area=float(width * height),
                    color=(int(red), int(green), int(blue)),
                )
            )

    contour_masks = _build_contour_masks(working, target_color_array)
    for contour_mask, region_color in contour_masks:
        contours, hierarchy = cv2.findContours(
            contour_mask,
            cv2.RETR_CCOMP,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        if hierarchy is None:
            continue

        for contour_index, contour in enumerate(contours):
            # Child contours are holes and are attached to their outer path.
            if hierarchy[0][contour_index][3] != -1:
                continue

            hole_contours: list[np.ndarray] = []
            hole_index = hierarchy[0][contour_index][2]
            while hole_index != -1:
                hole_contours.append(contours[hole_index])
                hole_index = hierarchy[0][hole_index][0]

            area = cv2.contourArea(contour) - sum(
                cv2.contourArea(hole) for hole in hole_contours
            )
            if area < settings.min_area:
                continue

            original_points += len(contour) + sum(len(hole) for hole in hole_contours)
            simplified = cv2.approxPolyDP(
                contour,
                settings.approx_tolerance,
                closed=True,
            )
            simplified_holes = [
                cv2.approxPolyDP(hole, settings.approx_tolerance, closed=True).reshape(-1, 2)
                for hole in hole_contours
                if cv2.contourArea(hole) >= settings.min_area
            ]
            simplified_points += len(simplified) + sum(len(hole) for hole in simplified_holes)
            points = simplified.reshape(-1, 2)
            path_color = region_color or _mean_contour_color(
                contour,
                target_color_array,
                binary_array.shape,
            )
            paths.append(
                VectorPath(
                    points=points,
                    area=area,
                    color=path_color,
                    holes=simplified_holes,
                )
            )

    # Larger color regions form the background layers. Painting them first
    # allows smaller internal regions to remain visible in preview and SVG.
    paths.sort(key=lambda path: path.area, reverse=True)

    return VectorResult(
        paths=paths,
        image_width=width,
        image_height=height,
        original_point_count=original_points,
        simplified_point_count=simplified_points
    )


def _build_contour_masks(
    working: np.ndarray,
    color_array: np.ndarray | None,
) -> list[tuple[np.ndarray, tuple[int, int, int] | None]]:
    """Build one foreground mask or separate masks for each detected color."""
    foreground = working > 0
    if color_array is None:
        return [(working, None)]

    masks: list[tuple[np.ndarray, tuple[int, int, int] | None]] = []
    for bgr_color in np.unique(color_array[foreground].reshape(-1, 3), axis=0):
        color_pixels = np.all(color_array == bgr_color, axis=2)
        region_mask = np.where(foreground & color_pixels, 255, 0).astype(np.uint8)
        rgb_color = (int(bgr_color[2]), int(bgr_color[1]), int(bgr_color[0]))
        masks.append((region_mask, rgb_color))
    return masks


def _quantize_colors(
    color_array: np.ndarray,
    foreground: np.ndarray,
    requested_clusters: int,
    *,
    preserve_edges: bool,
) -> np.ndarray:
    """Reduce image colors into stable regions suitable for vector paths."""
    result = color_array.copy()
    pixels = color_array[foreground].reshape((-1, 3))
    if len(pixels) == 0:
        return result

    # Training K-Means on a representative sample keeps large photos
    # responsive while all foreground pixels are still assigned afterwards.
    max_training_pixels = 100_000
    if len(pixels) > max_training_pixels:
        sample_indices = np.linspace(
            0,
            len(pixels) - 1,
            max_training_pixels,
            dtype=np.int64,
        )
        training_pixels = pixels[sample_indices]
    else:
        training_pixels = pixels

    unique_training = np.unique(training_pixels, axis=0)
    cluster_count = min(requested_clusters, len(unique_training))
    if cluster_count <= 1:
        result[foreground] = unique_training[0]
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
        distances = np.sum(
            (chunk[:, None, :] - center_values[None, :, :]) ** 2,
            axis=2,
        )
        quantized_labels[start:start + chunk_size] = np.argmin(distances, axis=1)

    # Median filtering cluster labels removes isolated photo noise while
    # retaining the finite palette and producing coherent vector regions.
    label_map = np.full(foreground.shape, 255, dtype=np.uint8)
    label_map[foreground] = quantized_labels
    kernel_size = 3 if preserve_edges else 5
    filtered_labels = cv2.medianBlur(label_map, kernel_size)
    invalid_filtered = filtered_labels >= cluster_count
    filtered_labels[invalid_filtered] = label_map[invalid_filtered]
    result[foreground] = centers[filtered_labels[foreground]]
    return result


def _mean_contour_color(
    contour: np.ndarray,
    color_array: np.ndarray | None,
    image_shape: tuple[int, int],
) -> tuple[int, int, int]:
    """Return the average RGB color inside a contour."""
    if color_array is None:
        return (30, 144, 255)

    mask = np.zeros(image_shape, dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    blue, green, red = cv2.mean(color_array, mask=mask)[:3]
    return (int(red), int(green), int(blue))
