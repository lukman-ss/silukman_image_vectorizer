# Image Vectorizer Documentation

Last updated: 2026-06-05

This documentation covers the current Image Vectorizer desktop application:
PySide6 UI, raster image import, VTracer/OpenCV vectorization, SVG export,
batch processing, color palette editing, benchmarking, and packaging.

## Structure

- `architecture/` describes application modules, data models, UI boundaries,
  and processing pipeline flow.
- `developer/` contains setup, build, release, benchmark, and verification
  guides.
- `product/` captures project overview, glossary, status, checklist, ideas,
  and roadmap.
- `user/` explains UI workflow, local operation, performance tips, and
  troubleshooting.
- `assets/` documents visual assets used by docs and app resources.

## Key Runtime Flows

- Import raster image.
- Preview original image and processed/vectorized result side by side.
- Tune vectorization quality with presets and hand-picked settings.
- Edit output colors through dominant palette swatches or source-image color
  picking.
- Export single SVG or batch-process multiple images.
