# Phase 1 - Init Project Checklist

Last updated: 2026-06-04

- [x] Initialize the project structure directly in the current root.
- [x] Create the required application, documentation, and script directories.
- [x] Create the main entry point in `main.py`.
- [x] Create the main application window in `app/main_window.py`.
- [x] Create a basic PySide6 window titled `Image Vectorizer`.
- [x] Create the initial sidebar, preview area, control panel, and status bar layout.
- [x] Create basic application settings in `app/config/settings.py`.
- [x] Create application constants in `app/core/constants.py`.
- [x] Create root-based path helpers in `app/core/paths.py`.
- [x] Add the minimum dependencies to `requirements.txt`.
- [x] Add a Python desktop application `.gitignore`.
- [x] Add project description, dependency installation, and run instructions.
- [x] Create a checklist containing only Phase 1 tasks.
- [x] Document the initial Phase 1 architecture.
- [x] Create the development runner in `scripts/run_dev.py`.
- [x] Support startup through `python main.py` and `python scripts/run_dev.py`.
- [x] Add basic application startup error handling.
- [x] Keep the project free of testing frameworks.
- [x] Keep the project free of database, API, authentication, image processing, export, and non-desktop features.
- [x] Keep the project free of future-phase roadmap files.

# Phase 2 - Image Import, Preview & Processing Pipeline Checklist

Last updated: 2026-06-04

- [x] Add an `Import Image` button to the sidebar or control panel.
- [x] Create a file dialog for selecting a local image.
- [x] Limit accepted image formats to PNG, JPG, JPEG, BMP, and WEBP.
- [x] Validate image files before displaying them.
- [x] Display an error message when a file is invalid or cannot be opened.
- [x] Display the original image in the main preview area.
- [x] Create a separate preview area for the initial processing result.
- [x] Display image metadata:
  - [x] File name.
  - [x] File size.
  - [x] Image resolution.
  - [x] Image format.
  - [x] Color mode.
- [x] Create a dedicated image loading service, such as `app/services/image_loader.py`.
- [x] Create a simple model or data object for storing image information.
- [x] Create the initial image processing pipeline in `app/core/image_pipeline.py`.
- [x] Add grayscale processing as an initial pipeline stage.
- [x] Add simple threshold processing as an initial pipeline stage.
- [x] Add a simple threshold value control.
- [x] Update the processing result preview when the threshold value changes.
- [x] Keep the UI responsive while an image is processed.
- [x] Separate UI logic from processing logic for maintainability.
- [x] Add a status bar message when an image loads successfully.
- [x] Add a status bar message when processing completes successfully.
- [x] Document the Phase 2 checklist in `docs/checklist.md`.

# Phase 3 - Vectorization Engine Checklist

Last updated: 2026-06-04

* [x] Create a dedicated vectorization engine file in `app/core/vectorization_engine.py`.
* [x] Create a simple vector data model for storing detected paths or shapes.
* [x] Convert processed binary/threshold image into contours.
* [x] Filter small contours using minimum area configuration.
* [x] Add contour simplification using approximation tolerance.
* [x] Add basic smoothing option for detected contours.
* [x] Add invert detection option for dark/light image cases.
* [x] Add vectorization settings object for:

  * [x] Minimum area.
  * [x] Approximation tolerance.
  * [x] Smoothing enabled/disabled.
  * [x] Invert mode.
* [x] Connect the processed image result from Phase 2 into the vectorization engine.
* [x] Display vector preview in the existing processed preview area or a dedicated vector preview area.
* [x] Draw detected vector paths over a transparent or plain preview background.
* [x] Add UI controls for minimum area and approximation tolerance.
* [x] Update vector preview when vectorization settings change.
* [x] Add status bar message when vectorization completes successfully.
* [x] Add error handling when vectorization fails or no contour is detected.
* [x] Keep vectorization logic separate from UI logic.
* [x] Keep the vector result in memory only.
* [x] Document the Phase 3 checklist in `docs/checklist.md`.

# Phase 4 - SVG Export & Batch Processing Checklist

Last updated: 2026-06-04

