# Phase 1 Architecture

Last updated: 2026-06-04

The Phase 1 architecture establishes a small PySide6 desktop application
foundation with clear module boundaries.

## Entry Points

- `main.py` creates the Qt application, opens the main window, and handles
  startup failures.
- `scripts/run_dev.py` provides a root-aware development runner.

## Application Modules

- `app/main_window.py` defines the initial desktop window and its base layout.
- `app/ui/` is the package boundary for user interface modules.
- `app/core/` contains shared constants and project path helpers.
- `app/services/` is the package boundary for application services.
- `app/config/` contains basic application settings.
- `app/resources/` is the package boundary for desktop application resources.

The initial window contains a left sidebar, central preview area, right control
panel, and bottom status bar. No application features are implemented in this
phase.

# Phase 2 Architecture

Phase 2 extends the desktop foundation with local image import, validation,
metadata display, original and processed previews, and an initial processing
pipeline.

## Image Import And Metadata

- `app/services/image_loader.py` validates both file extensions and decoded
  content formats, loads preview data, detects color mode from decoded pixels,
  and creates an `ImageInfo` data object.
- `app/main_window.py` opens the local file dialog and displays image metadata,
  validation errors, previews, controls, and status messages.

## Processing Pipeline

- `app/core/image_pipeline.py` loads an image through OpenCV, converts it to
  grayscale, validates and applies a binary threshold, and returns the
  processed preview.
- `ImageProcessorThread` in `app/main_window.py` runs processing outside the
  main UI thread and queues the latest threshold request while work is active.
- Importing a new image or encountering a processing error clears stale derived
  previews and vector state while preserving the imported original image.

# Phase 3 Architecture

Last updated: 2026-06-04

Phase 3 converts the binary processing result into in-memory vector path data
and renders detected paths in the processing result preview area.

## Vectorization Engine

- `app/core/vectorization_engine.py` defines vector path, vector result, and
  vectorization settings data models.
- The engine detects external contours, filters them by minimum area, optionally
  smooths or inverts the input, and simplifies paths using approximation
  tolerance.
- The engine normalizes numeric foreground input into a binary mask, rejects
  invalid pixel/settings values, and preserves transparent background masks.
- Vectorization results remain in application memory and can be consumed by
  preview or export features without writing files from the engine.

## Vectorization UI

- `app/main_window.py` provides controls for minimum area, approximation
  tolerance, smoothing, and invert detection.
- Vector previews update when processing completes or vectorization settings
  change.
- Background workers snapshot threshold data and settings so each result matches
  the request that started it.
- Status messages report successful vectorization, missing contours, and
  vectorization failures.

# Phase 4 Architecture

Last updated: 2026-06-04

Phase 4 exports in-memory vector results as SVG documents and supports
multi-image batch processing.

## SVG Export

- `app/services/svg_exporter.py` builds SVG markup, validates output paths,
  appends missing `.svg` extensions, and performs atomic file writes.
- Single-image export uses the shared exporter service and reports progress,
  success, or failure through the desktop UI.

## Batch Processing

- `app/services/batch_processor.py` validates selected images, runs the existing
  processing and vectorization pipeline, creates overwrite-safe filenames, and
  delegates SVG writing to the shared exporter service.
- `BatchProcessingThread` keeps batch work outside the UI thread and reports the
  current file, progress, success count, and failed count through signals.
- A failed file or progress callback does not stop the remaining batch.

# Phase 5 Architecture

Last updated: 2026-06-04

Phase 5 centralizes light, dark, and system-aware styling without changing image
or vector preview data.

## Theme System

- `app/ui/theme.py` defines shared color tokens, accessible light and dark
  palettes, system color-scheme detection, and global QSS generation.
- Theme QSS covers panels, labels, buttons, inputs, selectors, lists, tabs,
  preview views, status bars, frames, scroll areas, and group boxes.
- `app/main_window.py` persists the selected theme through `QSettings`, applies
  it globally to the application, and refreshes System mode when the platform
  palette changes.

