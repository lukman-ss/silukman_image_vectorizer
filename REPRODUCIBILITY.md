# Reproducibility Guide

Panduan ini menggunakan entry point dan script yang tersedia di repository.
Jalankan seluruh perintah dari root repository. Contoh memakai shell POSIX
(Linux/macOS); di Windows gunakan aktivasi virtual environment yang setara.

## 1. Clone

```bash
git clone https://github.com/lukman-ss/silukman_image_vectorizer.git
cd silukman_image_vectorizer
git rev-parse HEAD
```

Simpan SHA dari perintah terakhir bersama laporan eksperimen. Untuk
mereproduksi revisi tertentu, jalankan `git checkout <commit-sha>` sebelum
instalasi.

## 2. Environment setup

Project mendukung Python 3.9–3.11 pada matriks CI saat ini.

```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

## 3. Install

Instal editable beserta dependensi research dan development:

```bash
python -m pip install -e ".[all]"
python -m pip check
python -c "import cv2, numpy, PySide6, vtracer; print('core dependencies: OK')"
```

Baseline opsional membutuhkan executable sistem:

```bash
potrace --version
inkscape --version
```

Perintah tersebut boleh gagal bila baseline terkait tidak akan dipakai. Runner
melewati backend eksternal yang tidak tersedia.

## 4. Dataset preparation

Aturan dataset lengkap berada di
`docs/research/DATASET_PREPARATION.md`. Untuk dataset berlisensi:

1. Simpan image asli tanpa resize atau manipulasi di `benchmark/samples/`.
2. Simpan teks lisensi yang diperlukan di `benchmark/licenses/`.
3. Tambahkan satu baris per image ke `benchmark/dataset_manifest.csv`.
4. Isi `filename`, `image_id`, `category`, `split`, metadata sumber/lisensi, dan
   SHA-256 yang sesuai file.

Repository juga menyediakan generator aset sintetis deterministik:

```bash
python -m benchmark.scripts.generate_synthetic --output benchmark/synthetic --seed 42
```

Generator tersebut menulis image dan `synthetic_manifest.json`; hasilnya tidak
otomatis ditambahkan ke manifest CSV benchmark utama.

## 5. License validation

```bash
python -m benchmark.scripts.validate_dataset
python scripts/validate_research_artifacts.py
```

Validator dataset memastikan field `license` tidak kosong, kategori/split/format
valid, file tersedia, metadata dimensi/alpha konsisten, dan checksum cocok.
Validasi ini **tidak** memverifikasi isi teks lisensi, kecocokan `license_url`,
atau hak redistribusi secara otomatis. Pemeriksaan legal atas sumber dan syarat
lisensi tetap harus dilakukan manual sebelum menjalankan atau menerbitkan
benchmark.

## 6. Run smoke benchmark

Smoke benchmark terisolasi membuat dataset sementara sendiri sehingga dapat
dijalankan pada clone baru:

```bash
python -m pytest tests/integration/test_benchmark_smoke.py -q
```

Untuk smoke test seluruh integrasi vektorisasi:

```bash
python -m pytest tests/integration/test_vectorization.py -q
```

## 7. Run full benchmark

Pastikan manifest mempunyai setidaknya satu row yang cocok dengan `split` dan
`categories` di config. Validasi dahulu, lalu jalankan:

```bash
python -m benchmark.scripts.validate_dataset
silukman-vectorizer benchmark run --config experiments/configs/benchmark-v1.yaml
```

Config bawaan menjalankan kombinasi berikut:

- split `test`;
- kategori `logo` dan `binary_graphic`;
- backend `silukman` dan `vtracer`;
- preset `low_complexity` dan `balanced`;
- dua repetition setelah satu warm-up.

Runner mencetak ID eksperimen dan menulis hasil ke
`experiments/<experiment-id>/`. Jangan membandingkan run dari hardware atau
revisi berbeda tanpa melaporkan perbedaannya.

## 8. Select an experiment directory

Command berikut memilih direktori eksperimen terbaru yang memiliki
`runs.jsonl`:

```bash
EXP_DIR="$(find experiments -mindepth 2 -maxdepth 2 -name runs.jsonl -print | sort | tail -n 1 | xargs dirname)"
test -n "$EXP_DIR"
printf '%s\n' "$EXP_DIR"
```

Jika ingin memakai run tertentu, tetapkan secara eksplisit:

```bash
EXP_DIR="experiments/20260728T060456Z_benchmark-v1_8b0a416_1006634"
```

## 9. Aggregate raw results

Tables dan plots membutuhkan `aggregated.json`:

```bash
silukman-vectorizer benchmark aggregate \
  --input "$EXP_DIR/runs.jsonl" \
  --output "$EXP_DIR/aggregated.json"
