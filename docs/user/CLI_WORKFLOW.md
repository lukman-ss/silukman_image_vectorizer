# CLI Workflow

Last updated: 2026-06-05

Image Vectorizer is primarily a desktop app. The command line is used for
running, verifying, and packaging the application.

## Run App

```bash
.venv/bin/python main.py
```

## Run Development Entry

```bash
.venv/bin/python scripts/run_dev.py
```

## Compile Check

```bash
.venv/bin/python -m py_compile app/main_window.py app/core/*.py app/services/*.py
```

## Build App

```bash
.venv/bin/python scripts/build_app.py
```
