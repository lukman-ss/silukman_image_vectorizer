# Implementation Status

Last updated: 2026-06-05

## Status Summary

The application is functional as a local desktop vectorization tool.

## Available Features

- Import raster image.
- Validate supported formats.
- Display original image and metadata.
- Preview thresholded raster.
- Preview vectorized result.
- Select VTracer or OpenCV Legacy backend.
- Tune vector settings.
- Edit color palette from dominant colors or picked source pixels.
- Export single SVG.
- Batch-process multiple SVG exports.
- Switch light/dark/system theme.
- Build local packaged app with PyInstaller.

## Known Tradeoffs

- Photo-like inputs can generate very large SVG files.
- Dense spline output improves curves but increases point count and SVG size.
- Palette replacement works best for flat artwork and clean color regions.
