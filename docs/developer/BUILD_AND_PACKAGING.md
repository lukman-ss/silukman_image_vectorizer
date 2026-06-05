# Build And Packaging

Last updated: 2026-06-05

Image Vectorizer uses PyInstaller for local desktop packaging.

## Build

macOS/Linux:

```bash
.venv/bin/python scripts/build_app.py
```

Windows:

```cmd
.venv\Scripts\python scripts\build_app.py
```

## Output

- `dist/Image Vectorizer/`
- `dist/Image Vectorizer.app` on macOS.

## Build Script Behavior

`scripts/build_app.py`:

- Cleans `build/` and `dist/`.
- Locates PyInstaller from `.venv` or system `PATH`.
- Runs `image_vectorizer.spec`.
- Cleans temporary build artifacts after success.

## Packaged Resources

The spec bundles:

- `app/resources/`
- `docs/`
- `LICENSE`
- PySide6 runtime dependencies.
- Image processing dependencies.
- VTracer dependency.
