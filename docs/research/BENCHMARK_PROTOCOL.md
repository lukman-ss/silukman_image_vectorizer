# Benchmark Protocol

Dokumen ini mendefinisikan protokol evaluasi yang sesuai dengan runner,
evaluator, dan analysis suite saat ini. Nilai eksperimen konkret harus disimpan
di YAML, `runs.jsonl`, dan `manifest.json`; dokumen ini tidak menggantikan
artefak tersebut.

## Research questions

Benchmark dirancang untuk menjawab pertanyaan berikut tanpa mengasumsikan satu
konfigurasi selalu terbaik:

1. Bagaimana perbedaan kesetiaan raster, kompleksitas SVG, runtime, dan memori
   antarbackend pada image yang sama?
2. Bagaimana preset mengubah trade-off kesetiaan, kompleksitas, dan performa?
3. Apakah pola hasil berbeda menurut kategori image?
4. Berapa tingkat kegagalan, timeout, atau skip setiap backend?
5. Apakah perbedaan dua konfigurasi konsisten pada pasangan image yang sama?

Jawaban harus dibatasi pada dataset, versi software, hardware, dan konfigurasi
yang benar-benar diuji.

## Dataset

Sumber data adalah CSV yang ditunjuk oleh `dataset.manifest`. Setiap row minimal
memiliki `image_id`, `filename`, `category`, `license`, dan `sha256`. Runner
memilih row dengan equality pada `dataset.split` dan membership pada
`dataset.categories`, lalu mengambil file relatif terhadap direktori manifest.

Sebelum run:

```bash
python -m benchmark.scripts.validate_dataset
```

Validator memeriksa identitas unik, kategori/split/format, keberadaan file,
checksum, dimensi, alpha, dan field lisensi yang tidak kosong. Validitas hukum
lisensi dan provenance tetap diperiksa manual.

## Categories

Kategori standar:

- `logo`
- `icon`
- `illustration`
- `complex_artwork`
- `photograph`
- `binary_graphic`

Analisis lintas kategori hanya boleh dilakukan jika setiap kategori mempunyai
jumlah sample yang dilaporkan. Dataset tidak boleh diklaim mewakili distribusi
image umum tanpa bukti sampling yang mendukung.

Evaluasi formal `real_world` secara ketat melarang penggunaan data sintetis/generated (seperti Robohash). Data yang dihasilkan oleh API generator harus dipisahkan ke dataset `synthetic_evaluation` dan dianalisis terpisah. Setiap citra `real_world` harus tervalidasi lisensinya dan penciptanya (provenance diverifikasi).

## Backends

Registry runner mendukung:

| Backend | Implementasi | Catatan protokol |
|---|---|---|
| `silukman` | Pipeline Silukman dengan preprocessing, backend terpilih preset, dan postprocessing. | Preset bawaan saat ini memilih VTracer. |
| `vtracer` | Binding VTracer langsung dengan subset parameter VTracer dari preset. | Preprocessing khusus Silukman tidak dijalankan. |
| `potrace` | Potrace CLI setelah konversi menjadi BMP 1-bit. | Hanya fair untuk `binary_graphic` dan `monochrome_silhouette`; kategori lain harus skip. |
| `inkscape` | Inkscape CLI dengan action Trace Bitmap. | Parameter tracing diperlakukan sebagai black-box preference fallback dan harus dicatat. |

Versi backend dan executable dicatat dalam environment manifest. Backend yang
tidak tersedia dilewati saat inisialisasi.

## Presets

Preset yang valid berasal dari `app/config/presets.json`:
`low_complexity`, `balanced`, dan `high_fidelity`. Nama preset membentuk sumbu
eksperimen; setiap backend aktif dijalankan untuk setiap preset.

Untuk perbandingan Silukman–VTracer direct, keyword VTracer yang sama dipetakan
dari preset. Parameter preprocessing Silukman yang tidak memiliki padanan
VTracer direct harus dilaporkan sebagai perbedaan pipeline, bukan disamarkan.

## Repetitions

`experiment.repetitions` menentukan jumlah run terukur per kombinasi:

```text
image × backend × preset × repetition
```

Config referensi `experiments/configs/benchmark-v1.yaml` memakai dua repetition.
Gunakan jumlah lebih besar bila inferensi statistik diperlukan dan laporkan
nilai aktual. Run ID menyertakan nomor repetition dan resume tidak mengulang run
yang sudah tercatat kecuali kebijakan retry berlaku.

## Warm-up

`experiment.warmup_runs` default 1. Runner melakukan warm-up per backend memakai
image pertama dan preset pertama sebelum timer run utama. Warm-up tidak dicatat
sebagai observasi.

Urutan ini berarti warm-up tidak mencakup seluruh kombinasi preset atau kategori.
Dataset harus tidak kosong; jika tidak ada row yang cocok dengan filter, full
benchmark tidak valid.

## Timeout

`experiment.timeout_seconds` default 60 detik dan diteruskan ke Potrace serta
Inkscape. External process dijalankan tanpa shell dan process group dihentikan
saat timeout.

Backend Python sinkron (`silukman` dan `vtracer`) belum memiliki hard timeout
yang benar-benar menghentikan eksekusi. Field timeout pada performance tracker
hanya dilaporkan untuk jalur tersebut. Karena itu, “timeout 60 detik untuk semua
backend” tidak boleh diklaim.

## Hardware reporting

Setiap eksperimen harus menyimpan:

