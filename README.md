# Image Vectorizer

Last updated: 2026-06-05

Image Vectorizer is a Python and PySide6 desktop application foundation for
working with raster images. The current application supports local image import,
original and processed previews, image metadata display, and an initial
grayscale and threshold processing pipeline. It can also detect, simplify, and
preview color-aware vector paths using configurable quality, background removal,
and comparison controls. The desktop UI supports accessible Light, Dark, and
System theme modes, single SVG export, and responsive batch SVG processing.

## Install Dependencies

```bash
python -m pip install -r requirements.txt
```

## Run

From the project root:

```bash
python main.py
```

Or use the development runner:

```bash
python scripts/run_dev.py
```

## Build & Packaging

To bundle the application into a standalone desktop executable for distribution:

### On Windows
```cmd
.venv\Scripts\python scripts\build_app.py
```

### On macOS / Linux
```bash
.venv/bin/python scripts/build_app.py
```

The script will automatically handle:
1. Cleaning previous build output folders.
2. Generating a clean build using the configuration from `image_vectorizer.spec`.
3. Creating the standalone package in the `dist/` directory.
4. Auto-detecting the application icon in `app/resources` using the native
   platform icon format when available.
5. Running a post-build cleanup on temporary compilation artifacts.
6. Using PyInstaller from `.venv` or the system PATH.

## Documentation

Project documentation is available in `docs/`.

- `docs/architecture/` for system and pipeline architecture.
- `docs/developer/` for setup, verification, benchmark, and packaging guides.
- `docs/product/` for project overview, glossary, status, and roadmap.
- `docs/user/` for UI workflow, performance tips, and troubleshooting.
