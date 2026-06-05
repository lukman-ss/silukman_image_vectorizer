# Compilation Release Guide

Last updated: 2026-06-05

## Release Preparation

1. Verify `APP_VERSION` in `app/core/constants.py`.
2. Run compile checks.
3. Run sample benchmark checks.
4. Build PyInstaller package.
5. Smoke test packaged executable.
6. Review `CHANGELOG.md`.

## Version Metadata

`image_vectorizer.spec` reads `APP_VERSION` from
`app/core/constants.py` for macOS bundle metadata.

## Smoke Test Packaged App

```bash
QT_QPA_PLATFORM=offscreen "./dist/Image Vectorizer/Image Vectorizer"
```

On macOS app bundle:

```bash
QT_QPA_PLATFORM=offscreen "./dist/Image Vectorizer.app/Contents/MacOS/Image Vectorizer"
```
