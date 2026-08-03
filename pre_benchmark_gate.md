# Pre-Benchmark Quality Gate

**Status**: `PILOT_INFRASTRUCTURE_PASSED`
**Version**: `1.27.1`

## Acceptance Criteria

### Dataset Requirements
- [x] Dataset manifest is available and contains > 60 verified images (61 images).
- [x] All images are verifiably CC BY 4.0 or public domain.
- [x] No synthesized data (must be real-world data).
- [x] Contains images from all required categories (logo, photograph, illustration, icon, binary_graphic).

### Infrastructure Validation
- [x] All `pytest` suites passing (100% success rate across all integrations and baselines).
- [x] Static analysis (mypy, flake8) passing.
- [x] `run_scaling_pilot.py` executed successfully.
- [x] `max_input_pixels` for standard benchmark set empirically (4,000,000 pixels) based on scaling pilot results avoiding 60s timeout line.
- [x] Hard timeouts enforced correctly using process isolation.
- [x] Process tree cleanup verified on POSIX (Process Groups) and Windows (`taskkill /T /F`).
- [x] No lingering zombie processes or leaked semaphores.

### Benchmarking Configs
- [x] `experiments/configs/full-standard-v1.yaml` (3 repetitions, 1 warmup, 60s timeout, 4MP limit).
- [x] `experiments/configs/stress-large-images-v1.yaml` (1 repetition, 0 warmup, 120s timeout, no size limit).

### Version Metadata Consistency
- [x] All metadata sources synchronized to `v1.27.1` (pyproject.toml, CITATION.cff, codemeta.json, .zenodo.json, app constants).

## Notes
- Scaling pilot confirmed that 2.8MP images take ~23s while 20MP images exceed the 60s/120s timeouts.
- Due to a 73.8% concentration of Twemoji icons in the dataset, final paper claims must be scoped appropriately.
- Full benchmark is ready for final execution. Status `FULL_BENCHMARK_APPROVED` is pending one final review if requested.
