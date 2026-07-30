# Real-World Dataset Curation Guide

This document outlines the strict guidelines and standard operating procedures (SOP) for compiling the real-world dataset intended for evaluating the Silukman Image Vectorizer.

## Objective
The dataset must consist of fully reproducible, legally safe, and diverse images that reflect real-world use cases (logos, icons, illustrations, photographs, etc.).

## 1. Allowed Categories
Images must strictly fall into one of the following categories:
- `logo`: Brand or product logos.
- `icon`: UI/UX icons, pictograms, glyphs.
- `flat illustration`: Vector-style graphics without complex gradients.
- `complex illustration`: Vector-style graphics with detailed shading, gradients, or meshes.
- `photograph`: Real-world pictures (raster native).
- `binary graphic`: Black and white scans, line art, or text documents.

**Target Minimum**: 10 images per category. **Ideal Target**: 15–20 images per category (90–120 images total).

## 2. License and Legal Requirements
**WARNING**: Do NOT scrape Google Images or use assets with unknown provenance.

All images must have an explicit license allowing:
1. Research use and processing.
2. Redistribution (sharing the original and vectorized outputs).
3. Public archiving (e.g., in a Zenodo repository).

### Allowed Licenses
- **CC0 (Creative Commons Zero)** / Public Domain
- **CC BY (Creative Commons Attribution)**
- Assets explicitly created by the authors for this project (must be stated).
- Dataset sources with explicit redistribution rights for research.

### Rejected Sources
- Copyrighted photos without explicit permission.
- Commercial logos without fair-use/research clauses allowing redistribution.
- Paid stock images.
- AI-generated images lacking explicit terms of use and source metadata.

## 3. Recommended Legal Sources
1. **Wikimedia Commons**: High-quality public domain and CC BY assets.
2. **Unsplash / Pexels**: Use strictly according to their license (usually permits modification and redistribution, but double-check).
3. **SVG Repo / Flaticon (Free tiers)**: Ensure the specific icon's license allows redistribution.
4. **OpenClipArt**: Public domain vector/raster conversions.
5. **Government/Public Archives**: NASA, Library of Congress (verify public domain status).

## 4. Manual Curation Checklist per Image
Before adding an image to the `benchmark/datasets/real_world/` folder, complete this checklist:
- [ ] Is the image visually clear and relevant to the category?
- [ ] Is the source URL recorded?
- [ ] Is the creator identified?
- [ ] Is the exact license identified (e.g., CC BY 4.0)?
- [ ] Does the license permit redistribution (`redistribution_allowed: true`)?
- [ ] Has the checksum (SHA-256) been generated?
- [ ] Is the attribution string properly formatted?

## 5. Adding to the Manifest
Update the real-world dataset manifest JSON/CSV. Ensure `dataset_role` is set to `evaluation`. Do NOT populate the real-world manifest with synthetic data or fake data.

The validation script (`benchmark/scripts/validate_dataset.py`) will automatically reject any evaluation image missing mandatory legal fields.
