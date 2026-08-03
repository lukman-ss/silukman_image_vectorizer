# Scaling Pilot Report

## Purpose
Determine the relationship between image pixel count and runtime/quality to define
evidence-based pixel limits for `full-standard-v1.yaml` and `stress-large-images-v1.yaml`.

**Images tested:** 2
**Resolution tiers:** [256, 512, 1024, 2048, None]
**Backends:** ['silukman', 'vtracer']
**Presets:** ['low_complexity', 'balanced', 'high_fidelity']
**Timeout per run:** 120s

## Results by Resolution Tier

| Image | Resolution | Pixels | Backend | Preset | Status | Time (s) | SVG KB | Paths |
|:------|:-----------|-------:|:--------|:-------|:-------|----------:|-------:|------:|
| img_wiki_logo_0 | 256x113 | 28,928 | silukman | low_complexity | success | 0.72 | 12.9 | 55 |
| img_wiki_logo_0 | 256x113 | 28,928 | silukman | balanced | success | 0.39 | 15.0 | 62 |
| img_wiki_logo_0 | 256x113 | 28,928 | silukman | high_fidelity | success | 0.34 | 40.6 | 133 |
| img_wiki_logo_0 | 256x113 | 28,928 | vtracer | low_complexity | success | 0.15 | 7.3 | 55 |
| img_wiki_logo_0 | 256x113 | 28,928 | vtracer | balanced | success | 0.15 | 12.5 | 64 |
| img_wiki_logo_0 | 256x113 | 28,928 | vtracer | high_fidelity | success | 0.29 | 40.4 | 133 |
| img_wiki_logo_0 | 512x227 | 116,224 | silukman | low_complexity | success | 0.25 | 25.9 | 100 |
| img_wiki_logo_0 | 512x227 | 116,224 | silukman | balanced | success | 0.26 | 30.4 | 112 |
| img_wiki_logo_0 | 512x227 | 116,224 | silukman | high_fidelity | success | 0.38 | 58.7 | 213 |
| img_wiki_logo_0 | 512x227 | 116,224 | vtracer | low_complexity | success | 0.16 | 19.1 | 106 |
| img_wiki_logo_0 | 512x227 | 116,224 | vtracer | balanced | success | 0.16 | 23.6 | 116 |
| img_wiki_logo_0 | 512x227 | 116,224 | vtracer | high_fidelity | success | 0.24 | 58.4 | 213 |
| img_wiki_logo_0 | 1024x455 | 465,920 | silukman | low_complexity | success | 0.37 | 49.1 | 207 |
| img_wiki_logo_0 | 1024x455 | 465,920 | silukman | balanced | success | 0.44 | 69.9 | 223 |
| img_wiki_logo_0 | 1024x455 | 465,920 | silukman | high_fidelity | success | 0.36 | 70.4 | 287 |
| img_wiki_logo_0 | 1024x455 | 465,920 | vtracer | low_complexity | success | 0.17 | 38.1 | 207 |
| img_wiki_logo_0 | 1024x455 | 465,920 | vtracer | balanced | success | 0.18 | 44.9 | 213 |
| img_wiki_logo_0 | 1024x455 | 465,920 | vtracer | high_fidelity | success | 0.30 | 70.0 | 287 |
| img_wiki_logo_0 | 1613x718 | 1,158,134 | silukman | low_complexity | success | 0.40 | 52.2 | 30 |
| img_wiki_logo_0 | 1613x718 | 1,158,134 | silukman | balanced | success | 0.54 | 68.3 | 30 |
| img_wiki_logo_0 | 1613x718 | 1,158,134 | silukman | high_fidelity | success | 0.36 | 40.8 | 31 |
| img_wiki_logo_0 | 1613x718 | 1,158,134 | vtracer | low_complexity | success | 0.20 | 27.4 | 30 |
| img_wiki_logo_0 | 1613x718 | 1,158,134 | vtracer | balanced | success | 0.20 | 33.7 | 30 |
| img_wiki_logo_0 | 1613x718 | 1,158,134 | vtracer | high_fidelity | success | 0.30 | 40.6 | 31 |
| img_wiki_logo_0 | 1613x718 | 1,158,134 | silukman | low_complexity | success | 0.39 | 52.2 | 30 |
| img_wiki_logo_0 | 1613x718 | 1,158,134 | silukman | balanced | success | 0.54 | 68.3 | 30 |
| img_wiki_logo_0 | 1613x718 | 1,158,134 | silukman | high_fidelity | success | 0.38 | 40.8 | 31 |
| img_wiki_logo_0 | 1613x718 | 1,158,134 | vtracer | low_complexity | success | 0.20 | 27.4 | 30 |
| img_wiki_logo_0 | 1613x718 | 1,158,134 | vtracer | balanced | success | 0.19 | 33.7 | 30 |
| img_wiki_logo_0 | 1613x718 | 1,158,134 | vtracer | high_fidelity | success | 0.28 | 40.6 | 31 |
| img_001 | 256x170 | 43,520 | silukman | low_complexity | success | 0.34 | 83.5 | 36 |
| img_001 | 256x170 | 43,520 | silukman | balanced | success | 0.81 | 211.3 | 202 |
| img_001 | 256x170 | 43,520 | silukman | high_fidelity | success | 0.49 | 688.4 | 1703 |
| img_001 | 256x170 | 43,520 | vtracer | low_complexity | success | 0.39 | 71.0 | 35 |
| img_001 | 256x170 | 43,520 | vtracer | balanced | success | 0.19 | 243.7 | 227 |
| img_001 | 256x170 | 43,520 | vtracer | high_fidelity | success | 0.24 | 686.6 | 1703 |
| img_001 | 512x341 | 174,592 | silukman | low_complexity | success | 0.54 | 201.8 | 94 |
| img_001 | 512x341 | 174,592 | silukman | balanced | success | 0.74 | 931.0 | 723 |
| img_001 | 512x341 | 174,592 | silukman | high_fidelity | success | 0.96 | 2865.8 | 6610 |
| img_001 | 512x341 | 174,592 | vtracer | low_complexity | success | 0.36 | 308.6 | 122 |
| img_001 | 512x341 | 174,592 | vtracer | balanced | success | 0.39 | 1115.7 | 908 |
| img_001 | 512x341 | 174,592 | vtracer | high_fidelity | success | 0.62 | 2859.2 | 6610 |
| img_001 | 1024x683 | 699,392 | silukman | low_complexity | success | 1.57 | 794.5 | 300 |
| img_001 | 1024x683 | 699,392 | silukman | balanced | success | 2.57 | 3838.8 | 2689 |
| img_001 | 1024x683 | 699,392 | silukman | high_fidelity | success | 5.58 | 12369.2 | 26030 |
| img_001 | 1024x683 | 699,392 | vtracer | low_complexity | success | 0.92 | 1499.5 | 414 |
| img_001 | 1024x683 | 699,392 | vtracer | balanced | success | 1.73 | 4721.4 | 3344 |
| img_001 | 1024x683 | 699,392 | vtracer | high_fidelity | success | 3.08 | 12343.6 | 26030 |
| img_001 | 2048x1367 | 2,799,616 | silukman | low_complexity | success | 2.55 | 2824.3 | 944 |
| img_001 | 2048x1367 | 2,799,616 | silukman | balanced | success | 9.02 | 15153.7 | 9978 |
| img_001 | 2048x1367 | 2,799,616 | silukman | high_fidelity | success | 22.74 | 49126.4 | 99093 |
| img_001 | 2048x1367 | 2,799,616 | vtracer | low_complexity | success | 4.58 | 4270.4 | 1209 |
| img_001 | 2048x1367 | 2,799,616 | vtracer | balanced | success | 9.73 | 18981.9 | 12145 |
| img_001 | 2048x1367 | 2,799,616 | vtracer | high_fidelity | success | 17.88 | 49029.5 | 99093 |
| img_001 | 5495x3669 | 20,161,155 | silukman | low_complexity | success | 24.38 | 22981.6 | 7685 |
| img_001 | 5495x3669 | 20,161,155 | silukman | balanced | success | 73.95 | 87267.6 | 56281 |
| img_001 | 5495x3669 | 20,161,155 | silukman | high_fidelity | timeout | 120.07 | 0.0 | 0 |
| img_001 | 5495x3669 | 20,161,155 | vtracer | low_complexity | failed | 0.69 | 0.0 | 0 |
| img_001 | 5495x3669 | 20,161,155 | vtracer | balanced | failed | 0.14 | 0.0 | 0 |
| img_001 | 5495x3669 | 20,161,155 | vtracer | high_fidelity | failed | 0.14 | 0.0 | 0 |

## Timeout Analysis

- First timeout observed at **20,161,155 pixels**.
- Recommended `max_input_pixels` for standard benchmark: **< 20,161,155** (below first observed timeout).

## Recommended Config Values

> [!NOTE]
> These values must be verified against the actual timeout analysis above before
> populating `full-standard-v1.yaml`.

```yaml
resource_policy:
  max_input_pixels: null  # TBD from scaling pilot — first timeout at ~20,161,155px
  resize_policy: reject
```