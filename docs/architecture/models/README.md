# Data Models

Last updated: 2026-06-05

## ImageInfo

Defined in `app/services/image_loader.py`.

- `file_path`
- `file_name`
- `file_size_bytes`
- `width`
- `height`
- `image_format`
- `color_mode`

Used for metadata display, default export path generation, and processing
source references.

## VectorizationSettings

Defined in `app/config/settings.py`.

- Legacy OpenCV controls:
  - `min_area`
  - `approx_tolerance`
  - `smoothing_enabled`
  - `invert`
  - `threshold_val`
- Color and background controls:
  - `color_mode`
  - `color_count`
  - `preserve_edges`
  - `remove_background`
  - `bg_tolerance`
  - `palette_replacements`
- Backend selection:
  - `engine_type`
  - `vtracer`

## VTracerSettings

Defined in `app/config/settings.py`.

- `colormode`
- `hierarchical`
- `mode`
- `filter_speckle`
- `color_precision`
- `layer_difference`
- `corner_threshold`
- `length_threshold`
- `max_iterations`
- `path_precision`

## VectorPath And VectorResult

Defined in `app/core/vectorization_engine.py`.

`VectorPath` stores contour points, area, fill color, and holes.
`VectorResult` stores paths, image dimensions, point counts, and fallback
status.

## VTracerVectorResult

Defined in `app/core/vectorizer_backend.py`.

Wraps raw SVG produced by VTracer while preserving the `VectorResult` interface.
