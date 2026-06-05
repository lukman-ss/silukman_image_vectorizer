# Quality Metrics

Last updated: 2026-06-05

## Visual Similarity

Rendered SVG previews can be compared against input raster previews with:

- Mean absolute error.
- Root mean squared error.
- Per-channel histogram correlation.

## Vector Complexity

Track:

- Path count.
- Estimated point count.
- SVG file size.
- Render validity through `QSvgRenderer.isValid()`.

## UI Quality

Track:

- App starts without crashing.
- Long-running vectorization keeps the UI responsive.
- Export is disabled when no valid vector result exists.
- Theme changes do not affect image render output.

## Palette Editing Quality

Track:

- Dominant palette returns up to 10 colors.
- Picked source pixel enters palette correctly.
- Replacement color appears in exported SVG.
- Reset removes all replacement mappings.
