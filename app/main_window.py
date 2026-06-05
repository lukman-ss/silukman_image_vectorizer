from __future__ import annotations

from typing import Optional, cast
import os
import copy

from PySide6.QtCore import Qt, QThread, Signal, QPoint, QSettings, QPointF
from PySide6.QtGui import QBrush, QPixmap, QImage, QPainter, QPen, QColor, QPainterPath, QPolygon
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QSizePolicy,
    QStatusBar,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QSlider,
    QComboBox,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsPixmapItem,
    QGroupBox,
    QTabWidget,
    QApplication,
)

from app.config.settings import DEFAULT_WINDOW_HEIGHT, DEFAULT_WINDOW_WIDTH, VectorizationSettings
from app.core.constants import (
    APPLICATION_TITLE,
    CONTROL_PANEL_TITLE,
    SIDEBAR_TITLE,
    STATUS_READY,
)
from app.core.vectorization_engine import VectorResult
from app.services.batch_processor import BatchFileValidation, validate_batch_files
from app.services.color_palette import ColorRGB, color_to_hex, extract_dominant_colors
from app.services.image_loader import ImageInfo, load_image

class SyncGraphicsView(QGraphicsView):
    """Custom graphics view that supports panning, zooming, and scroll/zoom synchronization."""
    zoomed = Signal(float)
    scrolled = Signal(int, int)
    image_clicked = Signal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene().addItem(self.pixmap_item)
        
        self.current_zoom = 1.0
        self._block_signals = False
        self.pick_color_enabled = False
        
        # Connect scrollbar value changes
        self.horizontalScrollBar().valueChanged.connect(self._on_scroll)
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def setImage(self, pixmap: QPixmap) -> None:
        self.pixmap_item.setPixmap(pixmap)
        self.scene().setSceneRect(self.pixmap_item.boundingRect())

    def setPickColorEnabled(self, enabled: bool) -> None:
        """Enable click-to-pick mode for image pixels."""
        self.pick_color_enabled = enabled
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        else:
            self.unsetCursor()
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def mousePressEvent(self, event) -> None:
        if self.pick_color_enabled and event.button() == Qt.MouseButton.LeftButton:
            position = event.position().toPoint() if hasattr(event, "position") else event.pos()
            scene_position = self.mapToScene(position)
            x = int(scene_position.x())
            y = int(scene_position.y())
            pixmap = self.pixmap_item.pixmap()
            if 0 <= x < pixmap.width() and 0 <= y < pixmap.height():
                self.image_clicked.emit(x, y)
                return
        super().mousePressEvent(event)

    def wheelEvent(self, event) -> None:
        zoom_factor = 1.15
        if event.angleDelta().y() < 0:
            zoom_factor = 1.0 / zoom_factor
            
        new_zoom = self.current_zoom * zoom_factor
        if 0.1 <= new_zoom <= 20.0:
            self.current_zoom = new_zoom
            self.zoomed.emit(self.current_zoom)
            self.applyZoom(self.current_zoom)

    def applyZoom(self, zoom_level: float) -> None:
        self.current_zoom = zoom_level
        self.resetTransform()
        self.scale(zoom_level, zoom_level)

    def _on_scroll(self) -> None:
        if not self._block_signals:
            self.scrolled.emit(
                self.horizontalScrollBar().value(),
                self.verticalScrollBar().value()
            )

    def syncScroll(self, h_val: int, v_val: int) -> None:
        self._block_signals = True
        self.horizontalScrollBar().setValue(h_val)
        self.verticalScrollBar().setValue(v_val)
        self._block_signals = False


class ImageProcessorThread(QThread):
    """Worker thread to run the image processing pipeline in the background."""
    result_ready = Signal(object)  # Emits (QImage, np.ndarray) on success, or str error message

    def __init__(self, file_path: str, threshold_val: int, parent=None) -> None:
        super().__init__(parent)
        self.file_path = file_path
        self.threshold_val = threshold_val

    def run(self) -> None:
        try:
            from app.core.image_pipeline import process_image_pipeline
            result_img, thresholded = process_image_pipeline(self.file_path, self.threshold_val)
            self.result_ready.emit((result_img, thresholded))
        except Exception as error:
            self.result_ready.emit(str(error))


class VectorizationThread(QThread):
    """Worker thread to run the vectorization engine in the background."""
    result_ready = Signal(object)  # Emits VectorResult or str error message

    def __init__(self, thresholded_array, settings, file_path: str | None, parent=None) -> None:
        super().__init__(parent)
        self.thresholded_array = thresholded_array.copy()
        self.settings = copy.deepcopy(settings)
        self.file_path = file_path

    def run(self) -> None:
        try:
            from app.core.vectorizer_backend import OpenCVVectorizerBackend, VTracerVectorizerBackend

            if self.settings.engine_type == "VTracer":
                try:
                    backend = VTracerVectorizerBackend()
                    vector_result = backend.vectorize(self.file_path, self.settings)
                except Exception as e:
                    fallback_settings = copy.deepcopy(self.settings)
                    fallback_settings.engine_type = "OpenCV Legacy"
                    backend = OpenCVVectorizerBackend()
                    vector_result = backend.vectorize(self.file_path, fallback_settings, self.thresholded_array)
                    vector_result.fallback_error = str(e)
            else:
                backend = OpenCVVectorizerBackend()
                vector_result = backend.vectorize(self.file_path, self.settings, self.thresholded_array)

            self.result_ready.emit(vector_result)
        except Exception as error:
            self.result_ready.emit(str(error))


