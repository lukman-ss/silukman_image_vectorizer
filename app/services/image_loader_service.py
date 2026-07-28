"""Service adapter for loading images into the application."""

from __future__ import annotations

from typing import Optional, Tuple

from PySide6.QtGui import QPixmap

from app.services.image_loader import ImageInfo, load_image


class ImageLoaderService:
    """Thin adapter over the raw image_loader utility."""

    def load(self, file_path: str) -> Tuple[Optional[QPixmap], Optional[ImageInfo], Optional[str]]:
        """Load an image from disk.

        Returns:
            (pixmap, image_info, error_message) where error_message is None on success.
        """
        return load_image(file_path)
