
manuscript_path = 'paper/manuscript.md'
provenance_path = 'paper/MANUSCRIPT_DATA_PROVENANCE.md'

with open(manuscript_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Identify all synthetic values
replacements = {
    "`10` images from `10` categories": "[REAL_WORLD_DATASET_SIZE] images from [REAL_WORLD_CATEGORY_COUNT] categories",
    "`1 (Silukman)`": "[REAL_WORLD_BASELINES]",
    "`mean SSIM of 0.8793`": "[REAL_WORLD_PRIMARY_METRIC]",
    "`an average of 0.05-0.06 seconds per image`": "[REAL_WORLD_RUNTIME_RESULT]",
    "`0.0% failure rate`": "[REAL_WORLD_FAILURE_RATE]",
    "`10` images across `10` categories": "[REAL_WORLD_DATASET_SIZE] images across [REAL_WORLD_CATEGORY_COUNT] categories",
    "`balanced preset achieved 0.9053 SSIM vs low_complexity 0.8533`": "[REAL_WORLD_COMPLEXITY_RESULT]",
}

for old, new in replacements.items():
    content = content.replace(old, new)

# Move Generated Manuscript Snippets to Synthetic Smoke-Test Validation
snippets_marker = "## Generated Manuscript Snippets"
if snippets_marker in content:
    parts = content.split(snippets_marker)

    synthetic_section = """
## Synthetic Smoke-Test Validation

Pernyataan eksplisit: Hasil sintetis di bawah ini HANYA membuktikan bahwa:
- pipeline dapat dijalankan;
- output dapat dihasilkan;
- metrik dapat dihitung;
- artefak eksperimen dapat disimpan.
Hasil ini BUKAN representasi performa pada dunia nyata, karena dataset yang digunakan murni buatan (sintetis).
"""

    content = parts[0] + synthetic_section + parts[1]


with open(manuscript_path, 'w', encoding='utf-8') as f:
    f.write(content)

provenance_content = """# MANUSCRIPT DATA PROVENANCE

| Klaim | Lokasi Manuscript | Experiment ID | Raw Result Source | Status Validasi | Boleh Masuk Paper |
|---|---|---|---|---|---|
| `10` images | 844, 1342, 1707 | 20260729T..._preprint_simulation | dataset_manifest.csv | Valid (Synthetic) | Tidak |
| `10` categories | 844, 1342, 1707 | 20260729T..._preprint_simulation | dataset_manifest.csv | Valid (Synthetic) | Tidak |
| `1 (Silukman)` | 844, 1707 | 20260729T..._preprint_simulation | summary.json | Valid (Synthetic) | Tidak |
| `mean SSIM of 0.8793` | 846, 1707 | 20260729T..._preprint_simulation | runs.jsonl / summary.json | Valid (Synthetic) | Tidak |
| `an average of 0.05-0.06 seconds per image` | 846, 1707 | 20260729T..._preprint_simulation | runs.jsonl / summary.json | Valid (Synthetic) | Tidak |
| `0.0% failure rate` | 846, 1707 | 20260729T..._preprint_simulation | summary.json | Valid (Synthetic) | Tidak |
| `balanced preset achieved 0.9053 SSIM vs low_complexity 0.8533` | 1707 | 20260729T..._preprint_simulation | runs.jsonl / summary.json | Valid (Synthetic) | Tidak |
| `mean quality = 0.9772` dll (geometric_shapes dsb) | 1732-1742 | 20260729T..._preprint_simulation | runs.jsonl / summary.json | Menyesatkan (Kategori Palsu) | Tidak |

*Catatan: Seluruh data di atas berasal dari run benchmark smoke test sintetis. Data tersebut valid sebagai artefak simulasi tetapi menyesatkan jika disajikan sebagai evaluasi nyata.*
"""

with open(provenance_path, 'w', encoding='utf-8') as f:
    f.write(provenance_content)

print("Manuscript restored and provenance file created.")
