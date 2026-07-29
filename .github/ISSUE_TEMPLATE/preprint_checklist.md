---
name: Preprint Readiness Checklist
about: Checklist to verify that the repository is ready for a preprint release.
title: 'Preprint Release: [VERSION]'
labels: 'release, preprint'
assignees: ''
---

## Code
- [x] Core is callable without GUI.
- [x] CLI is available and documented.
- [x] All tests pass across the defined matrix.
- [x] Release tag is prepared/exists.
- [x] Dependency lock file (or pinned requirements) is included.

## Data
- [x] Dataset manifest is fully populated.
- [x] All source licenses are documented and compatible.
- [x] SHA-256 checksums are recorded for all inputs.
- [x] Images are correctly assigned to predefined categories.
- [x] Total sample count matches the paper's claim.

## Experiment
- [x] Experiment configuration (YAML/JSON) is frozen and archived.
- [x] Environment hardware and OS metadata are captured.
- [x] Raw result logs (`runs.jsonl`) are available and unedited.
- [x] Specified repetitions and warm-ups were executed.
- [x] Failures and timeouts are logged explicitly (not as zero quality).
- [x] Baseline configurations and versions are documented.

## Analysis
- [x] Aggregation tables are generated from raw logs.
- [x] Plots (e.g., Pareto, distributions) are generated programmatically.
- [x] Statistical tests are documented and reproducible.
- [x] Qualitative samples follow the predefined selection rule.
- [x] Limitations and missing data are declared.

## Documentation
- [x] `README.md` is complete and commands work.
- [x] `REPRODUCIBILITY.md` provides exact steps for reproducing the benchmark.
- [x] `ARCHITECTURE.md` accurately reflects the current implementation.
- [x] Benchmark protocol is documented.
- [x] Citation metadata (`CITATION.cff`, `.zenodo.json`, `codemeta.json`) are updated and match.

## Paper
- [x] Manuscript (`paper/manuscript.md`) is complete (placeholders resolved).
- [x] References (`paper/references.bib`) are verified and canonical.
- [x] Generated figures are linked correctly.
- [x] Generated tables match raw results exactly.
- [x] Supplementary material is attached.
