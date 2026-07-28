"""Custom QGraphicsView with synchronized zoom/pan and color-pick support."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView


class SyncGraphicsView(QGraphicsView):
    """Custom graphics view supporting panning, zooming, and scroll synchronization."""

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

        self.horizontalScrollBar().valueChanged.connect(self._on_scroll)
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)

    def setImage(self, pixmap: QPixmap) -> None:
        self.pixmap_item.setPixmap(pixmap)
        self.scene().setSceneRect(self.pixmap_item.boundingRect())

    def setPickColorEnabled(self, enabled: bool) -> None:
        """Enable or disable click-to-pick mode."""
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
                self.verticalScrollBar().value(),
            )

    def syncScroll(self, h_val: int, v_val: int) -> None:
        self._block_signals = True
        self.horizontalScrollBar().setValue(h_val)
        self.verticalScrollBar().setValue(v_val)
        self._block_signals = False
