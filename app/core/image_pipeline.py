from __future__ import annotations

import cv2
import numpy as np
from PySide6.QtGui import QImage


def process_image_pipeline(file_path: str, threshold_val: int) -> tuple[QImage, np.ndarray]:
    """Run the image processing pipeline.

    Stages:
    1. Load image and convert to grayscale.
    2. Apply binary thresholding.
    """
    if not isinstance(threshold_val, int) or isinstance(threshold_val, bool):
        raise ValueError("Threshold value must be an integer.")
    if not 0 <= threshold_val <= 255:
        raise ValueError("Threshold value must be between 0 and 255.")

    img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError("Failed to load image for processing pipeline.")

    if img.ndim == 2:
        gray = img
    elif img.shape[2] == 4:
        gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    elif img.shape[2] == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        raise ValueError("Unsupported image channel layout.")

    # Stage 2: Threshold processing
    _, thresholded = cv2.threshold(gray, threshold_val, 255, cv2.THRESH_BINARY)

    # Convert grayscale/binary numpy array to QImage
    height, width = thresholded.shape
    thresholded = np.ascontiguousarray(thresholded)
    bytes_per_line = thresholded.strides[0]
    
    # QImage.Format_Grayscale8 is appropriate for single-channel 8-bit image data
    q_image = QImage(
        thresholded.data,
        width,
        height,
        bytes_per_line,
        QImage.Format.Format_Grayscale8
    )

    # Create a copy to ensure memory ownership of the pixel data is transferred to QImage
    return q_image.copy(), thresholded