* [x] Create a dedicated SVG export service in `app/services/svg_exporter.py`.
* [x] Create SVG document builder logic for converting internal vector paths into SVG markup.
* [x] Convert vector path data from Phase 3 into SVG `<path>` elements.
* [x] Preserve original image width and height as SVG canvas size.
* [x] Add SVG `viewBox` based on the original image resolution.
* [x] Add basic SVG metadata:
  * [x] App name.
  * [x] Export timestamp.
  * [x] Source image file name.
* [x] Add an `Export SVG` button in the UI.
* [x] Disable the export button when no vector result exists.
* [x] Create a file save dialog for choosing SVG output path.
* [x] Validate output filename and extension.
* [x] Automatically append `.svg` extension if missing.
* [x] Write SVG content safely to disk.
* [x] Show success message when SVG export completes.
* [x] Show error message when SVG export fails.
* [x] Add a status bar message during and after export.
* [x] Create a batch processing service in `app/services/batch_processor.py`.
* [x] Add a `Batch Processing` mode or section in the UI.
* [x] Allow users to select multiple image files.
* [x] Validate all selected image files before processing.
* [x] Display the selected batch file list in the UI.
* [x] Allow users to choose an output folder for batch SVG export.
* [x] Process each image through the existing image loading, processing, and vectorization pipeline.
* [x] Export each processed vector result as an individual `.svg` file.
* [x] Keep original filenames when generating SVG files.
* [x] Add safe filename handling to avoid overwriting existing files.
* [x] Display batch progress in the UI.
* [x] Display current file being processed.
* [x] Show batch success and failed counts after processing completes.
* [x] Add error handling for failed files without stopping the entire batch.
* [x] Keep SVG export logic separate from batch processing logic.
* [x] Keep batch processing logic separate from UI logic.
* [x] Document the Phase 4 checklist in `docs/checklist.md`.

# Phase 5 - UI Polish & Light/Dark Mode Safe Theme Checklist

Last updated: 2026-06-04

* [x] Audit semua warna UI yang hardcoded di aplikasi.
* [x] Buat sistem theme terpusat, misalnya `app/ui/theme.py`.
* [x] Definisikan color token untuk:
  * [x] Background utama.
  * [x] Background panel/sidebar.
  * [x] Background input/control.
  * [x] Text primary.
  * [x] Text secondary.
  * [x] Border.
  * [x] Button background.
  * [x] Button text.
  * [x] Disabled state.
  * [x] Error state.
  * [x] Success state.
* [x] Pastikan semua teks tetap terbaca di light mode.
* [x] Pastikan semua teks tetap terbaca di dark mode.
* [x] Hilangkan kombinasi warna bermasalah seperti text gelap di background gelap.
* [x] Hilangkan kombinasi warna bermasalah seperti text terang di background terang.
* [x] Terapkan stylesheet global PySide6 berbasis QSS.
* [x] Terapkan style aman untuk:
  * [x] QPushButton.
  * [x] QLabel.
  * [x] QSlider.
  * [x] QGroupBox.
  * [x] QFrame.
  * [x] QScrollArea.
  * [x] QStatusBar.
  * [x] QLineEdit.
  * [x] QListWidget atau table/list component jika ada.
* [x] Tambahkan deteksi mode sistem jika memungkinkan.
* [x] Tambahkan fallback theme jika deteksi mode sistem tidak tersedia.
* [x] Tambahkan opsi manual untuk memilih:
  * [x] Light mode.
  * [x] Dark mode.
  * [x] System mode.
* [x] Simpan pilihan theme ke konfigurasi aplikasi.
* [x] Apply theme saat aplikasi pertama kali dibuka.
* [x] Apply theme ulang saat user mengganti mode.
* [x] Pastikan preview image tidak terganggu oleh perubahan theme.
* [x] Pastikan panel metadata tetap terbaca di semua mode.
* [x] Pastikan tombol import, export, batch, dan vectorization tetap jelas di semua mode.
* [x] Tambahkan spacing dan padding UI agar tampilan lebih rapi.
* [x] Perbaiki kontras border antar panel.
* [x] Dokumentasikan checklist Phase 5 di `docs/checklist.md`.

