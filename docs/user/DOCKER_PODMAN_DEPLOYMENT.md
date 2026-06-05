# Docker And Podman Deployment

Last updated: 2026-06-05

Image Vectorizer is a desktop GUI application and is not currently designed for
container deployment.

## Recommendation

Run the application directly on the desktop OS using Python or the packaged
PyInstaller build.

## Why Containers Are Not The Default

- PySide6 GUI forwarding is platform-specific.
- File dialogs and native desktop integration are simpler outside containers.
- Packaging targets local desktop distribution rather than server deployment.
