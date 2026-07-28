# Changelog

All notable changes to this project will be documented in this file.

## [1.14.0] - 2026-07-28

### Added
- Added comprehensive architecture documentation with dependency, data-flow, and error-flow diagrams.
- Added implementation-aligned vectorization pipeline and complete parameter reference documentation.
- Added a runnable reproducibility guide covering dataset validation, benchmark execution, analysis generation, checksum verification, and failure retries.
- Added an explicit benchmark protocol covering research questions, fairness, statistical analysis, failure handling, and qualitative sample selection.
- Added honest research limitations for backend dependence, metric coverage, dataset scope, hardware effects, parameter tuning, and cross-platform variance.
- Added a security audit for untrusted raster/SVG parsing, external executables, path handling, temporary files, command injection, and resource exhaustion.

## [1.13.7] - 2026-07-28

### Fixed
- Fixed release packaging failures by adding PyInstaller to the `dev` and `all` dependency extras used by the multi-platform release workflow.

## [1.13.6] - 2026-07-28

### Fixed
- Fixed GitHub Actions lint failures across Ubuntu, macOS, and Windows runners by importing `pathlib.Path` in the dataset validation test.
- Updated legacy CLI unit-test mocks to use the current result `status` contract, allowing the complete pre-release test suite to pass.
- Fixed automated release-note extraction for `v`-prefixed Git tags.

## [1.13.5] - 2026-07-28

### Fixed
- Fixed `pytest` import file mismatch error on CI by renaming `tests/core/test_svg_metrics.py` to `tests/core/test_core_svg_metrics.py` to avoid basename collisions with `tests/evaluation/test_svg_metrics.py`.

## [1.13.4] - 2026-07-28

### Fixed
- Fixed Windows CI pipeline assertion failure caused by native Windows path separators (`\`) in test expectations after YAML parsing outputted POSIX separators (`/`).

## [1.13.3] - 2026-07-28

### Fixed
- Fixed Windows CI pipeline test failures due to YAML escaping backslashes from dynamic Windows `tmp_path`.
- Fixed Windows CI pipeline failure in `test_unicode_and_space_path` caused by OpenCV string decoding issues with special Unicode characters in temporary directories.

## [1.13.2] - 2026-07-28

### Fixed
- Fixed GitHub Actions test workflow (`ci.yml`) where `test_benchmark_config_validation` failed due to missing `libegl1` and display server when importing PySide6 on Ubuntu runners.

## [1.13.1] - 2026-07-28

### Fixed
- Fixed GitHub Actions release workflow (`release.yml`) failing on missing dependencies by switching to `pip install .[all]` and installing `libegl1` and `xvfb` for headless GUI tests.

## [1.13.0] - 2026-07-28

### Added
- **Code Quality (FASE 12)**:
  - Standardized codebase with Black and Isort formatters.
  - Added robust type hints (PEP 484) to core components and benchmark runner.
  - Implemented structured JSON logging (`app/core/logging.py`) capturing metadata (timestamp, level, run_id, backend, duration).
  - Defined explicit exception hierarchy (`SilukmanError` and subclasses) for clearer error classification in CLI/GUI/Benchmarks.
  - Conducted Determinism Audit across the pipeline (file ordering, timestamps, RNG seeding).

### Fixed
- Fixed GitHub Actions test dependencies to install `[research]` extras required for benchmark validation (`yaml`, `scipy`).
- Fixed Windows CI pipeline invoking `PYTHONPATH` incompatibly.

## [1.12.0] - 2026-07-28

### Added
- **Dependency Locking & Installation Targets**: Reorganized `pyproject.toml` dependencies into `research`, `dev`, and `all` optional packages.
- **Enhanced Release Workflow**: Added robust checksum generation (SHA256), test prerequisites before releasing, and automatic release note extraction.

## [1.11.0] - 2026-07-28

### Added
- **Testing and Quality Assurance (FASE 10)**:
  - Added unit test suite covering core components (config validation, SVG metrics, result parsing).
  - Added integration test suite testing vectorization pipelines across multiple file formats (PNG, JPEG, RGBA) and edge cases.
  - Added Snapshot Regression test validating output SVG structure invariance.
  - Added CLI test validating all headless commands (`vectorize`, `batch`, `benchmark`).
  - Added Benchmark Smoke test verifying experiment runner against synthetic data.
  - Added code coverage reporting configuration (`pytest-cov`) focusing on core logic.

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
