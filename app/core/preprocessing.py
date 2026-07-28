import cv2
import numpy as np
import time
from typing import Tuple, List, Dict, Any
from pathlib import Path

from app.config.settings import VectorizationConfig


def apply_background_removal(img: np.ndarray, tolerance: float) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Removes the background by matching the corner colors and replacing them with transparency."""
    start_time = time.time()
    
    # Must be 3D and at least BGR
    if img.ndim == 2:
        result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.ndim == 3 and img.shape[2] == 1:
        result = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    elif img.ndim == 3 and img.shape[2] in (3, 4):
        result = img.copy()
    else:
        raise ValueError("Unsupported image channel layout for background removal.")

    if result.shape[2] == 3:
        result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)

    h, w = result.shape[:2]
    corners = [
        result[0, 0, :3],
        result[0, w - 1, :3],
        result[h - 1, 0, :3],
        result[h - 1, w - 1, :3]
    ]
    bg_color = np.mean(corners, axis=0)

    diff = np.linalg.norm(result[:, :, :3].astype(np.float32) - bg_color.astype(np.float32), axis=2)
    bg_mask = diff < tolerance
    result[bg_mask, 3] = 0
    
    pixels_removed = int(np.sum(bg_mask))

    metadata = {
        "operation": "background_removal",
        "tolerance": tolerance,
        "pixels_removed": pixels_removed,
        "bg_color_estimated": bg_color.tolist(),
        "duration_sec": time.time() - start_time
    }
    return result, metadata


def apply_palette_replacements(img: np.ndarray, replacements: List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]]) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Replaces specific RGB colors in the image with another color."""
    if not replacements:
        return img.copy(), {}

    start_time = time.time()
    result = img.copy()
    
    # Convert grayscale to color if necessary
    if result.ndim == 2:
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

    has_alpha = result.shape[2] == 4
    pixels_modified = 0

    for original_color, new_color in replacements:
        orig_bgr = np.array([original_color[2], original_color[1], original_color[0]], dtype=np.uint8)
        new_bgr = np.array([new_color[2], new_color[1], new_color[0]], dtype=np.uint8)

        mask = cv2.inRange(result[:, :, :3], orig_bgr, orig_bgr)
        count = int(np.sum(mask > 0))
        if count > 0:
            result[mask > 0, :3] = new_bgr
            pixels_modified += count
            if has_alpha:
                # Ensure modified pixels are fully opaque
                result[mask > 0, 3] = 255

    metadata = {
        "operation": "palette_replacement",
        "replacements_count": len(replacements),
        "pixels_modified": pixels_modified,
        "duration_sec": time.time() - start_time
    }
    return result, metadata


def apply_color_quantization(img: np.ndarray, max_colors: int, preserve_edges: bool = False) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Quantize colors of the image (RGB or RGBA) to max_colors using K-Means."""
    if max_colors <= 0:
        return img.copy(), {}

    start_time = time.time()
    
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
        return img.copy(), {"operation": "color_quantization", "message": "Empty foreground"}

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
        return result, {"operation": "color_quantization", "cluster_count": 1}

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

    metadata = {
        "operation": "color_quantization",
        "requested_colors": max_colors,
        "actual_colors": cluster_count,
        "preserve_edges": preserve_edges,
        "duration_sec": time.time() - start_time
    }
    return result, metadata


def apply_grayscale_threshold(img: np.ndarray, threshold_val: int) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Converts image to grayscale and applies a binary threshold."""
    start_time = time.time()
    
    if img.ndim == 2:
        gray = img.copy()
    elif img.shape[2] == 4:
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    elif img.shape[2] == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        raise ValueError("Unsupported image channel layout for grayscale conversion.")

    _, thresholded = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY)
    
    metadata = {
        "operation": "grayscale_threshold",
        "threshold_val": threshold_val,
        "duration_sec": time.time() - start_time
    }
    return thresholded, metadata


def preprocess_image(input_path: str, config: VectorizationConfig) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Orchestrates the preprocessing steps on an image.
    Returns the processed image and a list of metadata for each step applied.
    """
    path = Path(input_path)
    if not path.exists():
        raise ValueError(f"Image not found at {input_path}")
        
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Failed to load image for preprocessing from {input_path}")
        
    metadata_log = []
    
    # 1. Background removal
    if config.remove_background:
        img, meta = apply_background_removal(img, config.bg_tolerance)
        metadata_log.append(meta)
        
    # 2. Palette replacements
    if config.palette_replacements:
        img, meta = apply_palette_replacements(img, config.palette_replacements)
        metadata_log.append(meta)
        
    # 3. Quantization
    if config.color_mode == "Custom colors":
        img, meta = apply_color_quantization(img, config.color_count, config.preserve_edges)
        metadata_log.append(meta)
        
    # Note: Grayscale thresholding is only used for OpenCV Legacy, or as a standalone UI pipeline.
    # It is not applied globally to VTracer inputs. The VectorizationService or Backend handles 
    # whether to apply it explicitly depending on the engine.
    
    return img, metadata_log
