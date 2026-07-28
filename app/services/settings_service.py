"""Service for reading and writing persistent application settings."""
from __future__ import annotations

from PySide6.QtCore import QSettings


class SettingsService:
    """Wraps QSettings to persist user preferences across sessions."""

    def __init__(self) -> None:
        self._settings = QSettings("MyCompany", "ImageVectorizer")

    def get_theme(self, default: str = "System") -> str:
        return str(self._settings.value("theme", default))

    def set_theme(self, theme_name: str) -> None:
        self._settings.setValue("theme", theme_name)

    def get_last_input_dir(self, default: str = "") -> str:
        return str(self._settings.value("last_input_dir", default))

    def set_last_input_dir(self, path: str) -> None:
        self._settings.setValue("last_input_dir", path)

    def get_last_output_dir(self, default: str = "") -> str:
        return str(self._settings.value("last_output_dir", default))

    def set_last_output_dir(self, path: str) -> None:
        self._settings.setValue("last_output_dir", path)
