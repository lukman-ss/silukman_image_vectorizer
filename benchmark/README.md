# Silukman Image Vectorizer Benchmark Dataset

This directory contains the dataset architecture for evaluating the `silukman_image_vectorizer` application.

## Dataset Status

- **Real-world evaluation dataset status**: NOT POPULATED
- **Synthetic dataset status**: AVAILABLE FOR TESTING ONLY

## Architecture: Synthetic vs. Real-World

The dataset is strictly divided into two distinct subsets to prevent synthetic benchmarks from being passed off as real-world results:

1. **Synthetic Dataset** (`datasets/synthetic/`):
   - **Role**: `testing_only`
   - Dynamically generated images (shapes, gradients, noisy edges) used for CI pipelines, regression tests, and deterministic behavior checks.
   - **Publication Eligibility**: Results from this dataset MUST NOT be used for the main evaluation in the research manuscript.

2. **Real-World Dataset** (`datasets/real_world/`):
   - **Role**: `evaluation`
   - A manually curated collection of real-world images used for the final benchmark evaluation.
   - **Publication Eligibility**: Only results derived from this dataset may be reported as actual performance in publications.

## Results Organization

Experiment outputs in `benchmark/results/` are cleanly separated by their validation logic:
- `smoke/`: Contains outputs from `testing_only` datasets (such as synthetic benchmarks). These runs have `publication_eligible: false` in their manifest and are actively ignored by the main table generators and analysis scripts.
- `evaluation/`: Contains outputs strictly from full benchmarks running on the real-world dataset. These are the only valid outputs eligible for the research manuscript.

## Planned Categories

The evaluation dataset is planned to cover diverse graphic types:
- Logos
- Icons
- Flat illustrations
- Complex illustrations
- Photographs
- Binary graphics

*Note: Currently, the real-world dataset is empty. Claims regarding performance on these categories cannot be made until the dataset is populated.*

## Dataset Roles

The `dataset_role` attribute in the manifest strictly controls how an image is processed during benchmarking:
- `testing_only`: Allowed only for local smoke tests or regression validation.
- `evaluation`: Allowed for the full reproducible benchmark run.
- `qualitative_only`: Excluded from quantitative statistical analysis.

## How to Populate the Dataset

1. Follow the guidelines in `docs/research/CURATION_GUIDE.md` to select legally compliant images.
2. Place the image in `benchmark/datasets/real_world/images/`.
3. Save the full license text in `benchmark/datasets/real_world/licenses/`.
4. Add a new row to `benchmark/datasets/real_world/dataset_manifest.csv` ensuring all mandatory legal metadata (`license`, `source`, `redistribution_allowed`, `dataset_role=evaluation`, `attribution`) are filled correctly according to the schema.

## How to Validate

Before running an experiment, the dataset must pass the strict validation script:
```bash
.venv/bin/python benchmark/scripts/validate_dataset.py \
    --manifest benchmark/datasets/real_world/dataset_manifest.csv \
    --schema benchmark/real_world_manifest.schema.json \
    --samples benchmark/datasets/real_world/images/
```

The validator will reject any `evaluation` image that is missing proper legal provenance, licensing, or checksums.
