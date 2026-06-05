# Changelog

All notable changes to this project will be documented in this file.

## [1.0.2] - 2026-06-05

### Changed
- Retrigger PyPI publishing with a fresh release tag after repository secret validation.

## [1.0.1] - 2026-06-05

### Added
- PyPI package deployment metadata and publishing workflow.
- Console entry point for launching the desktop application from installed packages.
- Package validation flow for source distribution and wheel artifacts.

## [1.0.0] - 2026-06-04

### Added
- Standalone packaging support using PyInstaller.
- Automation build script in `scripts/build_app.py` with automatic clean-up of temporary build directories and application icon auto-detection.
- Fully modular application entry point in `main.py` and PyInstaller configuration in `image_vectorizer.spec`.
- Robust path management helper dynamically detecting PyInstaller runtime (`sys.frozen` and `sys._MEIPASS`).
- GUI error handling via QMessageBox critical dialog on startup failure or missing dependencies.
- Application version displaying version (`v1.0.0`) in the main window title bar.
- Quality presets (Logo, Photo, Artwork, Icon) with custom parameter mapping (including VTracer settings: color mode, layers, modes, and layer difference tolerance).
- Vectorization backend switcher allowing users to choose between VTracer and legacy OpenCV engines.
- Accessible Light, Dark, and System theme modes.
