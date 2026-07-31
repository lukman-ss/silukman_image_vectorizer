# Pre-Benchmark Gate Report

This report tracks the formal conditions required before `FULL_BENCHMARK` can be executed.
All code quality, dataset integrity, and pilot methodological validations must pass.

## Current Gate Status

**Status: FULL_BENCHMARK_BLOCKED**

**Blocking Reason(s):**
* Real-world evaluation dataset has not reached the required size and category coverage (API-generated images not eligible for real-world evaluation have been removed/quarantined following an audit).

## Verification History

| Command | Exit Code | Result | Timestamp | Commit SHA |
| :--- | :--- | :--- | :--- | :--- |
| `.venv/bin/python -m pytest tests/` | 0 | 134 passed, 5 skipped | 2026-07-31T06:39:20Z | `c9892b65c4893b238259dd76812a93f681cf1a64` |
| `.venv/bin/python -m mypy benchmark app tests scripts paper --ignore-missing-imports` | 0 | 0 errors | 2026-07-31T06:39:20Z | `c9892b65c4893b238259dd76812a93f681cf1a64` |
| `.venv/bin/python -m flake8 benchmark app tests scripts paper` | 0 | 0 errors | 2026-07-31T06:39:20Z | `c9892b65c4893b238259dd76812a93f681cf1a64` |
| `.venv/bin/python scripts/validate_research_artifacts.py` | 0 | All validated | 2026-07-31T06:39:20Z | `c9892b65c4893b238259dd76812a93f681cf1a64` |
| `.venv/bin/python -m app.cli_headless dataset status --manifest benchmark/datasets/real_world/dataset_manifest.csv` | 1 | REAL_WORLD_DATASET_INSUFFICIENT | 2026-07-31T06:39:20Z | `c9892b65c4893b238259dd76812a93f681cf1a64` |

## Audit Checklist

*   [x] `benchmark/results/` root contains no raw experiment folders.
*   [x] All historical smoke results are isolated in `benchmark/results/smoke/`.
*   [x] Smoke manifest explicitly defines `publication_eligible=false`.
*   [ ] Real-world dataset has reached the minimum criteria (60 images, 5 categories).
*   [x] Manuscript placeholders `[REPETITION_COUNT]`, `[WARMUP_COUNT]`, and `[PRESET_COUNT]` are used.
*   [x] No hardcoded numbers exist in the manuscript for experiment configurations.
*   [ ] Pilot benchmark completed successfully without any methodological blockers (Must re-run when dataset is ready).

---

## Conclusion

**Status: `FULL_BENCHMARK_BLOCKED`**

All code quality, methodology, tooling, and structural requirements are fully satisfied.
The sole remaining blocker is:

> **The real-world dataset has not reached 60 images, five categories, and at least ten images per included category.**

No pilot benchmark can run until at least 60 authentic real-world images across at least 5 categories (≥ 10 per category) are added.
