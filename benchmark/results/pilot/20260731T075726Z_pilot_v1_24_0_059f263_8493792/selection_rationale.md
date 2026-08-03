# Pilot Dataset Selection Rationale

## Subset Strategy
The pilot benchmark used a 10-image subset (2 images per category) selected to:
- Cover all 5 required categories: photograph, logo, binary_graphic, icon, illustration
- Represent diverse source origins (Wikimedia Commons, Twemoji, Lorem Picsum)
- Intentionally mix resolutions (72×72 Twemoji vs 256×256 photographs)

## Pilot Image Selection
| image_id | category | resolution | source |
|:---------|:---------|:-----------|:-------|
| img_007 | photograph | 256×256 | Lorem Picsum |
| img_008 | photograph | 256×256 | Lorem Picsum |
| img_wiki_logo_0 | logo | variable | Wikimedia Commons |
| img_twemoji_1 | logo | 72×72 | Twemoji |
| img_005 | binary_graphic | 216×217 | Wikimedia Commons |
| img_twemoji_36 | binary_graphic | 72×72 | Twemoji |
| img_twemoji_12 | icon | 72×72 | Twemoji |
| img_twemoji_13 | icon | 72×72 | Twemoji |
| img_twemoji_24 | illustration | 72×72 | Twemoji |
| img_twemoji_25 | illustration | 72×72 | Twemoji |

## Infrastructure Blocker Found
The original pilot manifest included `img_001` (5495×3669, 20MP) and `img_002` (5184×3308, 17MP).
Processing these on `high_fidelity` preset caused execution times exceeding 20 minutes per
repetition. These were replaced with `img_007` and `img_008` (256×256) for this pilot run.

The infrastructure fix (hard timeout via process isolation) was implemented in v1.27.0.
