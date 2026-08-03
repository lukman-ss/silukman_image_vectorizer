# Reproducibility Statement

## Source Integrity
- **Git Commit**: `unknown`
- **Data Provenance**: All tables and figures in this report are deterministically derived from `runs.jsonl`.
- **Exclusion Rule**: Failed runs are strictly isolated but NOT hidden. Mean/Median metrics naturally ignore failed subsets.
- **Environment**: Full OS, hardware, and dependency snapshots are stored in `manifest.json`.

To rerun this exact experiment:
`silukman-vectorizer benchmark run --resume-id 20260731T075726Z_pilot_v1_24_0_059f263_8493792 --retry-failed`