# Phase 6 - Vectorizer Quality Improvement & Advanced Controls Checklist

Last updated: 2026-06-05

## Goal

Improve the vectorizer result quality and add advanced controls inspired by professional vectorizer tools.

Reference behavior:

* Side-by-side original and vectorized preview.
* Detail level control: Low, Medium, High.
* Color mode control: Unlimited colors or Custom colors.
* Advanced options:

  * Edit result.
  * Remove background.
  * Hand-pick settings.
* Download/export result after vectorization.

## Phase 6 Checklist

* [x] Improve the preview layout into a side-by-side comparison view:

  * [x] Left panel for original image.
  * [x] Right panel for vectorized result.
  * [x] Clear labels: `Original Image` and `Vectorized Result`.
* [x] Add synchronized zoom for original and vectorized preview.
* [x] Add pan support for both preview panels.
* [x] Add fit-to-screen preview button.
* [x] Add actual-size preview button.
* [x] Add vectorized result overlay preview for debugging paths.
* [x] Add `Detail Level` control with options:

  * [x] Low.
  * [x] Medium.
  * [x] High.
* [x] Map `Detail Level` to vectorization settings:

  * [x] Low: stronger simplification, fewer paths.
  * [x] Medium: balanced simplification.
  * [x] High: lower simplification, more accurate paths.
* [x] Add `Color Mode` control with options:

  * [x] Unlimited colors.
  * [x] Custom colors.
* [x] Add custom color count control when `Custom colors` is selected.
* [x] Add color quantization before vectorization.
* [x] Add option to preserve anti-aliased artwork edges.
* [x] Improve contour detection for filled shapes.
* [x] Improve contour detection for transparent or light backgrounds.
* [x] Add `Remove Background` option.
* [x] Add background color detection.
* [x] Add tolerance setting for background removal.
* [x] Add invert/background mode handling for dark and light images.
* [x] Add path grouping by detected color.
* [x] Add SVG fill color support based on quantized regions.
* [x] Add path simplification preview comparison.
* [x] Add minimum path area filter to remove noise.
* [x] Add smoothing control for jagged vector paths.
* [x] Add result quality presets:

  * [x] Artwork.
  * [x] Logo.
  * [x] Icon.
  * [x] Photo.
* [x] Add `Hand-pick Settings` section for manual tuning:

  * [x] Threshold.
  * [x] Detail level.
  * [x] Minimum area.
  * [x] Smoothing.
  * [x] Color count.
  * [x] Background tolerance.
* [x] Add `Reset Settings` button.
* [x] Add `Re-vectorize` button after settings change.
* [x] Disable export/download button when vector result is empty.
* [x] Keep vectorization processing responsive and avoid UI freezing.
* [x] Add progress/status message while vectorization is running.
* [x] Add error message when vectorization result is empty or too noisy.
* [x] Refactor vectorization settings into a dedicated config object.
* [x] Refactor preview rendering so raster preview and vector preview stay separated.
* [x] Keep improved vector output compatible with existing SVG export from Phase 4.
* [x] Document the Phase 6 checklist in `docs/checklist.md`.

## Phase 6 Boundaries

* Do not rebuild Phase 1.
* Do not rebuild Phase 2.
* Do not rebuild Phase 3 from scratch.
* Do not rebuild Phase 4 from scratch.
* Do not rebuild Phase 5 from scratch.
* Do not create packaging.
* Do not add cloud processing.
* Do not add account system.
* Do not add API/backend service.
* Do not add database.
* Do not add AI model dependency.
* Do not replace the entire UI layout unless needed for the side-by-side preview.
* Do not break existing single-image export.
* Do not break existing batch processing.

## Expected Output

* Vectorized result is visually cleaner.
* User can control detail level.
* User can control color mode.
* User can remove background.
* User can manually tune vectorization settings.
* Original and vectorized result can be compared side by side.
* Exported SVG reflects the improved vector result.

# Phase 7 - VTracer Engine Integration Checklist

Last updated: 2026-06-05

## Goal

Replace the current quality ceiling of the OpenCV contour-based vectorizer by adding VTracer as the primary vectorization backend, while keeping the current OpenCV engine as a fallback.

