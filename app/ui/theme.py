"""Centralized UI Theme management for Light, Dark, and System modes.

Provides color tokens, system dark mode detection, and global QSS stylesheet generation.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QPalette


THEME_MODES = ("System", "Light", "Dark")


@dataclass(frozen=True)
class ColorPalette:
    """Color tokens representing the design system."""
    bg_main: str
    bg_panel: str
    bg_input: str
    text_primary: str
    text_secondary: str
    border: str
    btn_primary: str
    btn_primary_hover: str
    btn_text: str
    btn_disabled_bg: str
    btn_disabled_text: str
    success: str
    error: str


# Premium Dark Mode Theme Palette
DARK_PALETTE = ColorPalette(
    bg_main="#121214",
    bg_panel="#1e1e24",
    bg_input="#2a2a35",
    text_primary="#ffffff",
    text_secondary="#a0a0b2",
    border="#2d2d3a",
    btn_primary="#2563eb",
    btn_primary_hover="#1d4ed8",
    btn_text="#ffffff",
    btn_disabled_bg="#2d2d3a",
    btn_disabled_text="#64748b",
    success="#34d399",
    error="#f87171",
)

# Premium Light Mode Theme Palette
LIGHT_PALETTE = ColorPalette(
    bg_main="#f8fafc",
    bg_panel="#ffffff",
    bg_input="#f1f5f9",
    text_primary="#0f172a",
    text_secondary="#64748b",
    border="#e2e8f0",
    btn_primary="#2563eb",
    btn_primary_hover="#1d4ed8",
    btn_text="#ffffff",
    btn_disabled_bg="#e2e8f0",
    btn_disabled_text="#94a3b8",
    success="#047857",
    error="#b91c1c",
)


def is_system_dark_mode() -> bool:
    """Detect system dark mode, falling back to palette luminance."""
    application = QGuiApplication.instance()
    if application is None:
        return False

    try:
        color_scheme = application.styleHints().colorScheme()
        if color_scheme != Qt.ColorScheme.Unknown:
            return color_scheme == Qt.ColorScheme.Dark
    except (AttributeError, RuntimeError):
        pass

    background = application.palette().color(
        QPalette.ColorGroup.Active,
        QPalette.ColorRole.Window,
    )
    luma = 0.299 * background.red() + 0.587 * background.green() + 0.114 * background.blue()
    return luma < 128


def normalize_theme_mode(theme_name: str) -> str:
    """Return a supported theme mode or the System fallback."""
    return theme_name if theme_name in THEME_MODES else "System"


def get_stylesheet(dark_mode: bool) -> str:
    """Generate global QSS stylesheet based on the active theme mode."""
    p = DARK_PALETTE if dark_mode else LIGHT_PALETTE

    return f'''
    /* Global Application Background */
    QMainWindow, QDialog {{
        background-color: {p.bg_main};
    }}

    /* Base Widgets */
    QWidget {{
        color: {p.text_primary};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        font-size: 12px;
    }}

    /* Panels & Cards */
    #panel {{
        background-color: {p.bg_panel};
        border: 1px solid {p.border};
        border-radius: 8px;
    }}

    #panel QLabel {{
        color: {p.text_primary};
    }}

    /* Section Labels */
    QLabel {{
        color: {p.text_primary};
    }}

    /* Secondary/Info Labels */
    QLabel[secondary="true"] {{
        color: {p.text_secondary};
    }}

    QLabel[state="success"] {{
        color: {p.success};
    }}

    QLabel[state="error"] {{
        color: {p.error};
    }}

    QGroupBox {{
        background-color: {p.bg_panel};
        border: 1px solid {p.border};
        border-radius: 6px;
        margin-top: 10px;
        padding: 10px 6px 6px 6px;
        font-weight: bold;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: {p.text_primary};
        background-color: {p.bg_panel};
    }}

    QFrame, QScrollArea {{
        background-color: {p.bg_panel};
        border: 1px solid {p.border};
        color: {p.text_primary};
    }}

    /* Buttons */
    QPushButton {{
        background-color: {p.btn_primary};
        color: {p.btn_text};
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: bold;
    }}

    QPushButton:hover {{
        background-color: {p.btn_primary_hover};
    }}

    QPushButton:pressed {{
        background-color: {p.btn_primary};
    }}

    QPushButton:disabled {{
        background-color: {p.btn_disabled_bg};
        color: {p.btn_disabled_text};
        border: 1px solid {p.border};
    }}

    /* Controls Inputs */
    QLineEdit, QComboBox {{
        background-color: {p.bg_input};
        color: {p.text_primary};
        border: 1px solid {p.border};
        border-radius: 5px;
        padding: 6px 8px;
        selection-background-color: {p.btn_primary};
        selection-color: {p.btn_text};
    }}

    QLineEdit:disabled, QComboBox:disabled {{
        background-color: {p.btn_disabled_bg};
        color: {p.btn_disabled_text};
    }}

    QComboBox QAbstractItemView {{
        background-color: {p.bg_panel};
        color: {p.text_primary};
        border: 1px solid {p.border};
        selection-background-color: {p.btn_primary};
        selection-color: {p.btn_text};
    }}

    QCheckBox {{
        color: {p.text_primary};
        spacing: 7px;
    }}

    QCheckBox::indicator {{
        width: 15px;
        height: 15px;
        background-color: {p.bg_input};
        border: 1px solid {p.border};
        border-radius: 3px;
    }}

    QCheckBox::indicator:checked {{
        background-color: {p.btn_primary};
        border-color: {p.btn_primary_hover};
    }}

    QSlider::groove:horizontal {{
        border: 1px solid {p.border};
        height: 6px;
        background: {p.bg_input};
        margin: 2px 0;
        border-radius: 3px;
    }}

    QSlider::handle:horizontal {{
        background: {p.btn_primary};
        border: none;
        width: 14px;
        height: 14px;
        margin: -4px 0;
        border-radius: 7px;
    }}

    QSlider::handle:horizontal:hover {{
        background: {p.btn_primary_hover};
    }}

    QListWidget {{
        background-color: {p.bg_input};
        border: 1px solid {p.border};
        border-radius: 6px;
        padding: 4px;
        outline: 0;
    }}

    QListWidget::item {{
        padding: 6px 8px;
        border-radius: 4px;
        color: {p.text_primary};
    }}

    QListWidget::item:hover {{
        background-color: {p.border};
    }}

    QListWidget::item:selected {{
        background-color: {p.btn_primary};
        color: {p.btn_text};
    }}

    QTabWidget::pane {{
        background-color: {p.bg_panel};
        border: 1px solid {p.border};
        border-radius: 6px;
    }}

    QTabBar::tab {{
        background-color: {p.bg_input};
        color: {p.text_secondary};
        border: 1px solid {p.border};
        padding: 7px 12px;
    }}

    QTabBar::tab:selected {{
        background-color: {p.bg_panel};
        color: {p.text_primary};
    }}

    QGraphicsView {{
        background-color: {p.bg_input};
        border: 1px solid {p.border};
        border-radius: 5px;
    }}

    QToolTip {{
        background-color: {p.bg_panel};
        color: {p.text_primary};
        border: 1px solid {p.border};
        padding: 4px;
    }}

    /* Status Bar */
    QStatusBar {{
        background-color: {p.bg_panel};
        border-top: 1px solid {p.border};
        color: {p.text_secondary};
    }}

    QStatusBar QLabel {{
        color: {p.text_secondary};
    }}
    '''
