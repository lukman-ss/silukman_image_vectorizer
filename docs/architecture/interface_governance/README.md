# Interface Governance

Last updated: 2026-06-05

This document defines the UI interaction boundaries for Image Vectorizer.

## Primary Panels

- Left sidebar:
  - Import image.
  - Export SVG.
  - Select batch images.
  - Process batch.
- Center preview:
  - Original image.
  - Vectorized result.
  - Thresholded raster preview.
  - Synchronized zoom and pan.
- Right control panel:
  - Metadata.
  - Input color palette.
  - Quality preset.
  - Engine selector.
  - Hand-pick settings.
  - Theme selector.

## Palette Editing

- The dominant palette is extracted from the input image, not from the SVG.
- The app displays up to 10 dominant colors.
- A swatch click opens a color picker for replacing that source color.
- The eyedropper mode lets the user click a source pixel directly in the
  original preview.
- Palette changes re-run vectorization and apply to VTracer and OpenCV Legacy
  backends.

## UI Safety

- Export is disabled when there is no valid vector result.
- Invalid image files show a blocking error dialog.
- Long processing runs in worker threads.
- Theme changes must not alter image or SVG render data.