# Phase 6 Architecture

Last updated: 2026-06-05

Phase 6 extends vectorization quality controls and preview comparison while
preserving the existing processing and SVG export flow.

## Quality Pipeline

- `VectorizationSettings` in `app/config/settings.py` stores advanced quality,
  color, edge preservation, and background removal options.
- `app/core/vectorization_engine.py` supports foreground-aware background
  removal, alpha transparency, safe color quantization, and contour grouping by
  detected custom color.
- Vector paths retain detected RGB fill colors for preview and SVG export.

## Responsive Preview

- Image processing and vectorization run in separate workers.
- Repeated settings changes queue the latest request instead of forcibly
  terminating active workers or blocking the UI thread.
- Original, vectorized, and thresholded raster previews remain separate and
  share synchronized zoom and pan controls.

# Phase 7 Architecture

Last updated: 2026-06-05

Phase 7 integrates the Rust-based VTracer engine as the primary vectorization backend while keeping the OpenCV Legacy engine as a fallback.

## Engine Abstraction & Backends

- `app/core/vectorizer_backend.py` introduces the `VectorizerBackend` interface and subclasses:
  - `OpenCVVectorizerBackend` encapsulates the legacy thresholding and contour-based vectorization.
  - `VTracerVectorizerBackend` integrates the Rust-based `vtracer` engine for high-fidelity color tracing.
- Subclassing `VectorResult` to `VTracerVectorResult` allows passing raw SVG strings produced by VTracer directly into the export and rendering pipeline.
- Thread-level fallback automatically handles `vtracer` failures by reverting to OpenCV Legacy and displaying a clear warning dialog detailing the error to the user.

## Native SVG Integration & Preprocessing

- `app/services/svg_exporter.py` natively supports `VTracerVectorResult` by writing raw SVG data atomically and enforcing `.svg` extension normalization.
- `app/services/batch_processor.py` supports the VTracer backend with automatic per-file fallback to OpenCV Legacy.
- UI previews render native VTracer SVGs using `QSvgRenderer` on a QPainter canvas.
- Color quantization preprocessing using K-Means is integrated into the VTracer backend to guarantee that the generated vector output strictly obeys the custom color limits set by the user.

## Configuration & Preset Settings

- `VTracerSettings` in `app/config/settings.py` isolates VTracer-specific configurations in a dedicated nested settings object.
- Presets (Logo, Artwork, Icon, Photo) are mapped to optimized VTracer parameters (e.g., Logo uses strong simplification and fewer colors, while Photo enables high color limits with pro-active user warnings about SVG complexity).
- Default VTracer curve fitting favors denser spline output for flat logos,
  icons, and character artwork while keeping user-facing simplification controls
  available for smaller SVG output.

# Phase 8 Architecture

Last updated: 2026-06-05

Phase 8 prepares the desktop application for local packaged distribution using
PyInstaller while preserving the existing application entry point and runtime
path helpers.

## Packaging Entry Point

- `main.py` remains the single application entry point for development and
  packaged builds.
- Startup now validates required packaged resources before opening the main
  window and reports missing dependencies or resources through a desktop error
  dialog when possible.
- `app/core/paths.py` resolves paths from `sys._MEIPASS` in frozen builds and
  from the project root during development.

## Build Configuration

- `image_vectorizer.spec` defines the PyInstaller bundle, bundled resources,
  hidden imports, application name, version metadata, and platform-specific
  icon usage.
- `app/resources/icon.icns` is generated from the existing PNG icon for macOS
  application bundles.
- `scripts/build_app.py` cleans build output, locates PyInstaller from the
  local virtual environment or system PATH on Windows, macOS, and Linux, then
  runs the shared spec file.

## Distribution Output

- Build artifacts are created in `dist/`.
- Temporary PyInstaller build artifacts are removed after a successful build.
- Required resources and documentation are bundled with the packaged app so it
  can run without depending on the source folder layout.
