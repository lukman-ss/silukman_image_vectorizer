# CI/CD Automation

Last updated: 2026-06-05

There is no CI/CD service configured in this repository yet. This document
defines the expected local automation gates before a release.

## Local Verification Gates

```bash
.venv/bin/python -m py_compile main.py scripts/run_dev.py app/main_window.py
.venv/bin/python -m py_compile app/config/settings.py app/core/vectorizer_backend.py
.venv/bin/python -m py_compile app/services/*.py
```

## Smoke Run

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python main.py
```

## Build Gate

```bash
.venv/bin/python scripts/build_app.py
```

## Future CI Candidate Steps

- Install Python dependencies.
- Run compile checks.
- Run palette extraction regression.
- Run sample vectorization benchmark.
- Build PyInstaller package per platform.
