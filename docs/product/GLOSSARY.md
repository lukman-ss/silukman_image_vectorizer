# Glossary

Last updated: 2026-06-05

- Raster: Pixel-based image such as PNG or JPG.
- Vector: Shape/path-based image format such as SVG.
- SVG: Scalable Vector Graphics output file.
- VTracer: Rust-based vectorization engine used as the primary backend.
- OpenCV Legacy: Contour-based fallback vectorization backend.
- Palette: A set of dominant colors detected from the input image.
- Palette replacement: A source color to replacement color mapping.
- Path count: Number of SVG paths generated.
- Point count: Estimated number of coordinate points in SVG path data.
- Background removal: Preprocessing that makes background pixels transparent.
- Atomic write: Writing to a temporary file before replacing the target file.
