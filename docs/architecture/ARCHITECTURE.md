# Architecture

Last updated: 2026-06-05

Image Vectorizer is a local desktop application built with Python and PySide6.
The app keeps UI orchestration in `app/main_window.py`, shared data and engine
logic in `app/core/`, and IO-oriented services in `app/services/`.

## Runtime Layers

- Entry points:
  - `main.py`
  - `scripts/run_dev.py`
- UI layer:
  - `app/main_window.py`
  - `app/ui/theme.py`
- Core layer:
  - `app/core/image_pipeline.py`
  - `app/core/vectorization_engine.py`
  - `app/core/vectorizer_backend.py`
  - `app/core/paths.py`
  - `app/core/constants.py`
- Service layer:
  - `app/services/image_loader.py`
  - `app/services/svg_exporter.py`
  - `app/services/batch_processor.py`
  - `app/services/color_palette.py`
- Configuration:
  - `app/config/settings.py`

## Processing Flow

1. The user imports a PNG/JPG/JPEG/BMP/WEBP image.
2. `image_loader` validates the file and returns preview metadata.
3. `image_pipeline` creates the thresholded raster preview for legacy paths.
4. `vectorizer_backend` selects VTracer or OpenCV Legacy.
5. Optional preprocessing applies background removal, color quantization, and
   palette replacements.
6. Vector output is rendered in the preview and stored in memory.
7. `svg_exporter` writes SVG through normalized paths and atomic writes.

## Responsiveness

Image processing, vectorization, and batch export run through worker threads.
The UI queues the latest request when a previous worker is still active, which
keeps controls responsive during expensive vectorization.

## Packaging

PyInstaller packaging is defined by `image_vectorizer.spec` and driven by
`scripts/build_app.py`. Frozen apps resolve resources through `app/core/paths.py`.
