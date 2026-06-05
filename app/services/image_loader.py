"""Image loading service for reading and validating image files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6.QtGui import QImage, QImageReader, QPixmap


# ---------------------------------------------------------------------------
# Data model for image information
# ---------------------------------------------------------------------------

@dataclass
class ImageInfo:
    """Simple data object holding metadata for a loaded image."""

    file_path: str
    file_name: str
    file_size_bytes: int
    width: int
    height: int
    image_format: str
    color_mode: str

    @property
    def file_size_display(self) -> str:
        """Return human-readable file size."""
        size = self.file_size_bytes
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    @property
    def resolution_display(self) -> str:
        return f"{self.width} × {self.height} px"


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
SUPPORTED_IMAGE_FORMATS = {"PNG", "JPEG", "BMP", "WEBP"}


def load_image(file_path: str) -> tuple[Optional[QPixmap], Optional[ImageInfo], Optional[str]]:
    """Load and validate an image file.

    Returns:
        (pixmap, image_info, error_message)
        On success: (QPixmap, ImageInfo, None)
        On failure: (None, None, error_message)
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    if ext not in SUPPORTED_FORMATS:
        return None, None, f"Unsupported format '{ext}'. Accepted: PNG, JPG, JPEG, BMP, WEBP."
    if not path.exists() or not path.is_file():
        return None, None, "Image file does not exist."

    reader = QImageReader(str(path))
    reader.setDecideFormatFromContent(True)
    if not reader.canRead():
        return None, None, f"Cannot read image: {reader.errorString()}"

    image_format = bytes(reader.format()).decode("ascii", errors="ignore").upper()
    if image_format not in SUPPORTED_IMAGE_FORMATS:
        return None, None, (
            f"Unsupported image content format '{image_format or 'Unknown'}'. "
            "Accepted: PNG, JPG, JPEG, BMP, WEBP."
        )

    image = reader.read()
    if image.isNull():
        return None, None, "Failed to load image data. The file may be corrupt."
    pixmap = QPixmap.fromImage(image)

    file_name = path.name
    try:
        file_size = path.stat().st_size
    except OSError:
        file_size = 0

    width = image.width()
    height = image.height()
    color_mode = _detect_color_mode(image)

    info = ImageInfo(
        file_path=str(path),
        file_name=file_name,
        file_size_bytes=file_size,
        width=width,
        height=height,
        image_format=image_format,
        color_mode=color_mode,
    )

    return pixmap, info, None


def _detect_color_mode(image: QImage) -> str:
    """Detect the displayed image color mode from decoded pixel data."""
    grayscale_formats = {
        QImage.Format.Format_Mono,
        QImage.Format.Format_MonoLSB,
        QImage.Format.Format_Grayscale8,
        QImage.Format.Format_Grayscale16,
    }
    if image.format() in grayscale_formats:
        return "Grayscale"
    if image.format() == QImage.Format.Format_Indexed8 and image.isGrayscale():
        return "Grayscale"
    if image.hasAlphaChannel():
        return "RGBA"
    return "RGB"
