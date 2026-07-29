# Silukman Image Vectorizer - Release Notes (Research-Ready Version)

**Version:** 1.19.0 (Preprint Release Candidate)

This release marks the primary research-ready milestone for Silukman Image Vectorizer, providing the complete toolset required to reproduce the empirical findings in our software paper.

## Main Features
- **High-Fidelity Raster-to-Vector Conversion**: Supports `VTracer` and `OpenCV Legacy` backends with advanced post-processing optimization.
- **Configurable Presets**: Extensible JSON-backed configuration system offering distinct fidelity/complexity trade-offs (e.g., `low_complexity`, `balanced`, `high_fidelity`).
- **Comprehensive Desktop Interface & Headless CLI**: Provides both a rich PySide6 graphical interface for qualitative adjustments and a robust headless CLI for batch processing.

## Benchmark Framework
- Includes a fully automated, reproducible benchmark suite (`benchmark/runner/experiment_runner.py`).
- Supports running unified evaluations against Inkscape and Potrace baselines.
- Calculates comprehensive quality metrics (Pixel, Edge, Histogram, SSIM) alongside execution complexity and runtime performance.

## Dataset Policy
- The benchmark expects the `lukman_dataset` containing legally cleared, openly licensed raster images.
- Images must adhere to the categorized structure defined in `dataset_manifest.json`.

## Reproducibility
- Execution environment metadata (Hardware, OS, Dependency trees) is rigorously captured via `env_capture.py`.
- Config hashes and image SHA-256 checksums guarantee input-to-output provenance.
- Cache isolation prevents benchmark pollution across repeated runs.

## Supported Platforms
- Evaluated on macOS (ARM64/x86_64), Linux (Ubuntu), and Windows 10/11.
- Python 3.9+ required.

## Known Limitations
- VTracer backend memory instrumentation is currently unmeasured natively due to C-binding limits in the Python wrapper.
- Extremely large images (>8192x8192) may exceed standard allocation limits and should be handled with care.

## Citation
If you use this software in your research, please cite it as detailed in the `CITATION.cff` or `README.md`. (DOI will be provided upon Zenodo archival).

## Artifacts
- The source code archive (`.tar.gz`, `.zip`)
- Pre-built binary distributions (where applicable)
- Evaluated `runs.jsonl` (to be attached to the final benchmark release)

## Compatibility & Migration Notes
- **Upgrading from 1.16.x**: The SVG parser is now strictly secure against XML injections (`defusedxml`). Any malformed XML artifacts previously accepted may now be rightfully rejected.
- The `VectorizationConfig` requires strictly typed backend selection (`engine_type`).