## Phase 7 Checklist

- [x] Keep the current OpenCV + K-Means vectorizer as fallback engine.
- [x] Add engine abstraction layer, for example `app/core/vectorizer_backend.py`.
- [x] Create backend interface with methods:
  - [x] `vectorize(input_path, settings)`.
  - [x] `supports_color()`.
  - [x] `supports_svg_output()`.
  - [x] `get_engine_name()`.
- [x] Create `OpenCVVectorizerBackend` for the existing engine.
- [x] Create `VTracerVectorizerBackend` as the new primary engine.
- [x] Add `vtracer` to project dependency only for Phase 7.
- [x] Add safe import handling for `vtracer`.
- [x] Show clear error message if VTracer dependency is missing.
- [x] Add engine selector in settings:
  - [x] VTracer.
  - [x] OpenCV Legacy.
- [x] Set VTracer as default engine when available.
- [x] Set OpenCV Legacy as fallback when VTracer is unavailable.
- [x] Map existing UI controls to VTracer settings:
  - [x] Detail level.
  - [x] Color mode.
  - [x] Custom color count.
  - [x] Background removal.
  - [x] Speckle/noise filtering.
  - [x] Path simplification.
- [x] Add VTracer-specific settings object.
- [x] Add color mode mapping:
  - [x] Black and white.
  - [x] Color.
- [x] Add hierarchical mode mapping:
  - [x] Cutout.
  - [x] Stacked.
- [x] Add curve fitting mode mapping:
  - [x] Pixel.
  - [x] Polygon.
  - [x] Spline.
- [x] Generate SVG directly from VTracer output.
- [x] Render VTracer SVG result in preview area.
- [x] Keep existing SVG export flow compatible with VTracer output.
- [x] Ensure batch processing can use VTracer backend.
- [x] Add fallback path if VTracer fails on a file during batch processing.
- [x] Add status message showing which engine is active.
- [x] Add error handling for failed VTracer conversion.
- [x] Add before/after comparison using the existing side-by-side preview.
- [x] Prevent 128-color mode from being used as default.
- [x] Keep 64 colors or lower as safer default for colored artwork.
- [x] Add preset mapping:
  - [x] Logo: fewer colors, stronger simplification.
  - [x] Icon: fewer colors, clean paths.
  - [x] Artwork: balanced color and curve fitting.
  - [x] Photo: higher color tolerance but warn about SVG complexity.
- [x] Add output complexity warning when generated SVG is too large.
- [x] Document VTracer integration in `docs/checklist.md`.

## Phase 7 Boundaries

- Do not keep increasing K-Means color count as a quality fix.
- Do not rewrite the entire UI.
- Do not remove the existing OpenCV engine.
- Do not break existing import image feature.
- Do not break existing preview feature.
- Do not break existing SVG export feature.
- Do not break existing batch processing.
- Do not start packaging in this phase.
- Do not add cloud processing.
- Do not add AI model dependency.
- Do not add database, API, or account system.

## Expected Output

- VTracer becomes the main vectorization engine.
- OpenCV engine remains available as fallback.
- Vector result quality improves through hierarchical color tracing and curve fitting.
- SVG export uses VTracer output when VTracer is active.
- Batch processing works with the selected engine.
- Project no longer depends on pushing K-Means/OpenCV beyond its practical limit.

# Phase 8 - Packaging & Release Distribution Checklist

Last updated: 2026-06-05

## Goal

Prepare the Image Vectorizer desktop application for local distribution as a runnable desktop app.

## Phase 8 Checklist

