# Pipeline Architecture

Last updated: 2026-06-05

## Single Image Pipeline

1. User imports an image.
2. `load_image()` validates and loads a `QPixmap` and `ImageInfo`.
3. `process_image_pipeline()` creates grayscale and thresholded previews.
4. `VectorizationThread` snapshots the current settings.
5. `VTracerVectorizerBackend` runs first when available.
6. OpenCV Legacy is used when selected or as fallback.
7. `_render_vector_result()` renders the output in the UI.
8. `export_svg()` writes SVG output.

## Batch Pipeline

1. User selects multiple images.
2. `validate_batch_files()` checks extensions and decoded content.
3. User chooses an output folder.
4. `BatchProcessingThread` calls `process_batch()`.
5. Each valid image is vectorized and exported independently.
6. Failed files are recorded without stopping the batch.

## Color Palette Pipeline

1. `extract_dominant_colors()` detects up to 10 source colors from the input.
2. User picks a dominant swatch or source pixel from the preview.
3. User selects a replacement color.
4. Replacement pairs are stored in `VectorizationSettings.palette_replacements`.
5. `apply_palette_replacements()` changes source pixels during backend
   preprocessing.
6. The updated image is vectorized again.
