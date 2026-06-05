# Ideas And Research

Last updated: 2026-06-05

## Current Research Notes

- VTracer produces better high-fidelity color tracing than the OpenCV contour
  fallback.
- Flat 2D artwork benefits from clean inputs without shadows or blurred edges.
- Dense spline output improves point-to-point smoothness but increases SVG size.
- Photo-like inputs need high color precision for visual similarity but produce
  large files.

## Candidate Improvements

- Adjustable palette replacement tolerance.
- Per-color palette replacement preview before re-vectorizing.
- Swatch labels with usage percentage.
- SVG complexity estimator before export.
- Optional simplification pass after VTracer output.