* [x] Audit project structure before packaging.
* [x] Clean unused imports, unused files, and obsolete code.
* [x] Ensure `main.py` is the single application entry point.
* [x] Ensure all required assets are loaded using root-based path helpers.
* [x] Create packaging configuration for PyInstaller.
* [x] Add `pyinstaller` to development packaging requirements if needed.
* [x] Create packaging script in `scripts/build_app.py`.
* [x] Create build output directory handling.
* [x] Configure application name as `Image Vectorizer`.
* [x] Configure application icon if icon asset exists.
* [x] Bundle required application resources.
* [x] Bundle required UI/theme resources.
* [x] Bundle required PySide6 dependencies.
* [x] Bundle required image processing dependencies.
* [x] Ensure packaging works without requiring source folder structure outside the build.
* [x] Create Windows build command.
* [x] Create macOS build command if supported.
* [x] Create Linux build command if supported.
* [x] Add build cleanup command or script.
* [x] Add runtime check for missing dependency/resource after packaging.
* [x] Ensure import image feature works in packaged app.
* [x] Ensure preview feature works in packaged app.
* [x] Ensure vectorization feature works in packaged app.
* [x] Ensure SVG export works in packaged app.
* [x] Ensure batch processing works in packaged app.
* [x] Ensure light/dark theme works in packaged app.
* [x] Add application version constant.
* [x] Display application version in the UI or About dialog.
* [x] Create `CHANGELOG.md`.
* [x] Create basic release notes for first packaged build.
* [x] Update `README.md` with build instructions.
* [x] Document Phase 8 checklist in `docs/checklist.md`.

## Phase 8 Boundaries

* Do not rebuild Phase 1.
* Do not rebuild Phase 2.
* Do not rebuild Phase 3.
* Do not rebuild Phase 4.
* Do not rebuild Phase 5.
* Do not rebuild Phase 6.
* Do not rebuild Phase 7.
* Do not add new vectorization features.
* Do not add cloud processing.
* Do not add account system.
* Do not add API/backend service.
* Do not add database.
* Do not add AI model dependency.
* Do not redesign the UI.
* Focus only on packaging, release readiness, and local distribution.

## Expected Output

* Application can be packaged into a desktop executable.
* Packaged app can run without using `python main.py`.
* Existing import, preview, vectorization, SVG export, batch processing, theme, and VTracer engine features still work.
* Basic build documentation exists.
* First release notes are documented.

# Phase 9 - CI Workflow, Release Automation & Repository Publishing Checklist

Last updated: 2026-06-05

## Goal

Create automated GitHub workflows for Windows, macOS, and Linux builds, add release/tag automation, and publish the Image Vectorizer project to the GitHub repository.

## Phase 9 Checklist

### Repository Initialization & First Push

* [x] Ensure the project is already inside the correct root folder.
* [x] Ensure `.gitignore` is already configured before first commit.
* [x] Ensure `.gitignore` excludes local-only and generated folders:

  * [x] `dist/`
  * [x] `build/`
  * [x] `*.spec`
  * [x] `.venv/`
  * [x] `venv/`
  * [x] `__pycache__/`
  * [x] `.pytest_cache/`
  * [x] `.mypy_cache/`
  * [x] `.DS_Store`
  * [x] `samples/`
  * [x] generated archives such as `*.zip`, `*.tar.gz`, and `*.7z`
* [x] Initialize Git repository if `.git/` does not exist:

  * [x] `git init`
* [x] Ensure the main branch is named `main`:

  * [x] `git branch -M main`
* [x] Add all project files to Git:

  * [x] `git add .`
* [x] Create the first commit:

  * [x] `git commit -m "BIG BANG"`
* [x] Add GitHub remote repository:

  * [x] `git remote add origin https://github.com/lukman-ss/silukman_image_vectorizer.git`
* [x] If remote origin already exists, update it instead:

  * [x] `git remote set-url origin https://github.com/lukman-ss/silukman_image_vectorizer.git`
* [ ] Push the project to GitHub:

  * [ ] `git push -u origin main`
* [ ] Verify the repository contains the full project, not only `README.md`.
* [x] Verify ignored folders are not committed:

  * [x] `dist/`
  * [x] `build/`
  * [x] `.venv/`
  * [x] `venv/`
  * [x] `samples/`
  * [x] generated archives

### Git Bootstrap Commands

```bash
git init
git branch -M main

git add .
git commit -m "BIG BANG"

git remote add origin https://github.com/lukman-ss/silukman_image_vectorizer.git
git push -u origin main
```

### Existing Remote Fix

```bash
git remote set-url origin https://github.com/lukman-ss/silukman_image_vectorizer.git
git push -u origin main
```