```

## 10. Generate tables

```bash
silukman-vectorizer benchmark generate-tables --exp-dir "$EXP_DIR"
```

Output ditulis ke `$EXP_DIR/tables/` dalam format yang dibuat oleh
`benchmark.analysis.table_generator`, termasuk CSV, Markdown, dan LaTeX.

## 11. Generate plots

```bash
silukman-vectorizer benchmark generate-plots --exp-dir "$EXP_DIR"
```

Output ditulis ke `$EXP_DIR/plots/`. Pembuatan plot memerlukan data agregat yang
berisi metric yang digunakan generator.

Untuk menghasilkan agregasi, tabel, figure, analisis kegagalan, dan laporan
dalam satu workflow:

```bash
silukman-vectorizer benchmark report --run "$EXP_DIR"
```

## 12. Inspect raw results

Validasi setiap baris sebagai JSON dan tampilkan ringkasan status:

```bash
python - "$EXP_DIR/runs.jsonl" <<'PY'
import collections
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
print("rows:", len(rows))
print("status:", dict(collections.Counter(row.get("status") for row in rows)))
for row in rows:
    if row.get("status") != "success":
        print(row.get("run_id"), row.get("error_category"), row.get("error_message"))
PY
```

Untuk memeriksa satu SVG keluaran:

```bash
SVG_FILE="$(find "$EXP_DIR/outputs" -type f -name '*.svg' -print | sort | head -n 1)"
test -n "$SVG_FILE"
silukman-vectorizer inspect "$SVG_FILE" --json
```

## 13. Rerun failed cases

Gunakan ID direktori, bukan path penuh. Resume hanya diterima jika hash config
masih sama dengan run awal.

```bash
EXP_ID="$(basename "$EXP_DIR")"
silukman-vectorizer benchmark run \
  --config experiments/configs/benchmark-v1.yaml \
  --resume-id "$EXP_ID" \
  --retry-failed
```

Tanpa `--retry-failed`, run yang sudah tercatat—termasuk kegagalan—akan
dilewati.

## 14. Verify checksums

Validator utama membandingkan SHA-256 aktual setiap sample dengan kolom
`sha256` manifest:

```bash
python -m benchmark.scripts.validate_dataset --json
```

Untuk audit independen seluruh row:

```bash
python - <<'PY'
import csv
import hashlib
import pathlib

root = pathlib.Path("benchmark")
failed = False
with (root / "dataset_manifest.csv").open(encoding="utf-8", newline="") as handle:
    for row in csv.DictReader(handle):
        path = root / "samples" / row["filename"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        ok = actual.lower() == row["sha256"].lower()
        print(("OK" if ok else "MISMATCH"), row["image_id"], path)
        failed |= not ok
raise SystemExit(1 if failed else 0)
PY
```

## 15. Expected folder structure

Sebelum run:

```text
benchmark/
├── dataset_manifest.csv
├── dataset_manifest.schema.json
├── licenses/
│   └── <license-text>
└── samples/
    └── <image files>

experiments/
└── configs/
    └── benchmark-v1.yaml
```

Sesudah benchmark dan report:

```text
experiments/<experiment-id>/
├── aggregated.json
├── logs/
├── manifest.json
├── outputs/
├── plots/
├── report/
├── runs.jsonl
├── summary.json
├── tables/
└── tmp/
```

Sebagian direktori hanya muncul setelah tahap yang membuatnya. `runs.jsonl`
adalah sumber data mentah; simpan bersama `manifest.json`, config asli, Git SHA,
dan informasi environment.

## 16. Troubleshooting

### `No valid backends available to run`

Pastikan paket proyek dan VTracer terpasang:

```bash
python -m pip install -e ".[all]"
python -c "import vtracer; print('vtracer import: OK')"
```

Untuk Potrace atau Inkscape, instal executable sistem atau hapus nama backend
tersebut dari YAML.

### Dataset kosong atau warm-up gagal

Periksa bahwa row manifest cocok dengan filter config:

```bash
python -m benchmark.scripts.validate_dataset
python - <<'PY'
from benchmark.runner.config_schema import BenchmarkConfig
from benchmark.runner.experiment_runner import ExperimentRunner

runner = ExperimentRunner("experiments/configs/benchmark-v1.yaml")
print("matching rows:", len(runner._load_dataset()))
PY
```

Perintah diagnostik terakhir membuat objek runner dan dapat membuat nama
eksperimen di memori, tetapi belum menjalankan benchmark.

### `Config hash mismatch`

Resume mengharuskan file YAML identik dengan config awal. Kembalikan config
tersebut atau mulai eksperimen baru tanpa `--resume-id`.

### Plot tidak dapat dibuat

Pastikan agregasi sudah dijalankan dan dependensi research terpasang:

```bash
test -f "$EXP_DIR/aggregated.json"
python -m pip install -e ".[research]"
silukman-vectorizer benchmark generate-plots --exp-dir "$EXP_DIR"
```

### Qt gagal pada mesin headless

Rasterizer benchmark memakai PySide6. Pada Linux tanpa display, coba:

```bash
export QT_QPA_PLATFORM=offscreen
python -m pytest tests/integration/test_benchmark_smoke.py -q
```

### Dataset validator melaporkan checksum mismatch

Jangan mengubah checksum untuk menyembunyikan perubahan yang tidak disengaja.
Pulihkan file sumber yang benar, atau perlakukan file yang memang berubah
sebagai aset baru dan perbarui manifest serta provenance secara sadar.

