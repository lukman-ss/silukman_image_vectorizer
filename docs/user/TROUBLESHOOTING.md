# Troubleshooting

Last updated: 2026-06-05

## Image Fails To Import

- Check the file extension.
- Supported formats are PNG, JPG, JPEG, BMP, and WEBP.
- The decoded image content must match a supported format.

## Vector Result Is Empty

- Lower `Min Area`.
- Adjust threshold when using OpenCV Legacy.
- Try disabling background removal.
- Try another preset.

## SVG Is Too Large

- Reduce custom color count.
- Increase `Min Area`.
- Use `Logo` or `Icon` preset instead of `Photo`.
- Use stronger simplification.

## Result Looks Dirty

- Remove shadows, blur, or noisy backgrounds from the input.
- Enable background removal for clean white/solid backgrounds.
- Increase speckle filtering through higher `Min Area`.

## Palette Replacement Does Not Affect Expected Area

- Pick the source color directly from the original image.
- Use cleaner flat-color input.
- The source color may be anti-aliased or blended with neighboring pixels.