### CI Build Workflow

* [x] Create `.github/` directory if it does not exist.
* [x] Create `.github/workflows/` directory.
* [x] Create GitHub Actions workflow file:

  * [x] `.github/workflows/build.yml`
* [x] Configure workflow name as `Build Image Vectorizer`.
* [x] Configure workflow trigger for:

  * [x] Manual run using `workflow_dispatch`.
  * [x] Push to `main` branch.
  * [x] Pull request to `main` branch.
* [x] Create build matrix for:

  * [x] Windows runner.
  * [x] macOS runner.
  * [x] Linux runner.
* [x] Configure Python version used by all runners.
* [x] Checkout repository in workflow.
* [x] Install Python dependencies from `requirements.txt`.
* [x] Install packaging dependencies if separated from runtime dependencies.
* [x] Verify `pyinstaller` is available before build.
* [x] Run the existing packaging script:

  * [x] `python scripts/build_app.py`
* [x] Ensure workflow uses the existing Phase 8 packaging configuration.
* [x] Do not duplicate PyInstaller commands directly inside workflow if `scripts/build_app.py` already handles build logic.
* [x] Add platform-specific build output naming:

  * [x] `Image-Vectorizer-Windows`
  * [x] `Image-Vectorizer-macOS`
  * [x] `Image-Vectorizer-Linux`
* [x] Archive Windows build output as `.zip`.
* [x] Archive macOS build output as `.zip` or `.dmg` if already supported.
* [x] Archive Linux build output as `.tar.gz` or `.zip`.
* [x] Upload each platform build as GitHub Actions artifact.
* [x] Add artifact retention setting.
* [x] Add build failure handling with clear logs.
* [x] Add workflow step to print build output directory contents.
* [x] Add workflow step to verify packaged executable exists.
* [x] Add workflow step to verify bundled resources exist:

  * [x] `app/resources/icon.png`
  * [x] `app/resources/hero_image.png`
* [x] Add workflow step to verify application version exists.
* [x] Add workflow step to verify `CHANGELOG.md` exists.
* [x] Document CI build usage in `README.md`.
* [x] Document manual build and CI build difference in `README.md`.

### Release Workflow

* [x] Create release workflow file:

  * [x] `.github/workflows/release.yml`
* [x] Configure release workflow trigger using Git tags:

  * [x] `v*.*.*`
* [x] Build Windows artifact during release workflow.
* [x] Build macOS artifact during release workflow.
* [x] Build Linux artifact during release workflow.
* [x] Upload Windows artifact to GitHub Release.
* [x] Upload macOS artifact to GitHub Release.
* [x] Upload Linux artifact to GitHub Release.
* [x] Use tag name as release version.
* [x] Use `CHANGELOG.md` as release notes source if possible.
* [x] Ensure release is not published if any platform build fails.
* [x] Document release workflow usage in `README.md`.

### Manual Tag Workflow

* [x] Create manual tag workflow:

  * [x] `.github/workflows/create_tag.yml`
* [x] Configure manual tag workflow using `workflow_dispatch`.
* [x] Add version input for manual tag creation, for example:

  * [x] `v1.0.0`
* [x] Validate tag format must match:

  * [x] `v*.*.*`
* [x] Prevent duplicate tag creation if tag already exists.
* [x] Create Git tag from selected branch.
* [x] Push Git tag to repository.
* [x] Ensure pushed tag triggers `release.yml`.
* [x] Document manual tag flow in `README.md`.

### Required Workflow Files

* [x] `.github/workflows/build.yml`
* [x] `.github/workflows/release.yml`
* [x] `.github/workflows/create_tag.yml`

### Expected Release Flow

1. Push the full project to GitHub.
2. GitHub Actions runs `build.yml` on push or manual trigger.
3. Run `create_tag.yml` manually.
4. Input version, for example `v1.0.0`.
5. Workflow creates and pushes Git tag.
6. Tag push triggers `release.yml`.
7. Release workflow builds Windows, macOS, and Linux.
8. GitHub Release is created automatically.
9. Build artifacts are attached to the release.

## Platform Build Targets

### Windows

