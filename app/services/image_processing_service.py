"""Service for headless image preprocessing operations (no Qt widgets)."""

from __future__ import annotations

from typing import Tuple

import numpy as np
from PySide6.QtGui import QImage

from app.core.preprocessing import apply_grayscale_threshold


class ImageProcessingService:
    """Provides image preprocessing operations for UI preview and vectorization pipeline."""

    def create_threshold_preview(
        self, file_path: str, threshold_val: int
    ) -> Tuple[QImage, np.ndarray]:
        """Apply grayscale threshold and return a QImage + the raw ndarray.

        Raises:
            ValueError: If the image cannot be read.
        """
        import cv2

        img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Failed to read image: {file_path}")

        thresholded, _ = apply_grayscale_threshold(img, threshold_val)

        height, width = thresholded.shape
        thresholded_contiguous = np.ascontiguousarray(thresholded)
        bytes_per_line = thresholded_contiguous.strides[0]

        q_image = QImage(
            thresholded_contiguous.data,
            width,
            height,
            bytes_per_line,
            QImage.Format.Format_Grayscale8,
        )
        return q_image.copy(), thresholded
