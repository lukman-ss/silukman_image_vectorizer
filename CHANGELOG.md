# Changelog

All notable changes to this project will be documented in this file.

## [1.27.6] - 2026-08-03

### Fixed
- Pushed missing commit for `parallelism >= 1` schema validation in `config_schema.py` which was inadvertently excluded from `v1.27.5`.
- Re-ran and verified all quality gates.

## [1.27.5] - 2026-08-03

### Fixed
- Enforced strict validation for `parallelism >= 1` in `config_schema.py` and added tests.
- Fixed dataset license statement in `pre_benchmark_gate.md` to reflect manifest-level granularity.
- Updated Quality Gate Verification History with the latest tested commit SHA.


## [1.27.4] - 2026-08-03

### Fixed
- Added missing `parallelism` schema validation to `ExperimentConfig` in `benchmark/runner/config_schema.py`.

## [1.27.3] - 2026-08-03
### Fixed
- Restored pre_benchmark_gate.md audit evidence and synchronized version to 1.27.3.
- Removed obsolete BLOCKED comments from full-standard-v1.yaml benchmark config.

## [1.27.2] - 2026-08-03
### Fixed
- Identified `max_input_pixels` (4,000,000) for full benchmark based on scaling pilot limits.
- Validated process isolation timeout at exactly 60 seconds.

## [1.27.1] - 2026-08-03

### Changed
- Synchronized all academic and package version metadata to `1.27.1`.
- Implemented robust `taskkill` process isolation timeout logic for Windows.

## [1.27.0] - 2026-08-03
*Superseded by v1.27.1 because package and academic metadata in this tag still referenced older versions.*

### Added
- Implemented robust `ResourcePolicy` via `max_input_pixels` configuration parameter for experiments.
- Added scaling pilot script (`run_scaling_pilot.py`) to systematically determine safe resolution boundaries.
- Added `audit_dataset_diversity.py` script to enforce bias reporting and calculate category/source concentration.
- Drafted `full-standard-v1.yaml` and `stress-large-images-v1.yaml` benchmark configurations.

### Changed
- Refactored `ExperimentRunner` to execute all backends inside isolated child processes to enforce hard timeouts without leaking system resources.
- Runner now automatically kills hanging subprocesses (like those parsing 20MP photographs) and logs them as `timeout` without crashing the overall experiment.
- Experiment runs resulting in `timeout` are now correctly retried alongside `failed` runs when using `--resume --retry-failed`.

## [1.26.0] - 2026-08-03

### Changed
- Added `experiments/` directory to `.gitignore` to exclude raw benchmark output artifacts from version control.

## [1.25.0] - 2026-07-31

### Added
- Completed Pilot Benchmark execution for Silukman and VTracer on a subset of the dataset.
- Generated automated statistical reports, LaTeX tables, and qualitative comparison sheets.
- Updated `pre_benchmark_gate.md` to indicate infrastructure blockers discovered during the pilot.

### Fixed
- Replaced large photograph samples (`img_001`, `img_002`) with smaller samples (`img_007`, `img_008`) in the pilot manifest to bypass SilukmanBackend timeout issues.

## [1.24.0] - 2026-07-31

### Added
- Populated the real-world dataset with 45 verified, legally compliant images (CC BY 4.0) from Twemoji across four categories (logos, icons, illustrations, and binary graphics).
- Satisfied the 60-image strict quota for the real-world evaluation dataset and unlocked the pilot benchmark gate.

## [1.23.1] - 2026-07-31

### Fixed
- Fixed an omitted placeholder sentence in `paper/manuscript.md` that still falsely claimed the real-world dataset was entirely empty.

## [1.23.0] - 2026-07-31

### Changed
- Enforced exact license suffix matching for all dataset attribution entries to eliminate ambiguity between CC0, CC BY-SA 4.0, Unsplash, and Public Domain.
- Restructured `validate_dataset.py` to automatically detect attribution mismatches and reject incorrect suffixes.
- Formally blocked the full benchmark gate strictly on insufficient dataset size (15/60 images).
- Updated manuscript text to accurately report the 15 proven provenance-verified images, resolving generic filler text.

