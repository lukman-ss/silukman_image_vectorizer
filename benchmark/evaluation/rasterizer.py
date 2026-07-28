import os

import PySide6
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

# Force offscreen rendering for headless environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure there's a QCoreApplication instance available
_app = None
if QApplication.instance() is None:
    _app = QApplication([])


class SVGRasterizer:
    """
    Rasterizes SVG files back to pixel format for quality evaluation.

    Rationale for PySide6:
    We use PySide6.QtSvg because it is already a core dependency of the project.
    Alternative like CairoSVG would require installing native libcairo binaries
    which complicates the environment setup. Resvg is also excellent but requires
    a separate Python package. PySide6 is robust enough for our benchmark needs.
    """

    def __init__(self):
        self.backend_name = "PySide6.QtSvg"
        self.backend_version = PySide6.__version__

    def rasterize(
        self,
        svg_path: str,
        output_path: str,
        target_width: int,
        target_height: int,
        bg_color: tuple = (0, 0, 0, 0),
    ) -> dict:
        """
        Rasterizes the SVG to a PNG file.

        Args:
            svg_path: Path to input SVG.
            output_path: Path to output PNG.
            target_width: Desired output width.
            target_height: Desired output height.
            bg_color: RGBA tuple for the background color (default transparent).

        Returns:
            dict containing metadata about the rasterization process.
        """
        if not os.path.exists(svg_path):
            return {"success": False, "error": f"File not found: {svg_path}"}

        try:
            renderer = QSvgRenderer(svg_path)
            if not renderer.isValid():
                return {"success": False, "error": "Invalid SVG format or parsing failed."}

            # Create an image with ARGB32 to support alpha transparency
            image = QImage(target_width, target_height, QImage.Format.Format_ARGB32)

            # Consistent background handling
            r, g, b, a = bg_color
            image.fill(QColor(r, g, b, a))

            # Paint the SVG onto the image
            painter = QPainter(image)
            # Use high-quality antialiasing
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

            renderer.render(painter)
            painter.end()

            # Save as PNG
            saved = image.save(output_path, "PNG")

            if not saved:
                return {"success": False, "error": f"Failed to save image to {output_path}"}

            return {
                "success": True,
                "backend": self.backend_name,
                "backend_version": self.backend_version,
                "output_width": target_width,
                "output_height": target_height,
                "background_rgba": bg_color,
                "output_path": output_path,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