* [x] Build Windows executable from Windows runner.
* [x] Ensure generated `.exe` exists.
* [x] Include required resource files.
* [x] Package Windows output as `.zip`.
* [x] Upload Windows artifact.

### macOS

* [x] Build macOS application from macOS runner.
* [x] Ensure generated `.app` or executable exists.
* [x] Include required resource files.
* [x] Package macOS output as `.zip` or `.dmg` if supported.
* [x] Upload macOS artifact.

### Linux

* [x] Build Linux executable from Linux runner.
* [x] Ensure generated binary exists.
* [x] Include required resource files.
* [x] Package Linux output as `.tar.gz` or `.zip`.
* [x] Upload Linux artifact.

## Phase 9 Boundaries

* Do not rebuild Phase 1.
* Do not rebuild Phase 2.
* Do not rebuild Phase 3.
* Do not rebuild Phase 4.
* Do not rebuild Phase 5.
* Do not rebuild Phase 6.
* Do not rebuild Phase 7.
* Do not rebuild Phase 8.
* Do not change vectorization logic.
* Do not change SVG export logic.
* Do not change batch processing logic.
* Do not redesign the UI.
* Do not add new app features.
* Do not add database, API, account system, or cloud processing.
* Do not add code signing unless explicitly required.
* Do not add notarization unless explicitly required.
* Do not use `git add README.md` for the first project push.
* Do not overwrite an existing `README.md` with a single-line placeholder.
* Do not commit build output directories.
* Do not commit generated archives.
* Do not commit virtual environment folders.
* Do not commit `samples/`.
* Focus only on repository publishing, CI workflow, automated build, artifact upload, tag creation, and release automation.

## Expected Output

* Full project is pushed to GitHub repository.
* `.gitignore` excludes build output, virtual environments, generated archives, and `samples/`.
* GitHub Actions can build the app on Windows.
* GitHub Actions can build the app on macOS.
* GitHub Actions can build the app on Linux.
* Each platform build is uploaded as an artifact.
* Manual tag workflow can create validated version tags.
* Tag push can trigger automated release workflow.
* GitHub Release contains Windows, macOS, and Linux artifacts.
* Existing PyInstaller packaging logic from Phase 8 remains the source of truth.

# Phase 10 - PyPI Package Publishing Checklist

Last updated: 2026-06-05

## Goal

Publish Image Vectorizer as a Python package to PyPI using GitHub Actions, with the PyPI API token already stored in repository secrets as `PYPI_API_TOKEN`.

## Phase 10 Checklist

### Package Publishing Preparation

* [x] Decide the PyPI package name:

  * [x] `silukman-image-vectorizer`
* [x] Ensure the package name is consistent across:

  * [x] `pyproject.toml`
  * [x] README documentation
  * [x] GitHub workflow
  * [x] release notes
* [x] Create or update `pyproject.toml`.
* [x] Define package metadata:

  * [x] Package name.
  * [x] Version.
  * [x] Description.
  * [x] Author.
  * [x] License.
  * [x] Python version requirement.
  * [x] Project URLs.
  * [x] Classifiers.
* [x] Ensure package version uses a single source of truth.
* [x] Ensure app version and PyPI package version are synchronized.
* [x] Ensure `README.md` is used as the long description.
* [x] Ensure required runtime dependencies are declared correctly.
* [x] Ensure packaging/build dependencies are separated from runtime dependencies if needed.
* [x] Ensure local-only folders are excluded from package distribution:

  * [x] `dist/`
  * [x] `build/`
  * [x] `.github/`
  * [x] `.venv/`
  * [x] `venv/`
  * [x] `samples/`
  * [x] generated archives
* [x] Ensure app resource files needed by the package are included:

  * [x] `app/resources/icon.png`
  * [x] `app/resources/hero_image.png`
* [x] Ensure package can be imported without launching the GUI automatically.
* [x] Ensure `main.py` or console entry point can launch the app intentionally.
* [x] Add optional console script entry point if appropriate:

  * [x] `image-vectorizer`

### Build Validation

* [x] Install package build tools:

  * [x] `python -m pip install build twine`