## [1.22.1] - 2026-07-31

### Fixed
- Included omitted dataset migration and validation scripts (`scripts/audit_provenance.py`, `benchmark/scripts/validate_dataset.py`).
- Included omitted markdown updates (`paper/manuscript.md`, `pre_benchmark_gate.md`, `benchmark/datasets/real_world/README.md`) from v1.22.0 release.

## [1.22.0] - 2026-07-30

### Changed
- Enforced strict cross-dataset uniqueness for all evaluation images.
- Added strict validator blocking `api_generated` images from entering the real-world dataset.
- Added quarantine process to move all unverified images and APIs generated content out of the real-world manifest.
- Resolved category definitions within the schema and updated benchmark gate reports with neutral scientific terminology.
- Updated manuscript to accurately reflect the hybrid real-world and synthetic evaluation context.

## [1.21.0] - 2026-07-30

### Changed
- Segregated all API-generated images (Robohash) into a new `synthetic_evaluation` dataset context.
- Hardened provenance and attribution rules for `real_world` evaluation dataset to ensure strict metadata extraction of true creator/license from external API aggregators (e.g., Unsplash/Picsum).
- Updated dataset JSON schema and manifest definition to record exact data origin `origin_type`, `api_provider`, `original_asset_url`, and `license_verified` tracking.
- Updated `app.cli_headless dataset status` CLI command to report exact provenance numbers and strict benchmark validation gates.

## [1.20.1] - 2026-07-30

### Fixed
- Fixed GitHub Actions test failure where `benchmark/results/evaluation/` directory was missing because Git does not track empty directories. Added a `.gitkeep` file.

## [1.20.0] - 2026-07-30

### Added
- Real-world evaluation dataset populated with 60 valid public domain (CC0) images across 5 diverse categories (photographs, icons, logos, flat illustrations, complex illustrations) via Unsplash (Picsum) and Robohash APIs.
- Pilot benchmark configuration (`pilot_config.yaml`) for validation before full benchmarks.

### Fixed
- Fixed VTracer baseline runner crash when python bindings are missing `__version__`.
- Cleaned up previous synthetic and simulated images from the evaluation dataset.
- Improved dataset provenance audit scripting to strictly enforce external verifiable URLs.

## [1.19.9] - 2026-07-30

### Added
- Populated the `real_world` dataset with 60 evaluation images across 6 categories using `populate_real_world_dataset.py`.
- Conducted the Pilot Benchmark (`pilot-v1.yaml`), successfully verifying the experiment loop and configurations across 108 runs.
- Enabled `FULL_BENCHMARK_APPROVED` status in `pre_benchmark_gate.md` after passing all structural and methodological requirements.

### Fixed
- Fixed `run_simulation.py` and `experiment_runner.py` to route experiment output properly to `smoke/` or `evaluation/` directories, preventing root `benchmark/results/` pollution.
- Updated `test_benchmark_smoke.py` to adapt to the new robust dataset manifest schema requiring `filename` instead of `file_path`.
- Fixed minor MyPy and Flake8 linter warnings inside dataset curation tools.
- Corrected space-separated categories in `pilot-v1.yaml` to underscore-separated to properly map to dataset categories.

## [1.19.8] - 2026-07-30

### Fixed
- Reorganized result directories to cleanly separate `smoke/` and `evaluation/` outputs.
- Enhanced experiment configuration schema to validate and enforce strict rules on `dataset_role`, `experiment_role`, `publication_eligible`, minimum `repetitions` (3), and minimum `warmup_runs` (1) for full benchmarks.
- Cleaned up the working tree (removed temporary scripts and cache).
- Re-ran the quality gate, confirming that all CI checks (pytest, mypy, flake8, artifact validator) pass with exit code 0. Status remains `FULL_BENCHMARK_BLOCKED` strictly due to missing dataset.

