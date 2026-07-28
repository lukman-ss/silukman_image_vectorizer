from __future__ import annotations

from typing import Optional, cast

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import (
    QBrush,
    QColor,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygon,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QPoint

from app.config.settings import DEFAULT_WINDOW_HEIGHT, DEFAULT_WINDOW_WIDTH, VectorizationSettings
from app.controllers.vectorizer_controller import VectorizerController
from app.core.constants import APPLICATION_TITLE, CONTROL_PANEL_TITLE, SIDEBAR_TITLE, STATUS_READY
from app.core.vectorization_engine import VectorResult
from app.services.color_palette import ColorRGB, color_to_hex, extract_dominant_colors
from app.services.export_service import ExportService
from app.services.file_dialog_service import FileDialogService
from app.services.image_loader_service import ImageLoaderService
from app.services.image_processing_service import ImageProcessingService
from app.services.settings_service import SettingsService
from app.services.validation_service import ValidationService
from app.services.image_loader import ImageInfo
from app.ui.sync_graphics_view import SyncGraphicsView


class MainWindow(QMainWindow):
    """Main application window — handles layout, event binding, and UI state only."""

    def __init__(self) -> None:
        super().__init__()

        # ── DI: build services ──────────────────────────────────────────────
        self._settings_service = SettingsService()
        self._validation_service = ValidationService()
        self._image_loader_service = ImageLoaderService()
        self._image_processing_service = ImageProcessingService()
        self._export_service = ExportService()
        self._file_dialog_service = FileDialogService()

        self._controller = VectorizerController(
            image_loader_service=self._image_loader_service,
            image_processing_service=self._image_processing_service,
            export_service=self._export_service,
            file_dialog_service=self._file_dialog_service,
            settings_service=self._settings_service,
            validation_service=self._validation_service,
        )

        # ── Wire controller callbacks ──────────────────────────────────────
        self._controller.on_processing_done = self._on_processing_done
        self._controller.on_processing_error = self._on_processing_error
        self._controller.on_vectorization_done = self._on_vectorization_done
        self._controller.on_vectorization_error = self._on_vectorization_error

        # ── Local UI state ─────────────────────────────────────────────────
        self.original_pixmap = QPixmap()
        self.processed_pixmap = QPixmap()
        self.current_image_info: Optional[ImageInfo] = None
        self.palette_colors: list[ColorRGB] = []
        self.palette_replacements: dict[ColorRGB, ColorRGB] = {}
        self.palette_buttons: list[QPushButton] = []
        self.is_palette_pick_mode = False
        self._updating_from_preset = False

        # ── Engine availability ────────────────────────────────────────────
        from app.core.vectorizer_backend import VTRACER_AVAILABLE
        self._controller.vector_settings.engine_type = (
            "VTracer" if VTRACER_AVAILABLE else "OpenCV Legacy"
        )

        # ── Window setup ───────────────────────────────────────────────────
        self.setWindowTitle(APPLICATION_TITLE)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setCentralWidget(self._create_main_layout())
        self.setStatusBar(self._create_status_bar())

        from app.ui.theme import normalize_theme_mode
        saved_theme = normalize_theme_mode(self._settings_service.get_theme())
        self.theme_combo.setCurrentText(saved_theme)
        self._apply_theme(saved_theme)

    # ═══════════════════════════════════════════════════════════════════════
    # Layout construction
    # ═══════════════════════════════════════════════════════════════════════

    def _create_main_layout(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        panels = QWidget()
        panels.setLayout(self._create_panels_layout())
        layout.addWidget(panels)
        return container

    def _create_panels_layout(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        sidebar = self._create_panel(SIDEBAR_TITLE, 180)
        controls = self._create_panel(CONTROL_PANEL_TITLE, 240)

        # ── Sidebar ──────────────────────────────────────────────────────
        import_button = QPushButton("Import Image")
        import_button.clicked.connect(self._import_image)
        cast(QVBoxLayout, sidebar.layout()).addWidget(import_button)

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

        self.process_batch_button = QPushButton("Process Batch")
        self.process_batch_button.setEnabled(False)
        self.process_batch_button.clicked.connect(self._process_batch)
        cast(QVBoxLayout, sidebar.layout()).addWidget(self.process_batch_button)

        # ── Controls: metadata ───────────────────────────────────────────
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

        # ── Controls: palette ────────────────────────────────────────────
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

        # ── Controls: preset ─────────────────────────────────────────────
        preset_group = QWidget()
        preset_layout = QVBoxLayout(preset_group)
        preset_layout.setContentsMargins(4, 12, 4, 4)
        preset_layout.setSpacing(6)
        preset_title = QLabel("<b>Quality Preset:</b>")
        self.preset_combo = QComboBox()
        from app.config.preset_manager import PresetManager
        available_presets = PresetManager.get_instance().get_available_presets()
        self.preset_combo.addItems(available_presets + ["Custom"])
        self.preset_combo.setCurrentText("balanced" if "balanced" in available_presets else "Custom")
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(preset_title)
        preset_layout.addWidget(self.preset_combo)
        cast(QVBoxLayout, controls.layout()).addWidget(preset_group)

        # ── Controls: engine ─────────────────────────────────────────────
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
        else:
            self.engine_combo.setCurrentText(self._controller.vector_settings.engine_type)
        engine_layout.addWidget(engine_title)
        engine_layout.addWidget(self.engine_combo)
        cast(QVBoxLayout, controls.layout()).addWidget(engine_group)

        # ── Controls: hand-pick settings ─────────────────────────────────
        self.handpick_group = QGroupBox("Hand-pick Settings")
        handpick_layout = QVBoxLayout(self.handpick_group)
        handpick_layout.setContentsMargins(6, 12, 6, 6)
        handpick_layout.setSpacing(8)

        # Threshold
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

        # Detail level
        detail_title = QLabel("<b>Detail Level:</b>")
        self.detail_combo = QComboBox()
        self.detail_combo.addItems(["Low", "Medium", "High", "Custom"])
        self.detail_combo.setCurrentText("Medium")
        self.detail_combo.currentTextChanged.connect(self._on_detail_level_changed)
        handpick_layout.addWidget(detail_title)
        handpick_layout.addWidget(self.detail_combo)

        # Min Area
        min_area_title = QLabel("<b>Min Area (px):</b>")
        min_area_layout = QHBoxLayout()
        self.min_area_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_area_slider.setRange(0, 1000)
        self.min_area_slider.setValue(100)
        self.min_area_slider.valueChanged.connect(self._on_min_area_changed)
        self.min_area_value_label = QLabel("100")
        self.min_area_value_label.setFixedWidth(30)
        self.min_area_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        min_area_layout.addWidget(self.min_area_slider)
        min_area_layout.addWidget(self.min_area_value_label)
        handpick_layout.addWidget(min_area_title)
        handpick_layout.addLayout(min_area_layout)

        # Approx Tolerance
        approx_title = QLabel("<b>Approx Tolerance:</b>")
        approx_layout = QHBoxLayout()
        self.approx_slider = QSlider(Qt.Orientation.Horizontal)
        self.approx_slider.setRange(0, 100)
        self.approx_slider.setValue(20)
        self.approx_slider.valueChanged.connect(self._on_approx_tolerance_changed)
        self.approx_value_label = QLabel("2.0")
        self.approx_value_label.setFixedWidth(30)
        self.approx_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        approx_layout.addWidget(self.approx_slider)
        approx_layout.addWidget(self.approx_value_label)
        handpick_layout.addWidget(approx_title)
        handpick_layout.addLayout(approx_layout)

        # Checkboxes
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

        # BG Tolerance
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

        # Color Mode
        color_mode_title = QLabel("<b>Color Mode:</b>")
        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(["Unlimited colors", "Custom colors"])
        self.color_mode_combo.currentTextChanged.connect(self._on_color_mode_changed)
        handpick_layout.addWidget(color_mode_title)
        handpick_layout.addWidget(self.color_mode_combo)

        # Color Count
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

        # VTracer params
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

        # Overlay
        self.overlay_checkbox = QCheckBox("Overlay paths on original")
        self.overlay_checkbox.toggled.connect(self._on_overlay_changed)
        handpick_layout.addWidget(self.overlay_checkbox)

        cast(QVBoxLayout, controls.layout()).addWidget(self.handpick_group)

        # Engine-specific visibility
        is_vtracer = (self._controller.vector_settings.engine_type == "VTracer")
        self.threshold_group.setVisible(not is_vtracer)
        self.smoothing_checkbox.setVisible(not is_vtracer)
        self.invert_checkbox.setVisible(not is_vtracer)
        self.preserve_edges_checkbox.setVisible(not is_vtracer)
        self.vtracer_params_widget.setVisible(is_vtracer)

        # Reset / Re-vectorize
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

        # Theme
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

        # ── Preview area ─────────────────────────────────────────────────
        preview_area = QWidget()
        preview_vbox = QVBoxLayout(preview_area)
        preview_vbox.setContentsMargins(0, 0, 0, 0)
        preview_vbox.setSpacing(6)

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

        preview_hbox = QHBoxLayout()
        preview_hbox.setContentsMargins(0, 0, 0, 0)
        preview_hbox.setSpacing(8)

        original_panel = self._create_panel("Original Image")
        self.original_view = SyncGraphicsView()
        self.original_view.image_clicked.connect(self._on_original_image_clicked)
        cast(QVBoxLayout, original_panel.layout()).addWidget(self.original_view, 1)

        self.result_tabs = QTabWidget()

        vector_panel = self._create_panel("Vectorized Result")
        self.result_view = SyncGraphicsView()
        cast(QVBoxLayout, vector_panel.layout()).addWidget(self.result_view, 1)
        self.result_tabs.addTab(vector_panel, "Vectorized Result")

        raster_panel = self._create_panel("Thresholded Raster")
        self.raster_view = SyncGraphicsView()
        cast(QVBoxLayout, raster_panel.layout()).addWidget(self.raster_view, 1)
        self.result_tabs.addTab(raster_panel, "Thresholded Raster")

        preview_hbox.addWidget(original_panel, 1)
        preview_hbox.addWidget(self.result_tabs, 1)
        preview_vbox.addLayout(preview_hbox, 1)

        # Sync zoom
        self.original_view.zoomed.connect(self.result_view.applyZoom)
        self.original_view.zoomed.connect(self.raster_view.applyZoom)
        self.original_view.zoomed.connect(self._update_zoom_label)
        self.result_view.zoomed.connect(self.original_view.applyZoom)
        self.result_view.zoomed.connect(self.raster_view.applyZoom)
        self.result_view.zoomed.connect(self._update_zoom_label)
        self.raster_view.zoomed.connect(self.original_view.applyZoom)
        self.raster_view.zoomed.connect(self.result_view.applyZoom)
        self.raster_view.zoomed.connect(self._update_zoom_label)

        # Sync pan
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
        panel.setLayout(layout)
        return panel

    def _create_status_bar(self) -> QStatusBar:
        status_bar = QStatusBar()
        status_bar.showMessage(STATUS_READY)
        return status_bar

    # ═══════════════════════════════════════════════════════════════════════
    # Event handlers — delegate to controller, update UI
    # ═══════════════════════════════════════════════════════════════════════

    def _import_image(self) -> None:
        file_path = self._file_dialog_service.open_image_file(self)
        if not file_path:
            return

        pixmap, info, error = self._controller.load_image(file_path)
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
        self._controller.start_processing(info.file_path, self.threshold_slider.value())
        self.statusBar().showMessage(f"Image loaded: {info.file_name}")

    def _on_processing_done(self, q_img: QImage, thresholded) -> None:
        raster_pixmap = QPixmap.fromImage(q_img)
        self.raster_view.setImage(raster_pixmap)
        self.statusBar().showMessage("Image processing complete. Vectorizing image...")
        self._run_vectorization()

    def _on_processing_error(self, error_str: str) -> None:
        self._clear_processing_result()
        self.statusBar().showMessage("Image processing failed.")
        QMessageBox.warning(self, "Processing Error", f"Failed to process image:\n{error_str}")

    def _run_vectorization(self) -> None:
        """Sync UI state to controller settings, then launch vectorization."""
        if self._controller.state.thresholded_array is None:
            return

        self.export_button.setEnabled(False)
        self.statusBar().showMessage("Vectorizing image... Please wait.")

        self._controller.sync_vtracer_settings_from_ui(
            detail_text=self.detail_combo.currentText(),
            min_area_val=self.min_area_slider.value(),
            approx_slider_val=self.approx_slider.value(),
            color_mode_text=self.color_mode_combo.currentText(),
            color_count_val=self.color_count_slider.value(),
            preset_text=self.preset_combo.currentText(),
            vt_color_text=self.vtracer_color_mode_combo.currentText(),
            vt_hierarchical_text=self.vtracer_hierarchical_combo.currentText(),
            vt_mode_text=self.vtracer_mode_combo.currentText(),
        )
        self._controller.run_vectorization()

    def _on_vectorization_done(self, result: VectorResult) -> None:
        try:
            vector_image = self._render_vector_result(result)
        except Exception as error:
            self.export_button.setEnabled(False)
            self.statusBar().showMessage("Vector preview rendering failed.")
            QMessageBox.warning(self, "Preview Render Error", f"Failed to render vector preview:\n{error}")
            return

        self.processed_pixmap = QPixmap.fromImage(vector_image)
        self._update_result_image()

        if getattr(result, "fallback_error", None):
            self.statusBar().showMessage("VTracer failed! Fallback to OpenCV Legacy.")
            QMessageBox.warning(
                self, "VTracer Engine Fallback",
                f"VTracer failed to vectorize the image. Falling back to OpenCV Legacy engine.\n\nError details:\n{result.fallback_error}"
            )

        from app.core.vectorizer_backend import VTracerVectorResult
        engine_name = "VTracer" if isinstance(result, VTracerVectorResult) else "OpenCV Legacy"
        is_large = isinstance(result, VTracerVectorResult) and len(result.svg_data) > 1.5 * 1024 * 1024
        warning_suffix = " (Warn: SVG is complex/large!)" if is_large else ""

        if result.path_count == 0:
            self.statusBar().showMessage(f"[{engine_name}] No paths detected. Adjust settings.")
            self.export_button.setEnabled(False)
        else:
            noise_hint = " (too noisy? Try increasing Min Area)." if result.path_count > 2000 else "."
            self.statusBar().showMessage(
                f"[{engine_name}] Vectorized: {result.path_count} paths{noise_hint} "
                f"Points: {result.simplified_point_count} (reduced from {result.original_point_count}).{warning_suffix}"
            )
            self.export_button.setEnabled(True)

    def _on_vectorization_error(self, error_str: str) -> None:
        self.export_button.setEnabled(False)
        self.statusBar().showMessage("Vectorization failed.")
        QMessageBox.warning(self, "Vectorization Error", f"Failed to vectorize image:\n{error_str}")

    def _export_svg(self) -> None:
        if not self._controller.state.vector_result:
            return
        default_path = self._controller.build_default_export_path(self.current_image_info)
        file_path = self._file_dialog_service.save_svg_file(self, default_path)
        if not file_path:
            return
        try:
            self.statusBar().showMessage("Exporting SVG...")
            source_name = self.current_image_info.file_name if self.current_image_info else None
            output_path = self._controller.export_svg(file_path, source_name)
            self.statusBar().showMessage(f"Successfully exported to {output_path.name}")
            QMessageBox.information(self, "Export Complete", f"Successfully exported SVG to:\n{output_path}")
        except Exception as error:
            self.statusBar().showMessage("Export failed.")
            QMessageBox.critical(self, "Export Error", f"Failed to export SVG:\n{error}")

    def _select_batch_images(self) -> None:
        file_paths = self._file_dialog_service.open_image_files(self)
        if not file_paths:
            return

        self._controller.state.batch_files = self._controller.validate_batch_files(file_paths)
        self.batch_file_list.clear()

        invalid_count = 0
        for batch_file in self._controller.state.batch_files:
            if batch_file.is_valid:
                self.batch_file_list.addItem(batch_file.file_name)
            else:
                invalid_count += 1
                self.batch_file_list.addItem(f"{batch_file.file_name} - Invalid: {batch_file.error}")

        valid_count = len(self._controller.state.batch_files) - invalid_count
        self.process_batch_button.setEnabled(valid_count > 0)
        self.statusBar().showMessage(f"Batch selection: {valid_count} valid, {invalid_count} invalid.")
        if invalid_count:
            QMessageBox.warning(self, "Invalid Batch Images", f"{invalid_count} selected image(s) could not be validated.")

    def _process_batch(self) -> None:
        if self._controller.is_batch_running():
            return
        valid_paths = [f.file_path for f in self._controller.state.batch_files if f.is_valid]
        if not valid_paths:
            return

        output_dir = self._file_dialog_service.select_directory(self)
        if not output_dir:
            return

        self.statusBar().showMessage(f"Starting batch process for {len(valid_paths)} images...")
        self.process_batch_button.setEnabled(False)
        self._controller.start_batch(
            valid_paths=valid_paths,
            output_dir=output_dir,
            threshold_val=self.threshold_slider.value(),
            on_progress=self._on_batch_progress,
            on_done=self._on_batch_finished,
            on_finished=self._on_batch_thread_finished,
        )

    def _on_batch_progress(self, index: int, total_count: int, filename: str, success: bool) -> None:
        status = "Success" if success else "Failed"
        self.statusBar().showMessage(f"Processing [{index}/{total_count}]: {filename} ({status})")

    def _on_batch_finished(self, result: object) -> None:
        if isinstance(result, tuple) and len(result) >= 2:
            success_count, failed_count = result[0], result[1]
            errors = result[2] if len(result) == 3 else {}
            self.statusBar().showMessage(f"Batch complete. Success: {success_count}, Failed: {failed_count}.")
            error_details = ""
            if errors:
                error_details = "\n\nFailure Details:\n" + "\n".join(f"- {f}: {e}" for f, e in errors.items())
            QMessageBox.information(
                self, "Batch Processing Complete",
                f"Batch processing finished!\n\nSuccessfully exported: {success_count} SVGs\nFailed: {failed_count} images{error_details}"
            )
        else:
            self.statusBar().showMessage("Batch process failed.")
            QMessageBox.critical(self, "Batch Processing Error", f"An error occurred during batch processing:\n{result}")

    def _on_batch_thread_finished(self) -> None:
        self.process_batch_button.setEnabled(
            any(f.is_valid for f in self._controller.state.batch_files)
        )

    # ── Parameter event handlers ─────────────────────────────────────────────

    def _on_threshold_changed(self, value: int) -> None:
        self.threshold_value_label.setText(str(value))
        self._controller.vector_settings.threshold_val = value
        self._set_preset_custom()
        if self.current_image_info:
            self._controller.start_processing(self.current_image_info.file_path, value)

    def _on_min_area_changed(self, value: int) -> None:
        self.min_area_value_label.setText(str(value))
        self._controller.vector_settings.min_area = float(value)
        self._set_preset_custom()
        self._run_vectorization()

    def _on_approx_tolerance_changed(self, value: int) -> None:
        tolerance = value / 10.0
        self.approx_value_label.setText(f"{tolerance:.1f}")
        self._controller.vector_settings.approx_tolerance = tolerance
        self.detail_combo.blockSignals(True)
        self.detail_combo.setCurrentText("Custom")
        self.detail_combo.blockSignals(False)
        self._set_preset_custom()
        self._run_vectorization()

    def _on_detail_level_changed(self, text: str) -> None:
        mapping = {"Low": (50, "5.0", 5.0), "Medium": (20, "2.0", 2.0), "High": (5, "0.5", 0.5)}
        if text in mapping:
            slider_val, label_text, tolerance = mapping[text]
            self.approx_slider.blockSignals(True)
            self.approx_slider.setValue(slider_val)
            self.approx_slider.blockSignals(False)
            self.approx_value_label.setText(label_text)
            self._controller.vector_settings.approx_tolerance = tolerance
        self._set_preset_custom()
        self._run_vectorization()

    def _on_smoothing_changed(self, enabled: bool) -> None:
        self._controller.vector_settings.smoothing_enabled = enabled
        self._set_preset_custom()
        self._run_vectorization()

    def _on_invert_changed(self, enabled: bool) -> None:
        self._controller.vector_settings.invert = enabled
        self._set_preset_custom()
        self._run_vectorization()

    def _on_color_mode_changed(self, text: str) -> None:
        self.color_count_widget.setVisible(text == "Custom colors")
        self._controller.vector_settings.color_mode = text
        self._set_preset_custom()
        self._run_vectorization()

    def _on_color_count_changed(self, value: int) -> None:
        self.color_count_value_label.setText(str(value))
        self._controller.vector_settings.color_count = value
        self._set_preset_custom()
        self._run_vectorization()

    def _on_preserve_edges_changed(self, enabled: bool) -> None:
        self._controller.vector_settings.preserve_edges = enabled
        self._set_preset_custom()
        self._run_vectorization()

    def _on_remove_bg_changed(self, enabled: bool) -> None:
        self.bg_tolerance_widget.setVisible(enabled)
        self._controller.vector_settings.remove_background = enabled
        self._set_preset_custom()
        self._run_vectorization()

    def _on_bg_tolerance_changed(self, value: int) -> None:
        self.bg_tolerance_value_label.setText(str(value))
        self._controller.vector_settings.bg_tolerance = float(value)
        self._set_preset_custom()
        self._run_vectorization()

    def _on_overlay_changed(self, _enabled: bool) -> None:
        self._run_vectorization()

    def _on_engine_changed(self, text: str) -> None:
        self._controller.vector_settings.engine_type = text
        is_vtracer = (text == "VTracer")
        self.threshold_group.setVisible(not is_vtracer)
        self.smoothing_checkbox.setVisible(not is_vtracer)
        self.invert_checkbox.setVisible(not is_vtracer)
        self.preserve_edges_checkbox.setVisible(not is_vtracer)
        self.vtracer_params_widget.setVisible(is_vtracer)
        self._run_vectorization()

    def _on_vtracer_color_mode_changed(self, text: str) -> None:
        self._controller.vector_settings.vtracer.colormode = "color" if text == "Color" else "binary"
        self._set_preset_custom()
        self._run_vectorization()

    def _on_vtracer_hierarchical_changed(self, text: str) -> None:
        self._controller.vector_settings.vtracer.hierarchical = text.lower()
        self._set_preset_custom()
        self._run_vectorization()

    def _on_vtracer_mode_changed(self, text: str) -> None:
        mode_val = "none" if text.lower() == "pixel" else text.lower()
        self._controller.vector_settings.vtracer.mode = mode_val
        self._set_preset_custom()
        self._run_vectorization()

    def _reset_settings(self) -> None:
        self.preset_combo.setCurrentText("Logo")
        self.invert_checkbox.setChecked(False)
        self.overlay_checkbox.setChecked(False)
        self.vtracer_color_mode_combo.setCurrentText("Color")
        self.vtracer_hierarchical_combo.setCurrentText("Stacked")
        self.vtracer_mode_combo.setCurrentText("Spline")

    def _on_preset_changed(self, preset_name: str) -> None:
        if preset_name == "Custom":
            return
        from app.config.preset_manager import PresetManager
        try:
            config = PresetManager.get_instance().get_preset_config(preset_name)
        except ValueError:
            return

        self._updating_from_preset = True
        try:
            import copy
            self._controller.vector_settings = copy.deepcopy(config)

            self.threshold_slider.blockSignals(True)
            self.threshold_slider.setValue(config.threshold_val)
            self.threshold_value_label.setText(str(config.threshold_val))
            self.threshold_slider.blockSignals(False)

            self.min_area_slider.blockSignals(True)
            self.min_area_slider.setValue(int(config.min_area))
            self.min_area_value_label.setText(str(int(config.min_area)))
            self.min_area_slider.blockSignals(False)

            self.detail_combo.blockSignals(True)
            self.detail_combo.setCurrentText("Custom")
            self.detail_combo.blockSignals(False)

            self.smoothing_checkbox.blockSignals(True)
            self.smoothing_checkbox.setChecked(config.smoothing_enabled)
            self.smoothing_checkbox.blockSignals(False)

            self.preserve_edges_checkbox.blockSignals(True)
            self.preserve_edges_checkbox.setChecked(config.preserve_edges)
            self.preserve_edges_checkbox.blockSignals(False)

            self.remove_bg_checkbox.blockSignals(True)
            self.remove_bg_checkbox.setChecked(config.remove_background)
            self.remove_bg_checkbox.blockSignals(False)
            self.bg_tolerance_widget.setVisible(config.remove_background)

            self.color_mode_combo.blockSignals(True)
            self.color_mode_combo.setCurrentText(config.color_mode)
            self.color_mode_combo.blockSignals(False)
            self.color_count_widget.setVisible(config.color_mode == "Custom colors")

            self.color_count_slider.blockSignals(True)
            self.color_count_slider.setValue(config.color_count)
            self.color_count_value_label.setText(str(config.color_count))
            self.color_count_slider.blockSignals(False)

            self.bg_tolerance_slider.blockSignals(True)
            self.bg_tolerance_slider.setValue(int(config.bg_tolerance))
            self.bg_tolerance_value_label.setText(str(int(config.bg_tolerance)))
            self.bg_tolerance_slider.blockSignals(False)

            self.vtracer_color_mode_combo.blockSignals(True)
            self.vtracer_color_mode_combo.setCurrentText("Color" if config.colormode == "color" else "Black & White")
            self.vtracer_color_mode_combo.blockSignals(False)

            self.vtracer_hierarchical_combo.blockSignals(True)
            self.vtracer_hierarchical_combo.setCurrentText("Stacked" if config.hierarchical == "stacked" else "Cutout")
            self.vtracer_hierarchical_combo.blockSignals(False)

            self.vtracer_mode_combo.blockSignals(True)
            vt_mode = "Spline" if config.mode == "spline" else ("Polygon" if config.mode == "polygon" else "Pixel")
            self.vtracer_mode_combo.setCurrentText(vt_mode)
            self.vtracer_mode_combo.blockSignals(False)
        finally:
            self._updating_from_preset = False

        if self.current_image_info:
            self._controller.start_processing(self.current_image_info.file_path, config.threshold_val)

    def _on_theme_changed(self, theme_name: str) -> None:
        from app.ui.theme import normalize_theme_mode
        theme_name = normalize_theme_mode(theme_name)
        self._settings_service.set_theme(theme_name)
        self._apply_theme(theme_name)

    def _apply_theme(self, theme_name: str) -> None:
        if getattr(self, "_is_applying_theme", False):
            return
        self._is_applying_theme = True
        try:
            from app.ui.theme import get_stylesheet, is_system_dark_mode, normalize_theme_mode
            theme_name = normalize_theme_mode(theme_name)
            is_dark = theme_name == "Dark" or (theme_name == "System" and is_system_dark_mode())
            stylesheet = get_stylesheet(is_dark)
            app = QApplication.instance()
            if isinstance(app, QApplication):
                app.setStyleSheet(stylesheet)
            else:
                self.setStyleSheet(stylesheet)
        finally:
            self._is_applying_theme = False

    def changeEvent(self, event) -> None:
        if event.type() == QEvent.Type.PaletteChange:
            if not getattr(self, "_is_applying_theme", False) and hasattr(self, "theme_combo"):
                if self.theme_combo.currentText() == "System":
                    self._apply_theme("System")
        super().changeEvent(event)

    # ── Palette ─────────────────────────────────────────────────────────────

    def _load_input_palette(self, file_path: str) -> None:
        self.is_palette_pick_mode = False
        self.original_view.setPickColorEnabled(False)
        self.pick_palette_button.setChecked(False)
        self.pick_palette_button.setText("Pick Color From Image")
        self.palette_replacements.clear()
        self._controller.vector_settings.palette_replacements = []
        try:
            self.palette_colors = extract_dominant_colors(file_path, max_colors=10)
            self.palette_hint_label.setText("Click a color to replace it in the vector output.")
        except Exception as error:
            self.palette_colors = []
            self.palette_hint_label.setText(f"Palette unavailable: {error}")
        self._update_palette_display()

    def _update_palette_display(self) -> None:
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
            button.setToolTip(f"{source_hex} → {replacement_hex}" if source_color in self.palette_replacements else source_hex)
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
            self.palette_grid.addWidget(button, index // 5, index % 5)
            self.palette_buttons.append(button)

    def _choose_palette_replacement(self, source_color: ColorRGB) -> None:
        current_color = self.palette_replacements.get(source_color, source_color)
        selected = QColorDialog.getColor(QColor(*current_color), self, f"Replace {color_to_hex(source_color)}")
        if not selected.isValid():
            return
        replacement = (selected.red(), selected.green(), selected.blue())
        if replacement == source_color:
            self.palette_replacements.pop(source_color, None)
        else:
            self.palette_replacements[source_color] = replacement
        self._controller.vector_settings.palette_replacements = list(self.palette_replacements.items())
        self._update_palette_display()
        self.statusBar().showMessage(f"Palette color updated: {color_to_hex(source_color)} → {color_to_hex(replacement)}")
        self._run_vectorization()

    def _toggle_palette_pick_mode(self, checked: bool) -> None:
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
        if source_color in self.palette_colors:
            self.palette_colors.remove(source_color)
        self.palette_colors.insert(0, source_color)
        self.palette_colors = self.palette_colors[:10]
        self._update_palette_display()

    def _reset_palette_replacements(self) -> None:
        if not self.palette_replacements:
            return
        self.palette_replacements.clear()
        self._controller.vector_settings.palette_replacements = []
        self._update_palette_display()
        self.statusBar().showMessage("Palette color changes reset.")
        self._run_vectorization()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _set_preset_custom(self) -> None:
        if not self._updating_from_preset and hasattr(self, "preset_combo"):
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentText("Custom")
            self.preset_combo.blockSignals(False)

    def _render_vector_result(self, vector_result: VectorResult) -> QImage:
        """Draw vector paths on a QImage (or overlay on the original image)."""
        from app.core.vectorizer_backend import VTracerVectorResult
        overlay = hasattr(self, "overlay_checkbox") and self.overlay_checkbox.isChecked() and not self.original_pixmap.isNull()

        if isinstance(vector_result, VTracerVectorResult):
            width = max(vector_result.image_width, 1)
            height = max(vector_result.image_height, 1)
            if overlay:
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
                width, height = self.current_image_info.width, self.current_image_info.height
            else:
                width, height = 400, 400

        if overlay:
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
                painter_path.addPolygon(QPolygon([QPoint(int(pt[0]), int(pt[1])) for pt in points]))
                for hole in path.holes:
                    painter_path.addPolygon(QPolygon([QPoint(int(pt[0]), int(pt[1])) for pt in hole]))
                painter.drawPath(painter_path)
        finally:
            painter.end()
        return image

    def _update_metadata_display(self, info: ImageInfo) -> None:
        self.meta_labels["File"].setText(info.file_name)
        self.meta_labels["Size"].setText(info.file_size_display)
        self.meta_labels["Resolution"].setText(info.resolution_display)
        self.meta_labels["Format"].setText(info.image_format)
        self.meta_labels["Color Mode"].setText(info.color_mode)

    def _clear_processing_result(self) -> None:
        self._controller.state.thresholded_array = None
        self._controller.state.vector_result = None
        self.processed_pixmap = QPixmap()
        self.raster_view.setImage(QPixmap())
        self.result_view.setImage(QPixmap())
        self.export_button.setEnabled(False)

    def _update_preview_image(self) -> None:
        if not self.original_pixmap.isNull():
            self.original_view.setImage(self.original_pixmap)
        self._update_result_image()

    def _update_result_image(self) -> None:
        if not self.processed_pixmap.isNull():
            self.result_view.setImage(self.processed_pixmap)

    def _update_zoom_label(self, zoom_level: float) -> None:
        self.zoom_label.setText(f"Zoom: {int(zoom_level * 100)}%")

    def _fit_to_screen(self) -> None:
        if not self.original_pixmap.isNull():
            view_size = self.original_view.viewport().size()
            pix_size = self.original_pixmap.size()
            if pix_size.width() > 0 and pix_size.height() > 0:
                zoom = min(view_size.width() / pix_size.width(), view_size.height() / pix_size.height()) * 0.95
                self.original_view.applyZoom(zoom)
                self.result_view.applyZoom(zoom)
                self.raster_view.applyZoom(zoom)
                self._update_zoom_label(zoom)

    def _actual_size(self) -> None:
        self.original_view.applyZoom(1.0)
        self.result_view.applyZoom(1.0)
        self.raster_view.applyZoom(1.0)
        self._update_zoom_label(1.0)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
