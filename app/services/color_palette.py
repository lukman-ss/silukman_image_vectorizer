"""Color palette extraction and replacement helpers."""

from __future__ import annotations

import cv2
import numpy as np


ColorRGB = tuple[int, int, int]
ColorReplacement = tuple[ColorRGB, ColorRGB]


def extract_dominant_colors(file_path: str, max_colors: int = 10) -> list[ColorRGB]:
    """Return up to max_colors dominant RGB colors from an image."""
    if max_colors < 1:
        return []

    image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("Failed to read image for color palette extraction.")

    if image.ndim == 2:
        bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        foreground = np.ones(image.shape[:2], dtype=bool)
    elif image.ndim == 3 and image.shape[2] == 4:
        bgr = image[:, :, :3]
        foreground = image[:, :, 3] > 0
    elif image.ndim == 3 and image.shape[2] == 3:
        bgr = image
        foreground = np.ones(image.shape[:2], dtype=bool)
    else:
        raise ValueError("Unsupported image channel layout for palette extraction.")

    pixels = bgr[foreground].reshape(-1, 3)
    if len(pixels) == 0:
        return []

    max_sample_pixels = 80_000
    if len(pixels) > max_sample_pixels:
        sample_indices = np.linspace(0, len(pixels) - 1, max_sample_pixels, dtype=np.int64)
        pixels = pixels[sample_indices]

    unique_colors, unique_counts = np.unique(pixels, axis=0, return_counts=True)
    if len(unique_colors) <= max_colors:
        order = np.argsort(unique_counts)[::-1]
        return [_bgr_to_rgb_tuple(unique_colors[index]) for index in order]

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
    cv2.setRNGSeed(42)
    _, labels, centers = cv2.kmeans(
        pixels.astype(np.float32),
        max_colors,
        None,
        criteria,
        3,
        cv2.KMEANS_PP_CENTERS,
    )
    centers = np.uint8(np.clip(np.rint(centers), 0, 255))
    counts = np.bincount(labels.flatten(), minlength=len(centers))
    order = np.argsort(counts)[::-1]

    palette: list[ColorRGB] = []
    for index in order:
        color = _bgr_to_rgb_tuple(centers[index])
        if color not in palette:
            palette.append(color)
    return palette[:max_colors]


def apply_palette_replacements(
    image: np.ndarray,
    replacements: list[ColorReplacement],
    *,
    tolerance: float = 36.0,
) -> np.ndarray:
    """Replace colors in a BGR/BGRA image using RGB replacement pairs."""
    if not replacements:
        return image

    if image.ndim == 2:
        working = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif image.ndim == 3 and image.shape[2] in (3, 4):
        working = image.copy()
    else:
        raise ValueError("Unsupported image channel layout for palette replacement.")

    color_part = working[:, :, :3]
    valid_pixels = np.ones(working.shape[:2], dtype=bool)
    if working.ndim == 3 and working.shape[2] == 4:
        valid_pixels &= working[:, :, 3] > 0

    for source_rgb, replacement_rgb in replacements:
        source_bgr = np.array(source_rgb[::-1], dtype=np.float32)
        replacement_bgr = np.array(replacement_rgb[::-1], dtype=np.uint8)
        distance = np.linalg.norm(color_part.astype(np.float32) - source_bgr, axis=2)
        mask = valid_pixels & (distance <= tolerance)
        color_part[mask] = replacement_bgr

    return working


def color_to_hex(color: ColorRGB) -> str:
    """Return a CSS-style hex string for an RGB color."""
    red, green, blue = color
    return f"#{red:02x}{green:02x}{blue:02x}"


def _bgr_to_rgb_tuple(color) -> ColorRGB:
    blue, green, red = [int(channel) for channel in color[:3]]
    return (red, green, blue)
