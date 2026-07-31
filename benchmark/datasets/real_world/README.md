# Real-World Evaluation Dataset

**Status: SUFFICIENT (61 / 60 images)**

This dataset is intended for the official benchmark evaluation of the Silukman Image Vectorizer. It strictly contains exclusively real-world images from the following categories:
- Logos
- Icons
- Flat illustrations
- Complex illustrations
- Photographs
- Binary graphics

**Strict Provenance Rules:**
- API-generated images (e.g. Robohash) are NOT allowed in this dataset and must be moved to `synthetic_evaluation`.
- API-delivered images (e.g. Unsplash/Lorem Picsum) MUST fetch and verify the true original author and original asset URL. Generic attributions like "Unsplash Contributors" are rejected.
- Wikimedia Commons images MUST verify that the `license` exactly matches the `license_url` terms (e.g. CC BY-SA 4.0 cannot be listed as CC0).

Images are placed in `images/`, and their corresponding licenses in `licenses/`. The metadata is tracked in `dataset_manifest.csv` with `dataset_role=evaluation` and appropriate `origin_type` (e.g. `external_real_world`, `api_delivered_real_world`).

For curation guidelines, attribution rules, and valid legal sources, please refer to the `docs/research/CURATION_GUIDE.md` and `docs/research/ATTRIBUTION_TEMPLATE.md`.
