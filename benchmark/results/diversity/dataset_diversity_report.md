# Dataset Diversity Audit Report

**Manifest:** `dataset_manifest.csv`  
**Total evaluation images:** 61  
**Dominant source family:** Twemoji (45 images, 73.8%)  
**Twemoji images:** 45 (73.8%)  

> [!WARNING]
> **Style concentration alert:** 73.8% of images (45/61) are from a single source family (Twemoji). Aggregate results will heavily reflect this family's visual style. Do NOT claim broad visual diversity without this caveat.

## 1. Images per Source

| Source | Count | Percentage |
|:-------|------:|-----------:|
| Twemoji | 45 | 73.8% |
| curation_cli | 15 | 24.6% |
| Wikimedia Commons | 1 | 1.6% |
| **Source HHI** | | **0.605** (0=diverse, 1=monopoly) |

## 2. Images per Category

| Category | Count | Percentage |
|:---------|------:|-----------:|
| logo | 13 | 21.3% |
| photograph | 12 | 19.7% |
| binary_graphic | 12 | 19.7% |
| icon | 12 | 19.7% |
| illustration | 12 | 19.7% |

## 3. Images per Resolution Bucket

| Bucket | Count | Percentage |
|:-------|------:|-----------:|
| tiny (≤72×72) | 47 | 77.0% |
| small (≤256×256) | 10 | 16.4% |
| very large (>1920×1080) | 2 | 3.3% |
| large (≤1920×1080) | 2 | 3.3% |
| **Resolution HHI** | | **0.623** |

## 4. Images per Creator (Top 20)

| Creator | Count |
|:--------|------:|
| Twitter, Inc and other contributors | 45 |
| Agnes Monkelbaan | 2 |
| Dietmar Rabich | 1 |
| Nvile Media | 1 |
| إبراهيم الشعيبي | 1 |
| Alistair Cockburn | 1 |
| Vadim Sherbakov | 1 |
| Josefa Holland-Merten | 1 |
| veeterzy | 1 |
| Talia Cohen | 1 |
| Oscar Keys | 1 |
| Maria Carrasco | 1 |
| Namphuong Van | 1 |
| Josh Felise | 1 |
| Caleb George | 1 |
| ThomasSparda | 1 |

## 5. Category × Source Matrix

| Category | curation_cli | Wikimedia Commons | Twemoji |
|:---------|------:|------:|------:|
| binary_graphic | 2 | 0 | 10 |
| icon | 0 | 0 | 12 |
| illustration | 0 | 0 | 12 |
| logo | 1 | 1 | 11 |
| photograph | 12 | 0 | 0 |

## 6. Analysis Without Dominant Source Family

_(Excluding Twemoji: 16 images remaining)_

| Category | Count |
|:---------|------:|
| photograph | 12 |
| logo | 2 |
| binary_graphic | 2 |

| Source | Count |
|:-------|------:|
| curation_cli | 15 |
| Wikimedia Commons | 1 |

## 7. Benchmark Analysis Guidance

When reporting benchmark results, provide ALL of the following views:

1. **Overall aggregate** — all images.
2. **Without Twemoji** — 16 images, eliminates dominant-family bias.
3. **Per source family** — separate stats for each source.
4. **Per category** — separate stats for each category.

> [!IMPORTANT]
> Do NOT claim that logo, illustration, or binary_graphic categories represent a broad
> visual range if >60% of those images come from Twemoji.
