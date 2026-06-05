# Developer Setup

Last updated: 2026-06-05

## Requirements

- Python 3.9 or newer.
- Local virtual environment recommended.
- Dependencies from `requirements.txt`.

## Install

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

On Windows:

```cmd
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

## Run

```bash
.venv/bin/python main.py
```

Or:

```bash
.venv/bin/python scripts/run_dev.py
```

## Development Notes

- Keep UI code in `app/main_window.py`.
- Put reusable processing logic in `app/core/`.
- Put file IO and service logic in `app/services/`.
- Do not block the UI thread for image processing, vectorization, or batch work.