class BatchProcessingThread(QThread):
    """Worker thread for batch processing and SVG export."""

    progress = Signal(int, int, str, bool)
    result_ready = Signal(object)  # Emits (success_count, failed_count) or str error message

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


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.original_pixmap = QPixmap()
        self.processed_pixmap = QPixmap()
        self.current_image_info: Optional[ImageInfo] = None
        self.processor_thread: Optional[ImageProcessorThread] = None
        self.vectorization_thread: Optional[VectorizationThread] = None
        self.batch_thread: Optional[BatchProcessingThread] = None
        self._processing_pending = False
        self._vectorization_pending = False
        self._discard_vectorization_result = False
        self.vector_settings = VectorizationSettings()
        from app.core.vectorizer_backend import VTRACER_AVAILABLE
        if VTRACER_AVAILABLE:
            self.vector_settings.engine_type = "VTracer"
        else:
            self.vector_settings.engine_type = "OpenCV Legacy"
        self.vector_result: Optional[VectorResult] = None
        self.thresholded_array = None
        self.batch_files: list[BatchFileValidation] = []
        self.palette_colors: list[ColorRGB] = []
        self.palette_replacements: dict[ColorRGB, ColorRGB] = {}
        self.palette_buttons: list[QPushButton] = []
        self.is_palette_pick_mode = False
        self._updating_from_preset = False
        self.settings = QSettings("MyCompany", "ImageVectorizer")
        self.setWindowTitle(APPLICATION_TITLE)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setCentralWidget(self._create_main_layout())
        self.setStatusBar(self._create_status_bar())

        from app.ui.theme import normalize_theme_mode

        saved_theme = normalize_theme_mode(str(self.settings.value("theme", "System")))
        self.theme_combo.setCurrentText(saved_theme)
        self._apply_theme(saved_theme)

    def _create_main_layout(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        panels = QWidget()
        panels_layout = self._create_panels_layout()
        panels.setLayout(panels_layout)

        layout.addWidget(panels)
        return container

    def _create_panels_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        sidebar = self._create_panel(SIDEBAR_TITLE, 180)
        controls = self._create_panel(CONTROL_PANEL_TITLE, 240)

        # Add Import Image button to sidebar
        import_button = QPushButton("Import Image")
        import_button.clicked.connect(self._import_image)
        cast(QVBoxLayout, sidebar.layout()).addWidget(import_button)

        # Add Export SVG button to sidebar
        self.export_button = QPushButton("Export SVG")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self._export_svg)
        cast(QVBoxLayout, sidebar.layout()).addWidget(self.export_button)

        batch_title = QLabel("<b>Batch Processing</b>")
        cast(QVBoxLayout, sidebar.layout()).addWidget(batch_title)

        batch_select_button = QPushButton("Select Batch Images")
        batch_select_button.clicked.connect(self._select_batch_images)
        cast(QVBoxLayout, sidebar.layout()).addWidget(batch_select_button)

        self.batch_file_list = QListWidget()
        self.batch_file_list.setMinimumHeight(140)
        cast(QVBoxLayout, sidebar.layout()).addWidget(self.batch_file_list, 1)

        # Add Process Batch button to sidebar
        self.process_batch_button = QPushButton("Process Batch")
        self.process_batch_button.setEnabled(False)
        self.process_batch_button.clicked.connect(self._process_batch)
        cast(QVBoxLayout, sidebar.layout()).addWidget(self.process_batch_button)

        # Metadata labels in controls panel
        self.meta_labels: dict[str, QLabel] = {}
        for field in ("File", "Size", "Resolution", "Format", "Color Mode"):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(4, 2, 4, 2)
            row_layout.setSpacing(4)
            key_label = QLabel(f"<b>{field}:</b>")
            key_label.setFixedWidth(84)
            val_label = QLabel("—")
            val_label.setWordWrap(True)
            row_layout.addWidget(key_label)
            row_layout.addWidget(val_label, 1)
            cast(QVBoxLayout, controls.layout()).addWidget(row)
            self.meta_labels[field] = val_label

        self.palette_group = QGroupBox("Input Color Palette")
        palette_layout = QVBoxLayout(self.palette_group)
        palette_layout.setContentsMargins(6, 12, 6, 6)
        palette_layout.setSpacing(6)

        self.palette_hint_label = QLabel("Import an image to detect up to 10 colors.")
        self.palette_hint_label.setWordWrap(True)
        palette_layout.addWidget(self.palette_hint_label)

        self.palette_grid_widget = QWidget()
        self.palette_grid = QGridLayout(self.palette_grid_widget)
        self.palette_grid.setContentsMargins(0, 0, 0, 0)
        self.palette_grid.setSpacing(6)
        palette_layout.addWidget(self.palette_grid_widget)

        self.pick_palette_button = QPushButton("Pick Color From Image")
        self.pick_palette_button.setCheckable(True)
        self.pick_palette_button.clicked.connect(self._toggle_palette_pick_mode)
        palette_layout.addWidget(self.pick_palette_button)

        reset_palette_button = QPushButton("Reset Palette Changes")
        reset_palette_button.clicked.connect(self._reset_palette_replacements)
        palette_layout.addWidget(reset_palette_button)

        cast(QVBoxLayout, controls.layout()).addWidget(self.palette_group)

        # Preset selection
        preset_group = QWidget()
        preset_layout = QVBoxLayout(preset_group)
        preset_layout.setContentsMargins(4, 12, 4, 4)
        preset_layout.setSpacing(6)
        
        preset_title = QLabel("<b>Quality Preset:</b>")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Logo", "Artwork", "Icon", "Photo", "Custom"])
        self.preset_combo.setCurrentText("Logo") # default
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        
        preset_layout.addWidget(preset_title)
        preset_layout.addWidget(self.preset_combo)
        cast(QVBoxLayout, controls.layout()).addWidget(preset_group)

        # Engine Selection
        engine_group = QWidget()
        engine_layout = QVBoxLayout(engine_group)
        engine_layout.setContentsMargins(4, 12, 4, 4)
        engine_layout.setSpacing(6)

        engine_title = QLabel("<b>Vectorizer Engine:</b>")
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["VTracer", "OpenCV Legacy"])
        self.engine_combo.currentTextChanged.connect(self._on_engine_changed)

        from app.core.vectorizer_backend import VTRACER_AVAILABLE
        if not VTRACER_AVAILABLE:
            self.engine_combo.setEnabled(False)
            self.engine_combo.setCurrentText("OpenCV Legacy")
            self.vector_settings.engine_type = "OpenCV Legacy"
        else:
            self.engine_combo.setCurrentText(self.vector_settings.engine_type)

        engine_layout.addWidget(engine_title)
        engine_layout.addWidget(self.engine_combo)
        cast(QVBoxLayout, controls.layout()).addWidget(engine_group)

        # Hand-pick Settings Group
        self.handpick_group = QGroupBox("Hand-pick Settings")
        handpick_layout = QVBoxLayout(self.handpick_group)
        handpick_layout.setContentsMargins(6, 12, 6, 6)
        handpick_layout.setSpacing(8)

        # Threshold slider control in Hand-pick Settings
        self.threshold_group = QWidget()
        thresh_layout = QVBoxLayout(self.threshold_group)
        thresh_layout.setContentsMargins(0, 0, 0, 0)
        thresh_layout.setSpacing(4)

        thresh_title = QLabel("<b>Threshold Value:</b>")
        slider_layout = QHBoxLayout()
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 255)
        self.threshold_slider.setValue(127)
        self.threshold_slider.valueChanged.connect(self._on_threshold_changed)

        self.threshold_value_label = QLabel("127")
        self.threshold_value_label.setFixedWidth(30)
        self.threshold_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        slider_layout.addWidget(self.threshold_slider)
        slider_layout.addWidget(self.threshold_value_label)
        thresh_layout.addWidget(thresh_title)
        thresh_layout.addLayout(slider_layout)
        handpick_layout.addWidget(self.threshold_group)

        # Detail Level Combobox in Hand-pick Settings
        detail_title = QLabel("<b>Detail Level:</b>")
        self.detail_combo = QComboBox()
        self.detail_combo.addItems(["Low", "Medium", "High", "Custom"])
        self.detail_combo.setCurrentText("Medium")
        self.detail_combo.currentTextChanged.connect(self._on_detail_level_changed)
        handpick_layout.addWidget(detail_title)
        handpick_layout.addWidget(self.detail_combo)

        # Min Area Slider in Hand-pick Settings
        min_area_title = QLabel("<b>Min Area (px):</b>")
        min_area_slider_layout = QHBoxLayout()
        self.min_area_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_area_slider.setRange(0, 1000)
        self.min_area_slider.setValue(100)
        self.min_area_slider.valueChanged.connect(self._on_min_area_changed)

        self.min_area_value_label = QLabel("100")
        self.min_area_value_label.setFixedWidth(30)
        self.min_area_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        min_area_slider_layout.addWidget(self.min_area_slider)
        min_area_slider_layout.addWidget(self.min_area_value_label)
        handpick_layout.addWidget(min_area_title)
        handpick_layout.addLayout(min_area_slider_layout)

        # Approx Tolerance Slider in Hand-pick Settings
        approx_title = QLabel("<b>Approx Tolerance:</b>")
        approx_slider_layout = QHBoxLayout()
        self.approx_slider = QSlider(Qt.Orientation.Horizontal)
        self.approx_slider.setRange(0, 100)  # Represents 0.0 to 10.0
        self.approx_slider.setValue(20)    # Represents 2.0
        self.approx_slider.valueChanged.connect(self._on_approx_tolerance_changed)

        self.approx_value_label = QLabel("2.0")
        self.approx_value_label.setFixedWidth(30)
        self.approx_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        approx_slider_layout.addWidget(self.approx_slider)
        approx_slider_layout.addWidget(self.approx_value_label)
        handpick_layout.addWidget(approx_title)
        handpick_layout.addLayout(approx_slider_layout)

        # Checkboxes in Hand-pick Settings
        self.smoothing_checkbox = QCheckBox("Smooth contours")
        self.smoothing_checkbox.toggled.connect(self._on_smoothing_changed)
        handpick_layout.addWidget(self.smoothing_checkbox)

        self.invert_checkbox = QCheckBox("Invert detection")
        self.invert_checkbox.toggled.connect(self._on_invert_changed)
        handpick_layout.addWidget(self.invert_checkbox)

        self.preserve_edges_checkbox = QCheckBox("Preserve artwork edges")
        self.preserve_edges_checkbox.toggled.connect(self._on_preserve_edges_changed)
        handpick_layout.addWidget(self.preserve_edges_checkbox)

        self.remove_bg_checkbox = QCheckBox("Remove background")
        self.remove_bg_checkbox.toggled.connect(self._on_remove_bg_changed)
        handpick_layout.addWidget(self.remove_bg_checkbox)

        # Background tolerance widget in Hand-pick Settings
        self.bg_tolerance_widget = QWidget()
        bg_tol_layout = QVBoxLayout(self.bg_tolerance_widget)
        bg_tol_layout.setContentsMargins(0, 0, 0, 0)
        bg_tol_layout.setSpacing(4)
        
        bg_tol_title = QLabel("<b>BG Tolerance:</b>")
        bg_tol_slider_layout = QHBoxLayout()
        self.bg_tolerance_slider = QSlider(Qt.Orientation.Horizontal)
        self.bg_tolerance_slider.setRange(1, 100)
        self.bg_tolerance_slider.setValue(20)
        self.bg_tolerance_slider.valueChanged.connect(self._on_bg_tolerance_changed)
        
        self.bg_tolerance_value_label = QLabel("20")
        self.bg_tolerance_value_label.setFixedWidth(30)
        self.bg_tolerance_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        bg_tol_slider_layout.addWidget(self.bg_tolerance_slider)
        bg_tol_slider_layout.addWidget(self.bg_tolerance_value_label)
        bg_tol_layout.addWidget(bg_tol_title)
        bg_tol_layout.addLayout(bg_tol_slider_layout)
        
        handpick_layout.addWidget(self.bg_tolerance_widget)
        self.bg_tolerance_widget.setVisible(False)

        # Color Mode in Hand-pick Settings
        color_mode_title = QLabel("<b>Color Mode:</b>")
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(["Unlimited colors", "Custom colors"])
        self.color_mode_combo.currentTextChanged.connect(self._on_color_mode_changed)
        handpick_layout.addWidget(color_mode_title)
        handpick_layout.addWidget(self.color_mode_combo)

        # Custom Color Count Slider in Hand-pick Settings
        self.color_count_widget = QWidget()
        color_count_layout = QVBoxLayout(self.color_count_widget)
        color_count_layout.setContentsMargins(0, 4, 0, 0)
        color_count_layout.setSpacing(4)
        
        color_count_title = QLabel("<b>Max Colors:</b>")
        color_count_slider_layout = QHBoxLayout()
        self.color_count_slider = QSlider(Qt.Orientation.Horizontal)
        self.color_count_slider.setRange(2, 64)
        self.color_count_slider.setValue(8)
        self.color_count_slider.valueChanged.connect(self._on_color_count_changed)
        
        self.color_count_value_label = QLabel("8")
        self.color_count_value_label.setFixedWidth(30)
        self.color_count_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        color_count_slider_layout.addWidget(self.color_count_slider)
        color_count_slider_layout.addWidget(self.color_count_value_label)
        color_count_layout.addWidget(color_count_title)
        color_count_layout.addLayout(color_count_slider_layout)
        
        handpick_layout.addWidget(self.color_count_widget)
        self.color_count_widget.setVisible(False)

        # VTracer-specific parameters group
        self.vtracer_params_widget = QWidget()
        vtracer_params_layout = QVBoxLayout(self.vtracer_params_widget)
        vtracer_params_layout.setContentsMargins(0, 0, 0, 0)
        vtracer_params_layout.setSpacing(6)

        vtracer_color_mode_title = QLabel("<b>VTracer Color:</b>")
        self.vtracer_color_mode_combo = QComboBox()
        self.vtracer_color_mode_combo.addItems(["Color", "Black & White"])
        self.vtracer_color_mode_combo.currentTextChanged.connect(self._on_vtracer_color_mode_changed)
        vtracer_params_layout.addWidget(vtracer_color_mode_title)
        vtracer_params_layout.addWidget(self.vtracer_color_mode_combo)

        vtracer_hierarchical_title = QLabel("<b>VTracer Layers:</b>")
        self.vtracer_hierarchical_combo = QComboBox()
        self.vtracer_hierarchical_combo.addItems(["Stacked", "Cutout"])
        self.vtracer_hierarchical_combo.currentTextChanged.connect(self._on_vtracer_hierarchical_changed)
        vtracer_params_layout.addWidget(vtracer_hierarchical_title)
        vtracer_params_layout.addWidget(self.vtracer_hierarchical_combo)

        vtracer_mode_title = QLabel("<b>VTracer Mode:</b>")
        self.vtracer_mode_combo = QComboBox()
        self.vtracer_mode_combo.addItems(["Spline", "Polygon", "Pixel"])
        self.vtracer_mode_combo.currentTextChanged.connect(self._on_vtracer_mode_changed)
        vtracer_params_layout.addWidget(vtracer_mode_title)
        vtracer_params_layout.addWidget(self.vtracer_mode_combo)

        handpick_layout.addWidget(self.vtracer_params_widget)

        # Adjust initial visibility based on active engine
        is_vtracer = (self.vector_settings.engine_type == "VTracer")
        self.threshold_group.setVisible(not is_vtracer)
        self.smoothing_checkbox.setVisible(not is_vtracer)
        self.invert_checkbox.setVisible(not is_vtracer)
        self.preserve_edges_checkbox.setVisible(not is_vtracer)
        self.vtracer_params_widget.setVisible(is_vtracer)

        # Overlay paths checkbox in Hand-pick Settings
        self.overlay_checkbox = QCheckBox("Overlay paths on original")
        self.overlay_checkbox.toggled.connect(self._on_overlay_changed)
        handpick_layout.addWidget(self.overlay_checkbox)

        # Add Hand-pick Settings Group to controls layout
        cast(QVBoxLayout, controls.layout()).addWidget(self.handpick_group)

        # Reset & Re-vectorize buttons
        buttons_group = QWidget()
        buttons_layout = QHBoxLayout(buttons_group)
        buttons_layout.setContentsMargins(4, 4, 4, 4)
        buttons_layout.setSpacing(8)

        reset_button = QPushButton("Reset Settings")
        reset_button.clicked.connect(self._reset_settings)
        
        revectorize_button = QPushButton("Re-vectorize")
        revectorize_button.clicked.connect(self._run_vectorization)
        
        buttons_layout.addWidget(reset_button)
        buttons_layout.addWidget(revectorize_button)
        cast(QVBoxLayout, controls.layout()).addWidget(buttons_group)

        # Theme Settings UI Controls
        theme_group = QWidget()
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setContentsMargins(4, 12, 4, 4)
        theme_layout.setSpacing(6)

        theme_title = QLabel("<b>Application Theme:</b>")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        
        theme_layout.addWidget(theme_title)
        theme_layout.addWidget(self.theme_combo)
        cast(QVBoxLayout, controls.layout()).addWidget(theme_group)

        cast(QVBoxLayout, controls.layout()).addStretch(1)

        # Preview area: original image | processing result (split horizontally)
        preview_area = QWidget()
        preview_vbox = QVBoxLayout(preview_area)
        preview_vbox.setContentsMargins(0, 0, 0, 0)
        preview_vbox.setSpacing(6)

        # Preview toolbar
        preview_toolbar = QWidget()
        toolbar_layout = QHBoxLayout(preview_toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(8)

        fit_button = QPushButton("Fit to Screen")
        fit_button.clicked.connect(self._fit_to_screen)
        
        actual_size_button = QPushButton("Actual Size")
        actual_size_button.clicked.connect(self._actual_size)
        
        self.zoom_label = QLabel("Zoom: 100%")
        self.zoom_label.setFixedWidth(80)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        toolbar_layout.addWidget(fit_button)
        toolbar_layout.addWidget(actual_size_button)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.zoom_label)
        
        preview_vbox.addWidget(preview_toolbar)

        # Horizontal layout for side-by-side previews
        preview_hbox = QHBoxLayout()
        preview_hbox.setContentsMargins(0, 0, 0, 0)
        preview_hbox.setSpacing(8)

        original_panel = self._create_panel("Original Image")
        self.original_view = SyncGraphicsView()
        self.original_view.image_clicked.connect(self._on_original_image_clicked)
        cast(QVBoxLayout, original_panel.layout()).addWidget(self.original_view, 1)

        # Tab widget for vectorized result vs thresholded raster
        self.result_tabs = QTabWidget()
        
        # Tab 1: Vectorized Result
        vector_panel = self._create_panel("Vectorized Result")
        self.result_view = SyncGraphicsView()
        cast(QVBoxLayout, vector_panel.layout()).addWidget(self.result_view, 1)
        self.result_tabs.addTab(vector_panel, "Vectorized Result")
        
        # Tab 2: Thresholded Raster
        raster_panel = self._create_panel("Thresholded Raster")
        self.raster_view = SyncGraphicsView()
        cast(QVBoxLayout, raster_panel.layout()).addWidget(self.raster_view, 1)
        self.result_tabs.addTab(raster_panel, "Thresholded Raster")

        preview_hbox.addWidget(original_panel, 1)
        preview_hbox.addWidget(self.result_tabs, 1)
        preview_vbox.addLayout(preview_hbox, 1)

        # Synchronize zoom
        self.original_view.zoomed.connect(self.result_view.applyZoom)
        self.original_view.zoomed.connect(self.raster_view.applyZoom)
        self.original_view.zoomed.connect(self._update_zoom_label)
        
        self.result_view.zoomed.connect(self.original_view.applyZoom)
        self.result_view.zoomed.connect(self.raster_view.applyZoom)
        self.result_view.zoomed.connect(self._update_zoom_label)
        
        self.raster_view.zoomed.connect(self.original_view.applyZoom)
        self.raster_view.zoomed.connect(self.result_view.applyZoom)
        self.raster_view.zoomed.connect(self._update_zoom_label)
        
        # Synchronize pan
        self.original_view.scrolled.connect(self.result_view.syncScroll)
        self.original_view.scrolled.connect(self.raster_view.syncScroll)
        
        self.result_view.scrolled.connect(self.original_view.syncScroll)
        self.result_view.scrolled.connect(self.raster_view.syncScroll)
        
        self.raster_view.scrolled.connect(self.original_view.syncScroll)
        self.raster_view.scrolled.connect(self.result_view.syncScroll)

        layout.addWidget(sidebar)
        layout.addWidget(preview_area, 1)
        layout.addWidget(controls)
        return layout

    def _create_panel(self, title: str, fixed_width: Optional[int] = None) -> QWidget:
        panel = QWidget()
        panel.setObjectName("panel")
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        if fixed_width is not None:
            panel.setFixedWidth(fixed_width)

        layout = QVBoxLayout(panel)
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(label)
        # Ensure layout can hold additional widgets like buttons
        panel.setLayout(layout)
        return panel

    def _create_status_bar(self) -> QStatusBar:
        status_bar = QStatusBar()
        status_bar.showMessage(STATUS_READY)
        return status_bar

    def _import_image(self) -> None:
        """Open file dialog and load image using image_loader service."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not file_path:
            return

        pixmap, info, error = load_image(file_path)

        if error:
            QMessageBox.critical(self, "Invalid Image", error)
            return

        if pixmap is None or info is None:
            return

        self.original_pixmap = pixmap
        self.current_image_info = info
        self._clear_processing_result()
        self._update_preview_image()
        self._fit_to_screen()
        self._update_metadata_display(info)
        self._load_input_palette(info.file_path)
        self._start_processing()
        self.statusBar().showMessage(f"Image loaded: {info.file_name}")

    def _load_input_palette(self, file_path: str) -> None:
        """Extract and display dominant colors from the imported image."""
        self.is_palette_pick_mode = False
        self.original_view.setPickColorEnabled(False)
        self.pick_palette_button.setChecked(False)
        self.pick_palette_button.setText("Pick Color From Image")
        self.palette_replacements.clear()
        self.vector_settings.palette_replacements = []
        try:
            self.palette_colors = extract_dominant_colors(file_path, max_colors=10)
            self.palette_hint_label.setText("Click a color to replace it in the vector output.")
        except Exception as error:
            self.palette_colors = []
            self.palette_hint_label.setText(f"Palette unavailable: {error}")
        self._update_palette_display()

    def _update_palette_display(self) -> None:
        """Refresh the color palette swatches."""
        while self.palette_grid.count():
            item = self.palette_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.palette_buttons = []
        if not self.palette_colors:
            return

        for index, source_color in enumerate(self.palette_colors):
            button = QPushButton()
            replacement_color = self.palette_replacements.get(source_color, source_color)
            source_hex = color_to_hex(source_color)
            replacement_hex = color_to_hex(replacement_color)
            button.setFixedSize(32, 32)
            button.setText("✓" if source_color in self.palette_replacements else "")
            button.setToolTip(
                f"{source_hex} → {replacement_hex}" if source_color in self.palette_replacements else source_hex
            )
            button.setStyleSheet(
                "QPushButton {"
                f"background-color: {replacement_hex};"
                "border: 2px solid #4b5563;"
                "border-radius: 6px;"
                "color: white;"
                "font-weight: bold;"
                "}"
            )
            button.clicked.connect(lambda checked=False, color=source_color: self._choose_palette_replacement(color))
            row = index // 5
            column = index % 5
            self.palette_grid.addWidget(button, row, column)
            self.palette_buttons.append(button)

    def _choose_palette_replacement(self, source_color: ColorRGB) -> None:
        """Open a color picker and replace the selected source color."""
        current_color = self.palette_replacements.get(source_color, source_color)
        selected = QColorDialog.getColor(
            QColor(*current_color),
            self,
            f"Replace {color_to_hex(source_color)}",
        )
        if not selected.isValid():
            return

        replacement = (selected.red(), selected.green(), selected.blue())
        if replacement == source_color:
            self.palette_replacements.pop(source_color, None)
        else:
            self.palette_replacements[source_color] = replacement

        self.vector_settings.palette_replacements = list(self.palette_replacements.items())
        self._update_palette_display()
        self.statusBar().showMessage(
            f"Palette color updated: {color_to_hex(source_color)} → {color_to_hex(replacement)}"
        )
        self._run_vectorization()

    def _toggle_palette_pick_mode(self, checked: bool) -> None:
        """Enable or disable picking a source color from the original preview."""
        if checked and self.original_pixmap.isNull():
            self.pick_palette_button.setChecked(False)
            QMessageBox.information(self, "Pick Color", "Import an image before picking a color.")
            return

        self.is_palette_pick_mode = checked
        self.original_view.setPickColorEnabled(checked)
        if checked:
            self.pick_palette_button.setText("Click Original Image...")
            self.statusBar().showMessage("Click a color in the original image to replace it.")
        else:
            self.pick_palette_button.setText("Pick Color From Image")
            self.statusBar().showMessage("Color picking cancelled.")

    def _on_original_image_clicked(self, x: int, y: int) -> None:
        """Use the clicked original-image pixel as the source color."""
        if not self.is_palette_pick_mode or self.original_pixmap.isNull():
            return

        self.pick_palette_button.setChecked(False)
        self.is_palette_pick_mode = False
        self.original_view.setPickColorEnabled(False)
        self.pick_palette_button.setText("Pick Color From Image")

        image = self.original_pixmap.toImage()
        if not (0 <= x < image.width() and 0 <= y < image.height()):
            return

        color = image.pixelColor(x, y)
        source_color: ColorRGB = (color.red(), color.green(), color.blue())
        self._add_picked_palette_color(source_color)
        self.statusBar().showMessage(f"Picked source color {color_to_hex(source_color)}.")
        self._choose_palette_replacement(source_color)

    def _add_picked_palette_color(self, source_color: ColorRGB) -> None:
        """Insert a picked source color into the visible palette."""
        if source_color in self.palette_colors:
            self.palette_colors.remove(source_color)
        self.palette_colors.insert(0, source_color)
        self.palette_colors = self.palette_colors[:10]
        self._update_palette_display()

    def _reset_palette_replacements(self) -> None:
        """Clear all palette color replacements."""
        if not self.palette_replacements:
            return
        self.palette_replacements.clear()
        self.vector_settings.palette_replacements = []
        self._update_palette_display()
        self.statusBar().showMessage("Palette color changes reset.")
        self._run_vectorization()

    def _on_theme_changed(self, theme_name: str) -> None:
        """Handle theme change from combobox."""
        from app.ui.theme import normalize_theme_mode

        theme_name = normalize_theme_mode(theme_name)
        self.settings.setValue("theme", theme_name)
        self._apply_theme(theme_name)

    def _apply_theme(self, theme_name: str) -> None:
        """Apply style sheet globally based on selected theme mode."""
        if hasattr(self, "_is_applying_theme") and self._is_applying_theme:
            return

        self._is_applying_theme = True
        try:
            from app.ui.theme import get_stylesheet, is_system_dark_mode, normalize_theme_mode
            
            theme_name = normalize_theme_mode(theme_name)
            is_dark = False
            if theme_name == "System":
                is_dark = is_system_dark_mode()
            elif theme_name == "Dark":
                is_dark = True
            else:
                is_dark = False

            stylesheet = get_stylesheet(is_dark)
            application = QApplication.instance()
            if isinstance(application, QApplication):
                application.setStyleSheet(stylesheet)
            else:
                self.setStyleSheet(stylesheet)
        finally:
            self._is_applying_theme = False

    def changeEvent(self, event) -> None:
        """Apply theme again if system palette changes while in 'System' mode."""
        from PySide6.QtCore import QEvent
        if event.type() == QEvent.Type.PaletteChange:
            if hasattr(self, "_is_applying_theme") and self._is_applying_theme:
                super().changeEvent(event)
                return

            if hasattr(self, "theme_combo"):
                current_theme = self.theme_combo.currentText()
                if current_theme == "System":
                    self._apply_theme("System")
        super().changeEvent(event)

    def _set_preset_custom(self) -> None:
        """Switch preset combo to 'Custom' if not updating from preset programmatically."""
        if not getattr(self, "_updating_from_preset", False):
            if hasattr(self, "preset_combo"):
                self.preset_combo.blockSignals(True)
                self.preset_combo.setCurrentText("Custom")
                self.preset_combo.blockSignals(False)

    def _on_preset_changed(self, preset_name: str) -> None:
        """Handle preset quality selection changes."""
        if preset_name == "Custom":
            return

        self._updating_from_preset = True
        try:
            if preset_name == "Logo":
                threshold = 127
                min_area = 100
                detail_level = "Low"
                smoothing = False
                preserve_edges = False
                remove_background = False
                color_mode = "Custom colors"
                color_count = 6
                bg_tolerance = 20
                vt_colormode = "Color"
                vt_hierarchical = "Stacked"
                vt_mode = "Spline"
                vt_layer_difference = 32
                vt_color_precision = 6
            elif preset_name == "Artwork":
                threshold = 127
                min_area = 20
                detail_level = "High"
                smoothing = True
                preserve_edges = True
                remove_background = False
                color_mode = "Custom colors"
                color_count = 24
                bg_tolerance = 20
                vt_colormode = "Color"
                vt_hierarchical = "Stacked"
                vt_mode = "Spline"
                vt_layer_difference = 16
                vt_color_precision = 6
            elif preset_name == "Icon":
                threshold = 127
                min_area = 5
                detail_level = "High"
                smoothing = False
                preserve_edges = False
                remove_background = True
                color_mode = "Custom colors"
                color_count = 12
                bg_tolerance = 15
                vt_colormode = "Color"
                vt_hierarchical = "Cutout"
                vt_mode = "Spline"
                vt_layer_difference = 16
                vt_color_precision = 5
            elif preset_name == "Photo":
                threshold = 127
                min_area = 10
                detail_level = "Medium"
                smoothing = False
                preserve_edges = False
                remove_background = False
                color_mode = "Unlimited colors"
                color_count = 64
                bg_tolerance = 20
                vt_colormode = "Color"
                vt_hierarchical = "Stacked"
                vt_mode = "Spline"
                vt_layer_difference = 8
                vt_color_precision = 8
                
                # Warn user about complexity
                QMessageBox.information(
                    self,
                    "Preset Warning",
                    "The Photo preset uses higher color tolerance and curve fitting, which may produce a highly complex SVG with a large file size."
                )
            else:
                return

            # Apply settings to internal vector_settings object manually
            self.vector_settings.threshold_val = threshold
            self.vector_settings.min_area = float(min_area)
            self.vector_settings.smoothing_enabled = smoothing
            self.vector_settings.preserve_edges = preserve_edges
            self.vector_settings.remove_background = remove_background
            self.vector_settings.color_mode = color_mode
            self.vector_settings.color_count = color_count
            self.vector_settings.bg_tolerance = float(bg_tolerance)
            self.vector_settings.vtracer.colormode = "color" if vt_colormode == "Color" else "binary"
            self.vector_settings.vtracer.hierarchical = vt_hierarchical.lower()
            vt_mode_val = vt_mode.lower()
            if vt_mode_val == "pixel":
                vt_mode_val = "none"
            self.vector_settings.vtracer.mode = vt_mode_val
            self.vector_settings.vtracer.layer_difference = vt_layer_difference
            self.vector_settings.vtracer.color_precision = vt_color_precision

            # Update UI controls safely with signals blocked to avoid redundant threads
            self.threshold_slider.blockSignals(True)
            self.threshold_slider.setValue(threshold)
            self.threshold_value_label.setText(str(threshold))
            self.threshold_slider.blockSignals(False)

            self.min_area_slider.blockSignals(True)
            self.min_area_slider.setValue(min_area)
            self.min_area_value_label.setText(str(min_area))
            self.min_area_slider.blockSignals(False)

            self.detail_combo.blockSignals(True)
            self.detail_combo.setCurrentText(detail_level)
            self.detail_combo.blockSignals(False)

            self.smoothing_checkbox.blockSignals(True)
            self.smoothing_checkbox.setChecked(smoothing)
            self.smoothing_checkbox.blockSignals(False)

            self.preserve_edges_checkbox.blockSignals(True)
            self.preserve_edges_checkbox.setChecked(preserve_edges)
            self.preserve_edges_checkbox.blockSignals(False)

            self.remove_bg_checkbox.blockSignals(True)
            self.remove_bg_checkbox.setChecked(remove_background)
            self.remove_bg_checkbox.blockSignals(False)
            self.bg_tolerance_widget.setVisible(remove_background)

            self.color_mode_combo.blockSignals(True)
            self.color_mode_combo.setCurrentText(color_mode)
            self.color_mode_combo.blockSignals(False)
            self.color_count_widget.setVisible(color_mode == "Custom colors")

            self.color_count_slider.blockSignals(True)
            self.color_count_slider.setValue(color_count)
            self.color_count_value_label.setText(str(color_count))
            self.color_count_slider.blockSignals(False)

            self.bg_tolerance_slider.blockSignals(True)
            self.bg_tolerance_slider.setValue(bg_tolerance)
            self.bg_tolerance_value_label.setText(str(bg_tolerance))
            self.bg_tolerance_slider.blockSignals(False)

            self.vtracer_color_mode_combo.blockSignals(True)
            self.vtracer_color_mode_combo.setCurrentText(vt_colormode)
            self.vtracer_color_mode_combo.blockSignals(False)

            self.vtracer_hierarchical_combo.blockSignals(True)
            self.vtracer_hierarchical_combo.setCurrentText(vt_hierarchical)
            self.vtracer_hierarchical_combo.blockSignals(False)

            self.vtracer_mode_combo.blockSignals(True)
            self.vtracer_mode_combo.setCurrentText(vt_mode)
            self.vtracer_mode_combo.blockSignals(False)
            
        finally:
            self._updating_from_preset = False

        self._start_processing()

    def _on_engine_changed(self, text: str) -> None:
        """Handle engine selection changes."""
        self.vector_settings.engine_type = text
        is_vtracer = (text == "VTracer")
        self.threshold_group.setVisible(not is_vtracer)
        self.smoothing_checkbox.setVisible(not is_vtracer)
        self.invert_checkbox.setVisible(not is_vtracer)
        self.preserve_edges_checkbox.setVisible(not is_vtracer)
        self.vtracer_params_widget.setVisible(is_vtracer)
        self._run_vectorization()

    def _on_vtracer_color_mode_changed(self, text: str) -> None:
        """Handle VTracer color mode changes."""
        if text == "Color":
            self.vector_settings.vtracer.colormode = "color"
        else:
            self.vector_settings.vtracer.colormode = "binary"
        self._set_preset_custom()
        self._run_vectorization()

    def _on_vtracer_hierarchical_changed(self, text: str) -> None:
        """Handle VTracer hierarchical layers mode changes."""
        self.vector_settings.vtracer.hierarchical = text.lower()
        self._set_preset_custom()
        self._run_vectorization()

    def _on_vtracer_mode_changed(self, text: str) -> None:
        """Handle VTracer curve fitting mode changes."""
        mode_val = text.lower()
        if mode_val == "pixel":
            mode_val = "none"
        self.vector_settings.vtracer.mode = mode_val
        self._set_preset_custom()
        self._run_vectorization()

    def _reset_settings(self) -> None:
        """Reset all settings to default values (Logo preset)."""
        self.preset_combo.setCurrentText("Logo")
        self.invert_checkbox.setChecked(False)
        self.overlay_checkbox.setChecked(False)
        self.vtracer_color_mode_combo.setCurrentText("Color")
        self.vtracer_hierarchical_combo.setCurrentText("Stacked")
        self.vtracer_mode_combo.setCurrentText("Spline")

    def _on_threshold_changed(self, value: int) -> None:
        """Handle threshold slider value changes."""
        self.threshold_value_label.setText(str(value))
        self.vector_settings.threshold_val = value
        self._set_preset_custom()
        self._start_processing()

    def _on_min_area_changed(self, value: int) -> None:
        """Handle min area slider changes."""
        self.min_area_value_label.setText(str(value))
        self.vector_settings.min_area = float(value)
        self._set_preset_custom()
        self._run_vectorization()

    def _on_approx_tolerance_changed(self, value: int) -> None:
        """Handle approx tolerance slider changes."""
        tolerance = value / 10.0
        self.approx_value_label.setText(f"{tolerance:.1f}")
        self.vector_settings.approx_tolerance = tolerance
        
        if hasattr(self, "detail_combo"):
            self.detail_combo.blockSignals(True)
            self.detail_combo.setCurrentText("Custom")
            self.detail_combo.blockSignals(False)
            
        self._set_preset_custom()
        self._run_vectorization()

    def _on_smoothing_changed(self, enabled: bool) -> None:
        """Handle contour smoothing option changes."""
        self.vector_settings.smoothing_enabled = enabled
        self._set_preset_custom()
        self._run_vectorization()

    def _on_invert_changed(self, enabled: bool) -> None:
        """Handle invert detection option changes."""
        self.vector_settings.invert = enabled
        self._set_preset_custom()
        self._run_vectorization()

    def _on_detail_level_changed(self, text: str) -> None:
        """Handle detail level changes by mapping to preset simplification values."""
        if text == "Low":
            self.approx_slider.blockSignals(True)
            self.approx_slider.setValue(50) # 5.0
            self.approx_slider.blockSignals(False)
            self.approx_value_label.setText("5.0")
            self.vector_settings.approx_tolerance = 5.0
        elif text == "Medium":
            self.approx_slider.blockSignals(True)
            self.approx_slider.setValue(20) # 2.0
            self.approx_slider.blockSignals(False)
            self.approx_value_label.setText("2.0")
            self.vector_settings.approx_tolerance = 2.0
        elif text == "High":
            self.approx_slider.blockSignals(True)
            self.approx_slider.setValue(5)  # 0.5
            self.approx_slider.blockSignals(False)
            self.approx_value_label.setText("0.5")
            self.vector_settings.approx_tolerance = 0.5
        
        self._set_preset_custom()
        self._run_vectorization()

    def _on_color_mode_changed(self, text: str) -> None:
        """Handle color mode combobox changes."""
        is_custom = (text == "Custom colors")
        self.color_count_widget.setVisible(is_custom)
        self.vector_settings.color_mode = text
        self._set_preset_custom()
        self._run_vectorization()

    def _on_color_count_changed(self, value: int) -> None:
        """Handle custom color count slider changes."""
        self.color_count_value_label.setText(str(value))
        self.vector_settings.color_count = value
        self._set_preset_custom()
        self._run_vectorization()

    def _on_overlay_changed(self, enabled: bool) -> None:
        """Handle overlay checkbox toggles."""
        self._run_vectorization()

    def _on_preserve_edges_changed(self, enabled: bool) -> None:
        """Handle preserve artwork edges changes."""
        self.vector_settings.preserve_edges = enabled
        self._set_preset_custom()
        self._run_vectorization()

    def _on_remove_bg_changed(self, enabled: bool) -> None:
        """Handle remove background option changes."""
        self.bg_tolerance_widget.setVisible(enabled)
        self.vector_settings.remove_background = enabled
        self._set_preset_custom()
        self._run_vectorization()

    def _on_bg_tolerance_changed(self, value: int) -> None:
        """Handle background tolerance slider changes."""
        self.bg_tolerance_value_label.setText(str(value))
        self.vector_settings.bg_tolerance = float(value)
        self._set_preset_custom()
        self._run_vectorization()

    def _start_processing(self) -> None:
        """Start the background image processing thread."""
        if not self.current_image_info:
            return

        if self.processor_thread and self.processor_thread.isRunning():
            self._processing_pending = True
            return

        if self.vectorization_thread and self.vectorization_thread.isRunning():
            self._discard_vectorization_result = True

        self.processor_thread = ImageProcessorThread(
            self.current_image_info.file_path,
            self.threshold_slider.value(),
            self
        )
        self.processor_thread.result_ready.connect(self._on_processing_finished)
        self.processor_thread.finished.connect(self._on_processing_thread_finished)
        self.processor_thread.start()

    def _on_processing_finished(self, result: object) -> None:
        """Handle result from background processing thread."""
        if self._processing_pending:
            return

        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], QImage):
            q_img, thresholded = result
            self.thresholded_array = thresholded
            
            # Display raster thresholded image in Raster Preview tab
            raster_pixmap = QPixmap.fromImage(q_img)
            self.raster_view.setImage(raster_pixmap)
            
            self._run_vectorization(processing_completed=True)
        elif isinstance(result, str):
            self._clear_processing_result()
            self.statusBar().showMessage("Image processing failed.")
            QMessageBox.warning(self, "Processing Error", f"Failed to process image:\n{result}")

    def _on_processing_thread_finished(self) -> None:
        """Start the latest queued processing request after the active worker exits."""
        self.processor_thread = None
        if self._processing_pending:
            self._processing_pending = False
            self._start_processing()

    def _run_vectorization(self, *, processing_completed: bool = False) -> None:
        """Run the vectorization engine on the thresholded image in a background thread."""
        if self.thresholded_array is None:
            return

        self.export_button.setEnabled(False)
        if processing_completed:
            self.statusBar().showMessage("Image processing complete. Vectorizing image...")
        else:
            self.statusBar().showMessage("Vectorizing image... Please wait.")

        if self.vectorization_thread and self.vectorization_thread.isRunning():
            self._vectorization_pending = True
            return

        # Map dynamic UI controls to VTracer settings
        import math
        
        # Detail Level mapping
        detail = self.detail_combo.currentText()
        if detail == "Low":
            self.vector_settings.vtracer.corner_threshold = 80
            self.vector_settings.vtracer.max_iterations = 5
        elif detail == "Medium":
            self.vector_settings.vtracer.corner_threshold = 60
            self.vector_settings.vtracer.max_iterations = 12
        elif detail == "High":
            self.vector_settings.vtracer.corner_threshold = 25
            self.vector_settings.vtracer.max_iterations = 20

        # Min Area (0-1000) to filter_speckle (1-250)
        min_area_val = self.min_area_slider.value()
        self.vector_settings.vtracer.filter_speckle = max(1, min_area_val // 25)

        # Approx Tolerance (slider value / 10.0) to VTracer curve length threshold.
        approx_val = self.approx_slider.value() / 10.0
        self.vector_settings.vtracer.length_threshold = max(3.5, min(10.0, approx_val + 1.5))

        # Color mode and precision mapping
        if self.color_mode_combo.currentText() == "Custom colors":
            color_cnt = self.color_count_slider.value()
            precision = max(1, min(8, int(math.ceil(math.log2(color_cnt)))))
            self.vector_settings.vtracer.color_precision = precision
        elif self.preset_combo.currentText() == "Photo":
            self.vector_settings.vtracer.color_precision = 8
        else:
            self.vector_settings.vtracer.color_precision = 6

        # Sync VTracer comboboxes explicitly here to handle signal blocking when presets are selected
        vt_color_text = self.vtracer_color_mode_combo.currentText()
        self.vector_settings.vtracer.colormode = "color" if vt_color_text == "Color" else "binary"

        vt_hierarchical_text = self.vtracer_hierarchical_combo.currentText()
        self.vector_settings.vtracer.hierarchical = vt_hierarchical_text.lower()

        vt_mode_text = self.vtracer_mode_combo.currentText()
        vt_mode_val = vt_mode_text.lower()
        if vt_mode_val == "pixel":
            vt_mode_val = "none"
        self.vector_settings.vtracer.mode = vt_mode_val

        file_path = self.current_image_info.file_path if self.current_image_info else None

        self.vectorization_thread = VectorizationThread(
            self.thresholded_array,
            self.vector_settings,
            file_path,
            self
        )
        self.vectorization_thread.result_ready.connect(self._on_vectorization_finished)
        self.vectorization_thread.finished.connect(self._on_vectorization_thread_finished)
        self.vectorization_thread.start()

    def _on_vectorization_finished(self, result: object) -> None:
        """Handle result from background vectorization thread."""
        if self._vectorization_pending or self._discard_vectorization_result:
            return

        from app.core.vectorizer_backend import VTracerVectorResult
        if isinstance(result, VectorResult):
            self.vector_result = result
            try:
                vector_image = self._render_vector_result(result)
            except Exception as error:
                self.vector_result = None
                self.export_button.setEnabled(False)
                self.statusBar().showMessage("Vector preview rendering failed.")
                QMessageBox.warning(
                    self,
                    "Preview Render Error",
                    f"Failed to render vector preview:\n{error}",
                )
                return
            self.processed_pixmap = QPixmap.fromImage(vector_image)
            self._update_result_image()

            if getattr(result, "fallback_error", None):
                self.statusBar().showMessage("VTracer failed! Fallback to OpenCV Legacy.")
                QMessageBox.warning(
                    self,
                    "VTracer Engine Fallback",
                    f"VTracer failed to vectorize the image. Falling back to OpenCV Legacy engine.\n\nError details:\n{result.fallback_error}"
                )

            engine_name = "VTracer" if isinstance(result, VTracerVectorResult) else "OpenCV Legacy"

            is_large = False
            if isinstance(result, VTracerVectorResult):
                is_large = len(result.svg_data) > 1.5 * 1024 * 1024 # 1.5 MB

            warning_suffix = " (Warn: SVG is complex/large!)" if is_large else ""

            if result.path_count == 0:
                self.statusBar().showMessage(f"[{engine_name}] No paths detected. Adjust settings (e.g. lower Min Area or adjust Threshold).")
                self.export_button.setEnabled(False)
            elif result.path_count > 2000:
                self.statusBar().showMessage(
                    f"[{engine_name}] Processing complete. Vectorized: {result.path_count} paths (too noisy? Try increasing Min Area). "
                    f"Points: {result.simplified_point_count} (reduced from {result.original_point_count}).{warning_suffix}"
                )
                self.export_button.setEnabled(True)
            else:
                self.statusBar().showMessage(
                    f"[{engine_name}] Processing complete. Vectorized: {result.path_count} paths. "
                    f"Points: {result.simplified_point_count} (reduced from {result.original_point_count}).{warning_suffix}"
                )
                self.export_button.setEnabled(True)
        else:
            self.vector_result = None
            self.export_button.setEnabled(False)
            self.statusBar().showMessage("Vectorization failed.")
            QMessageBox.warning(self, "Vectorization Error", f"Failed to vectorize image:\n{result}")

    def _on_vectorization_thread_finished(self) -> None:
        """Start the latest queued vectorization request after the active worker exits."""
        self.vectorization_thread = None
        if self._discard_vectorization_result:
            self._discard_vectorization_result = False
            if not self._vectorization_pending:
                return
        if self._vectorization_pending:
            self._vectorization_pending = False
            self._run_vectorization()

    def _render_vector_result(self, vector_result) -> QImage:
        """Draw vector paths on a plain white QImage or overlay on the original image."""
        from app.core.vectorizer_backend import VTracerVectorResult
        if isinstance(vector_result, VTracerVectorResult):
            width = vector_result.image_width
            height = vector_result.image_height
            if width <= 0 or height <= 0:
                width, height = 400, 400

            if hasattr(self, "overlay_checkbox") and self.overlay_checkbox.isChecked() and hasattr(self, "original_pixmap") and not self.original_pixmap.isNull():
                image = self.original_pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
            else:
                image = QImage(width, height, QImage.Format.Format_ARGB32)
                image.fill(Qt.GlobalColor.white)

            from PySide6.QtSvg import QSvgRenderer
            renderer = QSvgRenderer(vector_result.svg_data.encode("utf-8"))
            if not renderer.isValid():
                raise ValueError("Generated SVG is invalid and cannot be rendered.")
            painter = QPainter(image)
            try:
                renderer.render(painter)
            finally:
                painter.end()
            return image

        width = vector_result.image_width
        height = vector_result.image_height

        if width <= 0 or height <= 0:
            if self.current_image_info:
                width = self.current_image_info.width
                height = self.current_image_info.height
            else:
                width, height = 400, 400

        # Check if overlay is requested and original image is available
        if hasattr(self, "overlay_checkbox") and self.overlay_checkbox.isChecked() and hasattr(self, "original_pixmap") and not self.original_pixmap.isNull():
            image = self.original_pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        else:
            image = QImage(width, height, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.white)

        painter = QPainter(image)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            for path in vector_result.paths:
                points = path.points
                if len(points) < 2:
                    continue

                r, g, b = path.color
                path_color = QColor(r, g, b)
                painter.setPen(QPen(path_color, 1))
                painter.setBrush(QBrush(path_color))

                painter_path = QPainterPath()
                painter_path.setFillRule(Qt.FillRule.OddEvenFill)
                painter_path.addPolygon(
                    QPolygon([QPoint(int(pt[0]), int(pt[1])) for pt in points])
                )
                for hole in path.holes:
                    painter_path.addPolygon(
                        QPolygon([QPoint(int(pt[0]), int(pt[1])) for pt in hole])
                    )
                painter.drawPath(painter_path)
        finally:
            painter.end()
        return image

    def _export_svg(self) -> None:
        """Export the current vector result to an SVG file."""
        if not self.vector_result:
            return

        default_name = ""
        if self.current_image_info:
            dir_name = os.path.dirname(self.current_image_info.file_path)
            base_name, _ = os.path.splitext(self.current_image_info.file_name)
            default_name = os.path.join(dir_name, f"{base_name}_vectorized.svg")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export SVG",
            default_name,
            "SVG Files (*.svg)"
        )
        if not file_path:
            return

        try:
            self.statusBar().showMessage("Exporting SVG...")
            from app.services.svg_exporter import export_svg
            source_name = self.current_image_info.file_name if self.current_image_info else None
            output_path = export_svg(self.vector_result, file_path, source_name)

            self.statusBar().showMessage(f"Successfully exported to {output_path.name}")
            QMessageBox.information(
                self,
                "Export Complete",
                f"Successfully exported SVG to:\n{output_path}"
            )
        except Exception as error:
            self.statusBar().showMessage("Export failed.")
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export SVG:\n{error}"
            )

    def _process_batch(self) -> None:
        """Process all valid selected batch images and export them as SVGs."""
        if self.batch_thread and self.batch_thread.isRunning():
            return

        valid_paths = [f.file_path for f in self.batch_files if f.is_valid]
        if not valid_paths:
            return

        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder for Batch SVG Export",
            ""
        )
        if not output_dir:
            return

        total = len(valid_paths)
        self.statusBar().showMessage(f"Starting batch process for {total} images...")
        self.process_batch_button.setEnabled(False)
        self.batch_thread = BatchProcessingThread(
            valid_paths,
            output_dir,
            self.threshold_slider.value(),
            self.vector_settings,
            self,
        )
        self.batch_thread.progress.connect(self._on_batch_progress)
        self.batch_thread.result_ready.connect(self._on_batch_finished)
        self.batch_thread.finished.connect(self._on_batch_thread_finished)
        self.batch_thread.start()

    def _on_batch_progress(
        self,
        index: int,
        total_count: int,
        filename: str,
        success: bool,
    ) -> None:
        """Display progress reported by the batch worker."""
        status = "Success" if success else "Failed"
        self.statusBar().showMessage(
            f"Processing [{index}/{total_count}]: {filename} ({status})"
        )

    def _on_batch_finished(self, result: object) -> None:
        """Display the final batch result or worker error."""
        if isinstance(result, tuple) and len(result) >= 2:
            success_count = result[0]
            failed_count = result[1]
            errors = result[2] if len(result) == 3 else {}
            
            self.statusBar().showMessage(
                f"Batch complete. Success: {success_count}, Failed: {failed_count}."
            )
            
            error_details = ""
            if errors:
                error_details = "\n\nFailure Details:\n" + "\n".join(f"- {fname}: {err}" for fname, err in errors.items())
                
            QMessageBox.information(
                self,
                "Batch Processing Complete",
                f"Batch processing finished!\n\n"
                f"Successfully exported: {success_count} SVGs\n"
                f"Failed: {failed_count} images"
                f"{error_details}",
            )
        else:
            self.statusBar().showMessage("Batch process failed.")
            QMessageBox.critical(
                self,
                "Batch Processing Error",
                f"An error occurred during batch processing:\n{result}",
            )

    def _on_batch_thread_finished(self) -> None:
        """Restore batch controls after the worker exits."""
        self.batch_thread = None
        self.process_batch_button.setEnabled(
            any(batch_file.is_valid for batch_file in self.batch_files)
        )

    def _select_batch_images(self) -> None:
        """Select, validate, and display images for a future batch operation."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Batch Images",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not file_paths:
            return

        self.batch_files = validate_batch_files(file_paths)
        self.batch_file_list.clear()

        invalid_count = 0
        for batch_file in self.batch_files:
            if batch_file.is_valid:
                self.batch_file_list.addItem(batch_file.file_name)
            else:
                invalid_count += 1
                self.batch_file_list.addItem(
                    f"{batch_file.file_name} - Invalid: {batch_file.error}"
                )

        valid_count = len(self.batch_files) - invalid_count
        self.process_batch_button.setEnabled(valid_count > 0)
        self.statusBar().showMessage(
            f"Batch selection: {valid_count} valid, {invalid_count} invalid."
        )

        if invalid_count:
            QMessageBox.warning(
                self,
                "Invalid Batch Images",
                f"{invalid_count} selected image(s) could not be validated.",
            )

    def _update_metadata_display(self, info: ImageInfo) -> None:
        """Populate metadata labels in the controls panel."""
        self.meta_labels["File"].setText(info.file_name)
        self.meta_labels["Size"].setText(info.file_size_display)
        self.meta_labels["Resolution"].setText(info.resolution_display)
        self.meta_labels["Format"].setText(info.image_format)
        self.meta_labels["Color Mode"].setText(info.color_mode)

    def _clear_processing_result(self) -> None:
        """Clear derived image state while preserving the imported original image."""
        self.thresholded_array = None
        self.vector_result = None
        self.processed_pixmap = QPixmap()
        self.raster_view.setImage(QPixmap())
        self.result_view.setImage(QPixmap())
        self.export_button.setEnabled(False)

    def _update_zoom_label(self, zoom_level: float) -> None:
        """Update the preview toolbar zoom text."""
        self.zoom_label.setText(f"Zoom: {int(zoom_level * 100)}%")

    def _fit_to_screen(self) -> None:
        """Scale both preview views to fit the loaded image."""
        if hasattr(self, "original_pixmap") and not self.original_pixmap.isNull():
            view_size = self.original_view.viewport().size()
            pix_size = self.original_pixmap.size()
            
            if pix_size.width() > 0 and pix_size.height() > 0:
                w_ratio = view_size.width() / pix_size.width()
                h_ratio = view_size.height() / pix_size.height()
                zoom = min(w_ratio, h_ratio) * 0.95
                
                self.original_view.applyZoom(zoom)
                self.result_view.applyZoom(zoom)
                self.raster_view.applyZoom(zoom)
                self._update_zoom_label(zoom)

    def _actual_size(self) -> None:
        """Set zoom scale to 100% on both views."""
        self.original_view.applyZoom(1.0)
        self.result_view.applyZoom(1.0)
        self.raster_view.applyZoom(1.0)
        self._update_zoom_label(1.0)

    def _update_preview_image(self) -> None:
        """Set the original image in the graphics view."""
        if hasattr(self, "original_pixmap") and not self.original_pixmap.isNull():
            self.original_view.setImage(self.original_pixmap)
        self._update_result_image()

    def _update_result_image(self) -> None:
        """Set the vectorized result image in the graphics view."""
        if hasattr(self, "processed_pixmap") and not self.processed_pixmap.isNull():
            self.result_view.setImage(self.processed_pixmap)

    def resizeEvent(self, event) -> None:
        """Handle window resize event."""
        super().resizeEvent(event)
