# Changelog

All notable changes to this project will be documented in this file.

## [1.10.0] - 2026-07-28

### Added
- **Qualitative Comparison Generator**: Added `benchmark/analysis/qualitative_generator.py` to automatically compile side-by-side visual comparison sheets (markdown/html). Employs an explicit selection rule (Best, Median, Worst SSIM per category) to prevent cherry-picking.
- **Automated Comprehensive Reporting (FASE 9)**: 
  - New `benchmark report` CLI command that acts as an orchestrator.
  - Generates a full `report/` hierarchy (`summary.md`, `reproducibility.md`, `tables/`, `figures/`, `qualitative/`, `failures/`) derived entirely from raw JSONL data without manual intervention.

## [1.9.0] - 2026-07-28

### Added
- **Statistical Analysis Suite (FASE 8)**:
  - Added JSONL log aggregation module (`benchmark aggregate`) calculating descriptive statistics (mean, median, standard deviation, min, max, percentiles, confidence intervals, outlier detection) with robustness against missing or failed runs.
  - Implemented Paired Comparison analysis (`benchmark paired`) calculating per-image deltas, wins/ties/losses, Cohen's *d* effect size, and Wilcoxon signed-rank significance tests.
  - Added Pareto Frontier analysis (`benchmark pareto`) revealing multi-objective optimal trade-offs (e.g., SSIM vs SVG size) without assuming a universally "best" configuration.
  - Introduced Category Profiling (`benchmark category`) for evaluating algorithm strengths/weaknesses across specific image genres (logos, photos, icons, etc.) with explicit interpretation guardrails.
  - Built Failure Analysis system (`benchmark failure`) classifying crash/timeout/OOM logs into known error taxonomies and tracking failure rates while preserving complete trace transparency.

## [1.8.0] - 2026-07-28

### Added
- **Experiment Runner (FASE 7)**: 
  - Comprehensive `benchmark run` CLI for executing vectorization baselines against a configured dataset.
  - Deterministic experiment IDs (`timestamp_name_sha_hash`) for full traceability.
  - Comprehensive environment capture (`env_capture.py`) recording OS, CPU, RAM, Git states, and vectorizer versions.
  - Append-safe JSONL raw result output (`runs.jsonl`) with resilient parsing against corrupted lines.
  - Seamless experiment resume mechanism (`--resume-id`) with config hash-matching protections and retry logic (`--retry-failed`).
  - Strict process isolation (`run_isolated_process`) with group signal termination preventing zombie sub-processes during timeouts.

## [1.1.0] - 2026-07-28

### Added
- `CITATION.cff` — standard academic citation metadata (CFF v1.2.0) for software paper reference via GitHub and Zenodo.

## [1.0.5] - 2026-06-05

### Fixed
- Replace invalid PyPI Trove classifier with a valid graphics conversion classifier.

## [1.0.4] - 2026-06-05

### Changed
- Switch PyPI upload workflow to the official PyPA publish action with verbose diagnostics.

## [1.0.3] - 2026-06-05

### Changed
- Retrigger PyPI publishing after refreshing the repository upload token.

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