* [x] Build source distribution and wheel:

  * [x] `python -m build`
* [x] Verify build output exists:

  * [x] `dist/*.tar.gz`
  * [x] `dist/*.whl`
* [x] Validate package metadata:

  * [x] `python -m twine check dist/*`
* [x] Ensure generated package does not include ignored folders.
* [x] Ensure package can be installed locally from wheel.
* [x] Ensure installed package can launch the app.
* [x] Ensure package import does not trigger PySide6 GUI startup automatically.

### PyPI Publish Workflow

* [x] Create GitHub Actions workflow file:

  * [x] `.github/workflows/publish_pypi.yml`
* [x] Configure workflow name:

  * [x] `Publish to PyPI`
* [x] Configure workflow trigger using Git tags:

  * [x] `v*.*.*`
* [x] Add optional manual trigger:

  * [x] `workflow_dispatch`
* [x] Checkout repository in workflow.
* [x] Set up Python in workflow.
* [x] Install build tools:

  * [x] `python -m pip install --upgrade pip`
  * [x] `python -m pip install build twine`
* [x] Build package:

  * [x] `python -m build`
* [x] Validate package:

  * [x] `python -m twine check dist/*`
* [x] Publish package to PyPI using repository secret:

  * [x] `PYPI_API_TOKEN`
* [x] Use token authentication:

  * [x] `TWINE_USERNAME=__token__`
  * [x] `TWINE_PASSWORD=${{ secrets.PYPI_API_TOKEN }}`
* [x] Upload only files from `dist/`.
* [x] Prevent publish if build or twine check fails.
* [x] Prevent duplicate version upload.
* [x] Ensure PyPI publish only runs on release/tag workflow, not every push.
* [x] Document PyPI publishing workflow in `README.md`.

### Version & Tag Policy

* [x] Ensure PyPI version matches Git tag.
* [x] Use semantic version format:

  * [x] `v1.0.0`
* [x] Strip leading `v` when used as Python package version if needed.
* [x] Prevent publishing if package version already exists on PyPI.
* [x] Ensure `CHANGELOG.md` includes the release version.
* [x] Ensure GitHub Release and PyPI package publish use the same version.
* [x] Add release flow documentation:

  * [x] Update version.
  * [x] Update changelog.
  * [x] Commit changes.
  * [x] Create tag.
  * [x] Push tag.
  * [x] Build GitHub artifacts.
  * [x] Publish package to PyPI.

### Recommended Workflow Order

1. Update package version.
2. Update `CHANGELOG.md`.
3. Commit version update.
4. Create Git tag, for example `v1.0.0`.
5. Push tag to GitHub.
6. GitHub release workflow builds Windows, macOS, and Linux artifacts.
7. PyPI workflow builds source distribution and wheel.
8. PyPI workflow validates package metadata.
9. PyPI workflow publishes package using `PYPI_API_TOKEN`.

### Phase 10 Boundaries

* Do not rebuild Phase 1.
* Do not rebuild Phase 2.
* Do not rebuild Phase 3.
* Do not rebuild Phase 4.
* Do not rebuild Phase 5.
* Do not rebuild Phase 6.
* Do not rebuild Phase 7.
* Do not rebuild Phase 8.
* Do not rebuild Phase 9.
* Do not change vectorization logic.
* Do not change SVG export logic.
* Do not change batch processing logic.
* Do not redesign the UI.
* Do not add new app features.
* Do not commit PyPI token.
* Do not print PyPI token in logs.
* Do not publish to PyPI on every push.
* Do not publish duplicate versions.
* Do not include `samples/` in package distribution.
* Do not include build artifacts inside the PyPI package.
* Focus only on Python packaging, PyPI metadata, package build validation, and PyPI publish workflow.

## Expected Output

* Project has valid Python package metadata.
* Package can build `.whl` and `.tar.gz`.
* Package passes `twine check`.
* GitHub Actions can publish to PyPI using `PYPI_API_TOKEN`.
* PyPI publish is triggered safely by version tag.
* GitHub Release version and PyPI package version stay aligned.
* `samples/`, build folders, virtual environments, and generated archives are excluded from package distribution.
