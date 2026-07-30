# Synthetic Evaluation Dataset

This dataset contains artificially generated graphics (e.g. Robohash, generative APIs) used for robustness and scale testing, but which do not reflect real-world human-crafted vectors.

**Rules:**
- All entries must have `dataset_role=synthetic_evaluation` and `publication_scope=synthetic_analysis`.
- They must not be conflated with the `real_world` benchmark evaluation dataset in official comparative analysis.
- `origin_type` must be explicitly marked as `api_generated` or `synthetic`.
