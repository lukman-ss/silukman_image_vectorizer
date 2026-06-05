# Hardware Acceleration

Last updated: 2026-06-05

Image Vectorizer currently runs local CPU-based processing.

## Current Behavior

- PySide6 handles UI rendering.
- OpenCV handles image preprocessing.
- VTracer handles primary vectorization.
- Worker threads keep the UI responsive but do not move computation to GPU.

## Performance Notes

- Large photos can be expensive to vectorize.
- Dense spline output increases CPU time and SVG size.
- Batch processing runs sequentially per selected image.
