# Verification Guide

Last updated: 2026-06-05

## Compile Check

```bash
.venv/bin/python -m py_compile main.py scripts/run_dev.py
.venv/bin/python -m py_compile app/main_window.py app/config/settings.py
.venv/bin/python -m py_compile app/core/*.py app/services/*.py app/ui/*.py
```

## Source Smoke Test

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python main.py
```

## Development Runner Smoke Test

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/run_dev.py
```

## Palette Regression

Use `samples/flat_2d_benchmark/03_mobile_app_icon.png`.

Expected:

- `extract_dominant_colors()` returns 10 colors.
- A picked pixel can be stored as source color.
- A replacement pair updates `VectorizationSettings.palette_replacements`.
- Exported SVG contains the replacement color.

## Batch Regression

Run batch processing on `samples/flat_2d_benchmark/`.

Expected:

- 10 successful SVG files.
- No failed files.
- Output naming pattern: `<input_stem>_vectorized.svg`.
