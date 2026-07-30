# Dataset Curation Guide

This document details the exact requirements for curating the real-world evaluation dataset for the Silukman Image Vectorizer benchmark.

## 1. Targets and Categories

**Minimum Target:**
- Total images: **60 images minimum**
- Categories: **5 categories minimum**
- Per category: **10 images minimum**

**Target Categories:**
- `logo`
- `icon`
- `flat illustration`
- `complex illustration`
- `photograph`
- `binary graphic`

## 2. Required Metadata Fields

Every curated image MUST have the following fields recorded in `benchmark/datasets/real_world/dataset_manifest.csv`:

1. `image_id`
2. `filename`
3. `category`
4. `source`
5. `source_url`
6. `creator`
7. `license`
8. `license_url`
9. `redistribution_allowed`
10. `attribution`
11. `width`
12. `height`
13. `format`
14. `has_alpha`
15. `sha256`
16. `date_accessed`
17. `notes`
18. `dataset_role` (must be `evaluation`)

## 3. License Rules

We strictly adhere to ethical and legal open-science practices. 

**ACCEPTED Licenses and Sources:**
- `CC0` (Creative Commons Zero)
- Public Domain
- `CC BY` (Creative Commons Attribution)
- Self-made assets explicitly released for this research
- Datasets with explicit redistribution permission

**REJECTED Licenses and Sources:**
- Google Images (without explicit license)
- Paid stock assets (e.g., Shutterstock, Getty)
- Commercial brand logos without explicit permission
- Images with unknown or untraceable sources
- Files restricted to "view only" without redistribution rights
- AI-generated images without clear provenance and usage rules
