"""Background worker threads for image processing, vectorization, and batch ops."""

from __future__ import annotations

import copy
from typing import Optional

import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from app.config.settings import VectorizationSettings


class ImageProcessorThread(QThread):
    """Worker thread to run grayscale threshold pipeline in the background."""

    # Emits (QImage, np.ndarray) on success, or str error message on failure
    result_ready = Signal(object)

    def __init__(self, file_path: str, threshold_val: int, parent=None) -> None:
        super().__init__(parent)
        self.file_path = file_path
        self.threshold_val = threshold_val

    def run(self) -> None:
        try:
            import cv2

            from app.core.preprocessing import apply_grayscale_threshold

            img = cv2.imread(self.file_path, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise ValueError("Failed to read image")
            thresholded, _ = apply_grayscale_threshold(img, self.threshold_val)

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
            self.result_ready.emit((q_image.copy(), thresholded))
        except Exception as error:
            self.result_ready.emit(str(error))


class VectorizationThread(QThread):
    """Worker thread to run the vectorization engine in the background."""

    # Emits VectorResult or str error message
    result_ready = Signal(object)

    def __init__(
        self,
        thresholded_array: np.ndarray,
        settings: VectorizationSettings,
        file_path: Optional[str],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.thresholded_array = thresholded_array.copy()
        self.settings = copy.deepcopy(settings)
        self.file_path = file_path

    def run(self) -> None:
        try:
            from app.core.vectorizer_backend import (
                OpenCVVectorizerBackend,
                VTracerVectorizerBackend,
            )

            if self.settings.engine_type == "VTracer":
                try:
                    backend = VTracerVectorizerBackend()
                    vector_result = backend.vectorize(self.file_path, self.settings)
                except Exception as e:
                    fallback_settings = copy.deepcopy(self.settings)
                    fallback_settings.engine_type = "OpenCV Legacy"
                    backend = OpenCVVectorizerBackend()
                    vector_result = backend.vectorize(
                        self.file_path, fallback_settings, self.thresholded_array
                    )
                    vector_result.fallback_error = str(e)
            else:
                backend = OpenCVVectorizerBackend()
                vector_result = backend.vectorize(
                    self.file_path, self.settings, self.thresholded_array
                )

            self.result_ready.emit(vector_result)
        except Exception as error:
            self.result_ready.emit(str(error))


class BatchProcessingThread(QThread):
    """Worker thread for batch processing and SVG export."""

    progress = Signal(int, int, str, bool)
    result_ready = Signal(object)  # (success_count, failed_count, errors) or str

    def __init__(
        self,
        file_paths: list[str],
        output_dir: str,
        threshold_val: int,
        vector_settings: VectorizationSettings,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.file_paths = list(file_paths)
        self.output_dir = output_dir
        self.threshold_val = threshold_val
        self.vector_settings = copy.deepcopy(vector_settings)

    def run(self) -> None:
        try:
            from app.services.batch_processor import process_batch

            result = process_batch(
                file_paths=self.file_paths,
                output_dir=self.output_dir,
                threshold_val=self.threshold_val,
                vector_settings=self.vector_settings,
                progress_callback=self.progress.emit,
            )
            self.result_ready.emit(result)
        except Exception as error:
            self.result_ready.emit(str(error))
