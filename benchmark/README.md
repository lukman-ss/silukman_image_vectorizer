# Silukman Image Vectorizer Benchmark Dataset

This directory contains the experimental benchmark dataset used for evaluating the performance and visual fidelity of the `silukman_image_vectorizer` application.

## Principles
- **Reproducibility**: All images are cataloged in `dataset_manifest.csv` with their precise SH256 checksums.
- **Licensing Compliance**: Only images with explicitly open licenses (e.g., CC0, public domain, MIT) that permit redistribution are included. No images with ambiguous licensing are allowed.
- **Diversity**: The dataset covers a wide range of graphic types, including logos, icons, complex artwork, photographs, and binary graphics.

## Structure

```text
benchmark/
├── README.md                      # This documentation file
├── dataset_manifest.csv           # Central registry of all dataset images
├── dataset_manifest.schema.json   # JSON Schema defining the manifest structure
├── categories.json                # Standardized category definitions
├── licenses/                      # Full text of licenses used by the dataset images
├── samples/                       # The actual image files
└── scripts/                       # Helper scripts for dataset generation, hashing, and validation
```

## Adding Images

1. Verify the license permits redistribution.
2. Place the image file in the `samples/` directory.
3. If not already present, copy the full license text into the `licenses/` directory.
4. Calculate the SHA256 checksum of the file.
5. Append a new row to `dataset_manifest.csv` adhering to `dataset_manifest.schema.json`.
