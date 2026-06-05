import sys
from pathlib import Path


if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]

APP_DIR = PROJECT_ROOT / "app"
RESOURCES_DIR = APP_DIR / "resources"
DOCS_DIR = PROJECT_ROOT / "docs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
