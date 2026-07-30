# Pre-Benchmark Gate Report

This report tracks the formal conditions required before `FULL_BENCHMARK` can be executed.
All code quality, dataset integrity, and pilot methodological validations must pass.

## Current Gate Status

**Status: FULL_BENCHMARK_APPROVED**

*The evaluation dataset is populated, and the pilot benchmark executed successfully without blockers.*

## Verification History

| Command | Exit Code | Result | Timestamp | Commit SHA |
| :--- | :--- | :--- | :--- | :--- |
| `.venv/bin/python -m pytest tests/` | 0 | 134 passed, 5 skipped | 2026-07-30T07:18:04Z | `working-tree` |
| `.venv/bin/python -m mypy benchmark app tests scripts paper --ignore-missing-imports` | 0 | 0 errors | 2026-07-30T07:18:30Z | `working-tree` |
| `.venv/bin/python -m flake8 benchmark app tests scripts paper` | 0 | 0 errors | 2026-07-30T07:18:30Z | `working-tree` |
| `.venv/bin/python scripts/validate_research_artifacts.py` | 0 | All validated | 2026-07-30T07:18:30Z | `working-tree` |
| `.venv/bin/python -m app.cli_headless dataset status --manifest benchmark/datasets/real_world/dataset_manifest.csv` | 0 | DATASET_READY_FOR_PILOT_BENCHMARK | 2026-07-30T07:11:35Z | `working-tree` |

## Audit Checklist

*   [x] `benchmark/results/` root contains no raw experiment folders.
*   [x] All historical smoke results are isolated in `benchmark/results/smoke/`.
*   [x] Smoke manifest explicitly defines `publication_eligible=false`.
*   [x] Real-world dataset has reached the minimum criteria (60 images, 5 categories).
*   [x] Manuscript placeholders `[REPETITION_COUNT]`, `[WARMUP_COUNT]`, and `[PRESET_COUNT]` are used.
*   [x] No hardcoded numbers exist in the manuscript for experiment configurations.
*   [x] Pilot benchmark completed successfully without any methodological blockers.

---

## Conclusion

**Status: `READY_FOR_FULL_BENCHMARK`**

All requirements met. Proceeding to final production runs using `benchmark-v1.yaml`.

---

## Next Steps

**Step 1** — Execute pilot confirmation (if not already done):
```bash
.venv/bin/python benchmark/run_simulation.py \
  --config experiments/configs/pilot-v1.yaml
```

**Step 2** — Run full benchmark:
```bash
.venv/bin/python benchmark/run_simulation.py \
  --config experiments/configs/benchmark-v1.yaml
```