- OS, release, architecture, dan versi Python;
- model CPU dan jumlah logical CPU;
- total RAM;
- versi package dari `pip freeze`;
- versi VTracer, Potrace, Inkscape, serta Git commit/status;
- konfigurasi eksperimen dan hash-nya.

Environment capture ditulis ke `manifest.json`. Jalankan seluruh konfigurasi
yang dibandingkan pada mesin dan kondisi sistem yang sama. Laporkan bahwa
pengukuran memory native berbeda antarplatform: `resource.getrusage` digunakan
di macOS/Linux, sedangkan Windows memakai `tracemalloc` yang tidak menangkap
seluruh alokasi C/Rust.

## Metrics

Evaluator merasterisasi SVG ke dimensi raster asli, lalu menghitung:

| Kelompok | Metric |
|---|---|
| Pixel | MAE, RMSE, PSNR |
| Struktur | SSIM |
| Warna | histogram correlation dan histogram distance |
| Edge | precision, recall, F1 |
| Kompleksitas SVG | byte size, element count, path count, command count, group count, depth, metadata/style/gradient counts |
| Performa | wall-clock time, CPU time, peak memory jika tersedia |

Metric raster mengukur kemiripan setelah SVG dirasterisasi, bukan seluruh sifat
vektor. Metric kompleksitas bersifat deskriptif dan tidak otomatis berarti
lebih baik atau lebih buruk.

## Statistical analysis

Aggregator:

- hanya memasukkan run `success` dan nilai numerik non-null ke statistik metric;
- tetap menghitung status success/failed/skipped;
- melaporkan count, mean, median, sample standard deviation, min, max, p25, p75,
  IQR, raw observations, dan 95% t-interval jika `n > 1` dan variasi nonzero;
- menandai outlier di luar 1.5×IQR, tetapi tidak menghapusnya;
- memberi warning jika jumlah success overall kurang dari tiga.

Paired comparison memakai median per image untuk dua konfigurasi pada common
successful images, lalu melaporkan delta, wins/ties/losses, paired Cohen's
`d`, dan Wilcoxon signed-rank hanya bila setidaknya sepuluh delta nonzero.
P-value tidak boleh ditafsirkan sebagai ukuran efek, dan banyak pengujian metric
memerlukan koreksi multipel yang belum diterapkan otomatis.

## Failure handling

Crash, invalid output, timeout, dan resource error harus dipertahankan sebagai
record `failed`; incompatibility yang disengaja dicatat `skipped`. Metric yang
tidak dapat dihitung tetap `null`, bukan nol. `runs.jsonl` bersifat append-safe
dan setiap record membawa error list, hash input/output, config hash, dan
referensi environment.

Analisis kualitas tidak boleh menghapus kegagalan diam-diam. Selalu laporkan
failure rate bersama statistik success-only.

## Fairness

Aturan utama:

- gunakan file dan resolusi input yang sama;
- jangan tune satu backend memakai test split;
- jangan menghapus sample karena hasilnya buruk;
- gunakan mapping parameter identik jika konsepnya benar-benar sepadan;
- laporkan preprocessing yang hanya dimiliki satu pipeline;
- bandingkan hanya common successful images untuk uji paired, sambil tetap
  melaporkan kegagalan di luar pasangan;
- jangan menyamakan kemampuan Potrace, Inkscape, VTracer, dan Silukman.

Rincian tambahan berada di `docs/research/BASELINE_FAIRNESS.md`.

## Exclusion criteria

Image boleh dikeluarkan sebelum eksperimen hanya jika:

- gagal memenuhi schema atau checksum;
- file hilang, korup, atau tidak dapat dibaca;
- lisensi/provenance tidak memadai;
- berada di luar split/kategori yang dideklarasikan;
- tidak kompatibel secara prinsip dengan backend, dan kasus tersebut dicatat
  sebagai `skipped` untuk backend tersebut.

Hasil buruk, runtime lambat, atau kegagalan backend bukan alasan menghapus image
setelah run dimulai. Seluruh exclusion harus ditetapkan sebelum melihat hasil
test dan dicatat.

## Qualitative selection rule

Generator memilih, untuk setiap kategori, image dengan SSIM rata-rata terburuk,
median, dan terbaik pada konfigurasi referensi `silukman:balanced`. Untuk setiap
image terpilih, sheet memakai repetition pertama dari setiap konfigurasi yang
berhasil.

Keterbatasannya:

- pemilihan membutuhkan run sukses `silukman:balanced`;
- kode memakai mean antar-repetition untuk selection walaupun statistik utama
  sering mengutamakan median;
- image tanpa SSIM tidak dapat dipilih;
- sheet saat ini mencantumkan placeholder output SVG, bukan embed raster asli.

Aturan harus ditetapkan sebelum inspeksi manual. Jangan mengganti sample terpilih
karena tampilan tidak mendukung narasi.

## Reproducibility

Ikuti `REPRODUCIBILITY.md`. Minimum artefak yang disimpan:

- Git commit dan dirty state;
- YAML config asli dan config hash;
- dataset manifest serta checksum setiap input;
- `manifest.json`, `runs.jsonl`, dan `summary.json`;
- output SVG dan output hash;
- hasil agregasi, tabel, plot, serta laporan;
- log failure dan daftar exclusion.

Run dapat dilanjutkan memakai `--resume-id`; config hash harus identik. Failed
case hanya diulang dengan `--retry-failed`.

