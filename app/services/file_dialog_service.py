"""Service for opening file/directory dialog windows."""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QFileDialog, QWidget

IMAGE_FILTER = "Image Files (*.png *.jpg *.jpeg *.bmp *.webp)"
SVG_FILTER = "SVG Files (*.svg)"


class FileDialogService:
    """Provides file dialog operations. Does not store widget references."""

    def open_image_file(
        self, parent: Optional[QWidget] = None, initial_dir: str = ""
    ) -> Optional[str]:
        """Open single image file dialog. Returns selected path or None."""
        path, _ = QFileDialog.getOpenFileName(parent, "Select Image", initial_dir, IMAGE_FILTER)
        return path if path else None

    def open_image_files(
        self, parent: Optional[QWidget] = None, initial_dir: str = ""
    ) -> list[str]:
        """Open multi-image file dialog. Returns list of selected paths."""
        paths, _ = QFileDialog.getOpenFileNames(
            parent, "Select Batch Images", initial_dir, IMAGE_FILTER
        )
        return paths

    def save_svg_file(
        self,
        parent: Optional[QWidget] = None,
        initial_path: str = "",
    ) -> Optional[str]:
        """Open save SVG dialog. Returns target path or None."""
        path, _ = QFileDialog.getSaveFileName(parent, "Export SVG", initial_path, SVG_FILTER)
        return path if path else None

    def select_directory(
        self, parent: Optional[QWidget] = None, initial_dir: str = ""
    ) -> Optional[str]:
        """Open folder selection dialog. Returns selected directory or None."""
        path = QFileDialog.getExistingDirectory(
            parent, "Select Output Folder for Batch SVG Export", initial_dir
        )
        return path if path else None