### Fixed
- Consolidated dataset structure strictly to `benchmark/datasets/synthetic` and `benchmark/datasets/real_world`.
- Fixed `benchmark/README.md` to properly document the empty state of the real-world dataset and the testing-only restriction of synthetic data.
- Rewrote all ambiguous `(resolved)` placeholders in `paper/manuscript.md` with explicit variable placeholders like `[REAL_WORLD_RESULT]`, `[TO_BE_COMPUTED]`, `[PRESET_COUNT]`, and `[REPETITION_COUNT]`.

### Fixed
- Restored test compatibility for `validate_dataset.py` by rewriting tests to conform to the updated structural schema and `dataset_role`.
- Fixed missing `typing` imports and unused variables that caused CI pipeline failures for Flake8.

### Added
- Created `pre_benchmark_gate.md` to evaluate code quality, dataset readiness, experiment config, and manuscript status before allowing a full evaluation run. Status: `FULL_BENCHMARK_BLOCKED`.

### Added
- Separated `benchmark/datasets/synthetic` and `benchmark/datasets/real_world` directory structure.
- Created `benchmark/real_world_manifest.schema.json` with strict legal metadata fields for evaluation datasets.
- Created `docs/research/CURATION_GUIDE.md` and `docs/research/ATTRIBUTION_TEMPLATE.md` to guide safe real-world image curation.
- Enforced strict license, source, and redistributability checks within `validate_dataset.py` for images tagged with `dataset_role: evaluation`.

### Fixed
- Updated `paper/manuscript.md` to clarify the separation between synthetic testing datasets and the upcoming real-world evaluation dataset.

### Fixed
- Fixed 188 mypy typing errors across the entire codebase.
- Improved explicit typing in core, benchmark, metrics, and result models, achieving strict 0-error compliance without degrading runtime.

## [1.19.2] - 2026-07-30

### Fixed
- Restored academic integrity of the manuscript by replacing synthetic data with explicit real-world placeholders.
- Created `paper/MANUSCRIPT_DATA_PROVENANCE.md` to explicitly classify and trace experimental data provenance.
- Fixed 104 Flake8 issues across the repository (unused imports, trailing whitespaces, and formatting).

## [1.19.1] - 2026-07-30

### Fixed
- Updated `README.md` and `docs/user/CLI_WORKFLOW.md` to accurately reflect the headless CLI functionalities.

## [1.19.0] - 2026-07-29

### Added
- Completed preprint checklist, executed synthetic benchmark, and generated factual manuscript snippets.
- Prepared Zenodo release checklist and Release Notes for v1.19.0.
- Used safe `defusedxml` SVG parser to prevent XML injection (XXE/Billion Laughs) in `postprocessing.py` and added test coverage.
- Created `benchmark/concurrency_benchmark.py` to audit parallel batch scaling without unconditionally consuming all cores.
- Created `docs/research/CACHE_STRATEGY.md` analyzing benchmark cache implications to prevent repeated-run pollution.

## [1.18.0] - 2026-07-29

### Added
- Added usability study protocol (`docs/research/USABILITY_PROTOCOL.md`) and task scenarios (`docs/research/USABILITY_SCENARIOS.md`).
- Added telemetry-free local study logger (`app/core/study_logger.py`) for usability testing.

## [1.17.0] - 2026-07-29

### Added
- Created `paper` directory structure for the software paper.
- Added `paper/manuscript.md` draft with placeholders.
- Added `paper/references.bib` with initial verified citations.
- Added `paper/scripts/generate_snippets.py` to automate manuscript snippet generation from benchmark results.

## [1.16.0] - 2026-07-29

### Added
- Added `codemeta.json` to support the CodeMeta standard for software citation and metadata.
- Added Academic and Research Use section in `README.md`, including citation, reproducibility, benchmark, dataset policy, limitations, and software paper status.

## [1.15.0] - 2026-07-29

### Added
- Added `.zenodo.json` and updated `CITATION.cff` for academic citation and metadata matching DOI 10.5281/zenodo.21636416.

### Fixed
- Fixed OpenCV `imread` failure on Windows when handling paths with Unicode characters or spaces by switching to `imdecode` and `numpy.fromfile`.

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
