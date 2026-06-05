# Dataset Benchmarking

Last updated: 2026-06-05

## Benchmark Folders

- `samples/flat_2d_benchmark/`
- `samples/flat_2d_benchmark_result/`
- `samples/color_benchmark/`
- `samples/color_benchmark_result/`

## Flat 2D Benchmark

Use this benchmark for logos, icons, stickers, badges, and character artwork.

Expected behavior:

- Low path count for simple shapes.
- Clean fills.
- Minimal dirty speckles.
- Smooth curves when VTracer mode is `spline`.
- Reasonable SVG size.

## Photo/Color Benchmark

Use this benchmark to stress-test high color complexity.

Expected behavior:

- Larger SVG files.
- Higher path counts.
- Better visual similarity with `color_precision = 8`.
- Clear warning to users when SVG complexity is high.

## Metrics

- SVG file size.
- Path count.
- Estimated point count.
- Mean absolute pixel error from rendered SVG preview.
- Histogram correlation between input preview and rendered output.
