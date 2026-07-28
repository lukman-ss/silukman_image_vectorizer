"""VectorizerController — orchestration layer between UI events and services."""
from __future__ import annotations

import copy
import math
from typing import Callable, Optional

from app.config.settings import VectorizationSettings
from app.models.vectorization_state import VectorizationState
from app.services.export_service import ExportService
from app.services.file_dialog_service import FileDialogService
from app.services.image_loader_service import ImageLoaderService
from app.services.image_processing_service import ImageProcessingService
from app.services.settings_service import SettingsService
from app.services.validation_service import ValidationService
from app.workers.threads import (
    BatchProcessingThread,
    ImageProcessorThread,
    VectorizationThread,
)


class VectorizerController:
    """Connects UI events to services. Manages threading lifecycle and state."""

    def __init__(
        self,
        image_loader_service: ImageLoaderService,
        image_processing_service: ImageProcessingService,
        export_service: ExportService,
        file_dialog_service: FileDialogService,
        settings_service: SettingsService,
        validation_service: ValidationService,
    ) -> None:
        self._image_loader = image_loader_service
        self._image_processing = image_processing_service
        self._export = export_service
        self._file_dialog = file_dialog_service
        self._settings = settings_service
        self._validation = validation_service

        self.state = VectorizationState()
        self.vector_settings = VectorizationSettings()

        # Threading state
        self._processor_thread: Optional[ImageProcessorThread] = None
        self._vectorization_thread: Optional[VectorizationThread] = None
        self._batch_thread: Optional[BatchProcessingThread] = None
        self._processing_pending = False
        self._vectorization_pending = False
        self._discard_vectorization_result = False

        # Callbacks — set by MainWindow after construction
        self.on_processing_done: Optional[Callable] = None     # (q_image, thresholded_array)
        self.on_processing_error: Optional[Callable] = None    # (error_str)
        self.on_vectorization_done: Optional[Callable] = None  # (vector_result)
        self.on_vectorization_error: Optional[Callable] = None # (error_str)
        self.on_batch_progress: Optional[Callable] = None      # (index, total, filename, success)
        self.on_batch_done: Optional[Callable] = None          # (result)

    # ── Settings ────────────────────────────────────────────────────────────

    def get_theme(self) -> str:
        return self._settings.get_theme()

    def save_theme(self, theme_name: str) -> None:
        self._settings.set_theme(theme_name)

    # ── Image Loading ────────────────────────────────────────────────────────

    def load_image(self, file_path: str):
        """Load an image and update state. Returns (pixmap, image_info, error)."""
        pixmap, info, error = self._image_loader.load(file_path)
        if not error and info:
            from pathlib import Path
            self.state.input_path = Path(file_path)
            self.state.source_image = pixmap
            self.state.thresholded_array = None
            self.state.vector_result = None
        return pixmap, info, error

    # ── Processing ───────────────────────────────────────────────────────────

    def start_processing(self, file_path: str, threshold_val: int) -> None:
        """Start the background image processing pipeline."""
        if self._processor_thread and self._processor_thread.isRunning():
            self._processing_pending = True
            return

        if self._vectorization_thread and self._vectorization_thread.isRunning():
            self._discard_vectorization_result = True

        self._processor_thread = ImageProcessorThread(file_path, threshold_val)
        self._processor_thread.result_ready.connect(self._on_processing_finished)
        self._processor_thread.finished.connect(self._on_processing_thread_finished)
        self._processor_thread.start()

    def _on_processing_finished(self, result: object) -> None:
        if self._processing_pending:
            return
        from PySide6.QtGui import QImage
        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], QImage):
            q_img, thresholded = result
            self.state.thresholded_array = thresholded
            if self.on_processing_done:
                self.on_processing_done(q_img, thresholded)
        elif isinstance(result, str):
            if self.on_processing_error:
                self.on_processing_error(result)

    def _on_processing_thread_finished(self) -> None:
        self._processor_thread = None
        if self._processing_pending:
            self._processing_pending = False
            if self.state.input_path:
                self.start_processing(
                    str(self.state.input_path),
                    self.vector_settings.threshold_val,
                )

    # ── Vectorization ────────────────────────────────────────────────────────

    def run_vectorization(self, *, processing_completed: bool = False) -> bool:
        """Start vectorization background thread.

        Returns True if thread was launched, False if skipped (no data).
        """
        if self.state.thresholded_array is None:
            return False
        if self._vectorization_thread and self._vectorization_thread.isRunning():
            self._vectorization_pending = True
            return False

        file_path = str(self.state.input_path) if self.state.input_path else None
        settings_copy = copy.deepcopy(self.vector_settings)

        self._vectorization_thread = VectorizationThread(
            self.state.thresholded_array,
            settings_copy,
            file_path,
        )
        self._vectorization_thread.result_ready.connect(self._on_vectorization_finished)
        self._vectorization_thread.finished.connect(self._on_vectorization_thread_finished)
        self._vectorization_thread.start()
        return True

    def _on_vectorization_finished(self, result: object) -> None:
        if self._vectorization_pending or self._discard_vectorization_result:
            return
        from app.core.vectorization_engine import VectorResult
        if isinstance(result, VectorResult):
            self.state.vector_result = result
            if self.on_vectorization_done:
                self.on_vectorization_done(result)
        elif isinstance(result, str):
            self.state.vector_result = None
            if self.on_vectorization_error:
                self.on_vectorization_error(result)

    def _on_vectorization_thread_finished(self) -> None:
        self._vectorization_thread = None
        if self._discard_vectorization_result:
            self._discard_vectorization_result = False
            if not self._vectorization_pending:
                return
        if self._vectorization_pending:
            self._vectorization_pending = False
            self.run_vectorization()

    # ── Settings Mapping from UI ──────────────────────────────────────────────

    def sync_vtracer_settings_from_ui(
        self,
        detail_text: str,
        min_area_val: int,
        approx_slider_val: int,
        color_mode_text: str,
        color_count_val: int,
        preset_text: str,
        vt_color_text: str,
        vt_hierarchical_text: str,
        vt_mode_text: str,
    ) -> None:
        """Map all UI control values into `self.vector_settings`. Call before run_vectorization."""
        # Detail level → corner_threshold + max_iterations
        if detail_text == "Low":
            self.vector_settings.vtracer.corner_threshold = 80
            self.vector_settings.vtracer.max_iterations = 5
        elif detail_text == "Medium":
            self.vector_settings.vtracer.corner_threshold = 60
            self.vector_settings.vtracer.max_iterations = 12
        elif detail_text == "High":
            self.vector_settings.vtracer.corner_threshold = 25
            self.vector_settings.vtracer.max_iterations = 20

        # Min Area → filter_speckle
        self.vector_settings.vtracer.filter_speckle = max(1, min_area_val // 25)

        # Approx tolerance → length_threshold
        approx_val = approx_slider_val / 10.0
        self.vector_settings.vtracer.length_threshold = max(3.5, min(10.0, approx_val + 1.5))

        # Color precision
        if color_mode_text == "Custom colors":
            precision = max(1, min(8, int(math.ceil(math.log2(max(2, color_count_val))))))
            self.vector_settings.vtracer.color_precision = precision
        elif preset_text == "Photo":
            self.vector_settings.vtracer.color_precision = 8
        else:
            self.vector_settings.vtracer.color_precision = 6

        # Combo box values
        self.vector_settings.vtracer.colormode = "color" if vt_color_text == "Color" else "binary"
        self.vector_settings.vtracer.hierarchical = vt_hierarchical_text.lower()
        vt_mode_val = vt_mode_text.lower()
        if vt_mode_val == "pixel":
            vt_mode_val = "none"
        self.vector_settings.vtracer.mode = vt_mode_val

    # ── Export ───────────────────────────────────────────────────────────────

    def export_svg(self, file_path: str, source_name: Optional[str] = None):
        """Export the current vector result. Raises on failure."""
        if not self.state.vector_result:
            raise ValueError("No vector result available to export.")
        return self._export.export_svg_file(
            self.state.vector_result, file_path, source_name
        )

    def build_default_export_path(self, image_info) -> str:
        return self._export.build_default_export_path(image_info)

    # ── Batch Processing ──────────────────────────────────────────────────────

    def is_batch_running(self) -> bool:
        return bool(self._batch_thread and self._batch_thread.isRunning())

    def start_batch(
        self,
        valid_paths: list[str],
        output_dir: str,
        threshold_val: int,
        on_progress: Callable,
        on_done: Callable,
        on_finished: Callable,
    ) -> None:
        """Launch the batch processing thread."""
        self._batch_thread = BatchProcessingThread(
            valid_paths,
            output_dir,
            threshold_val,
            self.vector_settings,
        )
        self._batch_thread.progress.connect(on_progress)
        self._batch_thread.result_ready.connect(on_done)
        self._batch_thread.finished.connect(on_finished)
        self._batch_thread.start()

    def validate_batch_files(self, paths: list[str]):
        return self._validation.validate_batch_files(paths)
