# Vectorization Parameter Reference

Dokumen ini mencatat seluruh field pada
`app.config.settings.VectorizationConfig` sebagaimana dipakai oleh implementasi
saat ini. Efek yang dijelaskan adalah konsekuensi algoritmik yang diharapkan,
bukan klaim peningkatan kualitas. Penentuan kualitas harus memakai hasil
benchmark pada dataset, mesin, dan konfigurasi yang dilaporkan.

## Preset bawaan

Nilai preset berasal dari `app/config/presets.json`. Field yang tidak ditulis
oleh preset memakai default dataclass.

| Preset | Backend | Tujuan konfigurasi, bukan hasil terukur |
|---|---|---|
| `low_complexity` | VTracer | Mengurangi detail dan presisi keluaran melalui speckle filter yang lebih besar, layer difference lebih besar, serta path precision lebih rendah. |
| `balanced` | VTracer | Menggunakan nilai tengah di antara dua preset lain untuk beberapa parameter VTracer. |
| `high_fidelity` | VTracer | Mempertahankan lebih banyak kandidat detail melalui speckle filter lebih kecil, layer difference lebih kecil, dan path precision lebih tinggi. |

Kolom “Preset” pada tabel berikut menampilkan nilai efektif sebagai
`low_complexity / balanced / high_fidelity`. `default` berarti ketiganya tidak
menimpa nilai dataclass tersebut.

## Pemilihan backend

| Nama | Tipe | Default | Range/nilai valid | Backend mapping | Efek yang diharapkan | Trade-off | Preset | Keterbatasan |
|---|---|---:|---|---|---|---|---|---|
| `engine_type` | `str` | `VTracer` | `VTracer`, `OpenCV Legacy` | Memilih `VTracerBackend` atau `OpenCVLegacyBackend`. | Mengganti algoritma vektorisasi dan kelompok parameter yang aktif. | Hasil, dependensi, dan karakteristik SVG kedua backend berbeda. | `VTracer / VTracer / VTracer` | Jalur layanan kanonik tidak melakukan fallback otomatis ketika VTracer gagal; fallback VTracer ke OpenCV hanya ada pada worker GUI. |

## Preprocessing bersama

Tahap ini dijalankan oleh layanan kanonik sebelum backend. Pada jalur GUI,
worker memanggil backend secara lebih langsung sehingga perilakunya tidak selalu
identik dengan layanan kanonik.

| Nama | Tipe | Default | Range/nilai valid | Backend mapping | Efek yang diharapkan | Trade-off | Preset | Keterbatasan |
|---|---|---:|---|---|---|---|---|---|
| `color_mode` | `str` | `Unlimited colors` | `Unlimited colors`, `Custom colors` | `Custom colors` mengaktifkan K-Means pada preprocessing; OpenCV juga memakai field ini untuk jumlah cluster internal. Tidak diteruskan sebagai `colormode` VTracer. | `Custom colors` membatasi warna hasil preprocessing ke jumlah cluster yang diminta. | K-Means menambah waktu dan memori serta dapat menggabungkan warna yang berdekatan. | `Custom colors / Custom colors / Unlimited colors` | “Unlimited” berarti tahap quantization awal dilewati, bukan jaminan jumlah warna SVG tidak terbatas. OpenCV masih memakai maksimum internal 64 cluster. |
| `color_count` | `int` | `8` | 1–256 | Jumlah cluster K-Means bila `color_mode=Custom colors`; pada OpenCV menjadi jumlah cluster internal, atau 64 saat mode unlimited. | Nilai lebih besar menyediakan lebih banyak pusat warna kandidat. | Lebih banyak cluster dapat menambah waktu, region warna, path, dan ukuran keluaran. | `8 / 24 / 64` | Jumlah aktual dibatasi jumlah warna unik pada sampel training. VTracer tidak menerima parameter ini secara langsung. |
| `preserve_edges` | `bool` | `false` | `true`, `false` | Memilih median filter label 3×3 (`true`) atau 5×5 (`false`) pada quantization; OpenCV juga menerapkan bilateral filter pada mask saat aktif. | Kernel lebih kecil cenderung mempertahankan perubahan label lokal lebih banyak. | Dapat menyisakan lebih banyak region kecil; bilateral filter menambah kerja pada jalur OpenCV. | `false / true / false` | Nama field tidak membuktikan peningkatan edge metric; efek harus diukur. Tidak diteruskan ke VTracer. |
| `remove_background` | `bool` | `false` | `true`, `false` | Preprocessing bersama membuat alpha berdasarkan warna empat sudut; OpenCV juga menghitung foreground mask dari sudut. | Menjadikan piksel yang dekat dengan estimasi warna latar transparan/di luar mask. | Objek yang warnanya dekat latar dapat ikut terhapus. | `false / false / false` | Mengasumsikan empat sudut mewakili latar. Pada jalur OpenCV kanonik operasi terkait dapat terjadi lagi di engine. |
| `bg_tolerance` | `float` | `20.0` | 0.0–255.0 | Ambang jarak Euclidean warna untuk `remove_background`. | Nilai lebih besar mengklasifikasikan rentang warna lebih luas sebagai latar. | Nilai besar meningkatkan risiko menghapus foreground; nilai kecil dapat menyisakan latar. | `20.0 / 20.0 / 20.0` | Perbandingan memakai BGR tiga kanal dan kondisi `distance < tolerance`; nilai 0 tidak menghapus piksel melalui uji ini. |
| `palette_replacements` | `list[((int,int,int),(int,int,int))]` | `[]` | Daftar pasangan RGB; kanal secara praktis 0–255 | Preprocessing bersama melakukan penggantian RGB eksak sebelum quantization/backend. | Mengganti setiap warna sumber yang cocok persis dengan warna tujuan. | Warna antialias yang hanya mendekati sumber tidak ikut berubah. | `default / default / default` | Validasi config hanya menormalisasi struktur tuple/list; tidak memvalidasi panjang tuple atau range kanal. Piksel RGBA yang diganti dibuat opaque. |

## OpenCV Legacy

Parameter di bagian ini tidak dipetakan ke VTracer. Pada input berwarna, engine
OpenCV membentuk mask per warna hasil quantization dan mengekstrak contour dengan
`cv2.RETR_CCOMP`.

| Nama | Tipe | Default | Range/nilai valid | Backend mapping | Efek yang diharapkan | Trade-off | Preset | Keterbatasan |
|---|---|---:|---|---|---|---|---|---|
| `min_area` | `float` | `100.0` | ≥0 dan finite saat engine dijalankan | Menolak contour dengan area bersih lebih kecil dari nilai ini; hole juga disederhanakan hanya jika memenuhi ambang. | Nilai lebih besar mengurangi region kecil yang diekspor. | Detail kecil dapat hilang; nilai rendah dapat menambah noise/path. | `default / default / default` | Satuan adalah pixel² pada resolusi input, sehingga efek berubah menurut ukuran gambar. |
| `approx_tolerance` | `float` | `2.0` | ≥0 dan finite saat engine dijalankan | Menjadi epsilon absolut `cv2.approxPolyDP` untuk outer contour dan hole. | Nilai lebih besar menghasilkan aproksimasi dengan lebih sedikit titik kandidat. | Bentuk dapat makin menyimpang dari contour; nilai kecil menambah titik. | `default / default / default` | Satuan pixel, bukan persentase panjang contour; tidak scale invariant. |
| `smoothing_enabled` | `bool` | `false` | `true`, `false` | Mengaktifkan Gaussian blur 5×5 lalu threshold 127 sebelum contour detection. | Mengurangi perubahan lokal pada binary mask sebelum contour. | Tepi dan detail sempit dapat bergeser atau hilang. | `default / default / default` | Hanya efektif pada OpenCV; kernel dan threshold smoothing tidak dapat dikonfigurasi. |
| `invert` | `bool` | `false` | `true`, `false` | Menjalankan `cv2.bitwise_not` pada working mask. | Membalik foreground dan background binary. | Konfigurasi yang salah dapat membuat kanvas dianggap foreground. | `default / default / default` | Piksel di luar alpha mask dipaksa kembali ke nol; tidak memengaruhi VTracer. |
| `threshold_val` | `int` | `127` | 0–255 | Menjadi threshold biner OpenCV setelah konversi grayscale. | Piksel grayscale di atas nilai menjadi 255; sisanya menjadi 0. | Nilai tinggi memilih lebih sedikit piksel terang sebagai putih; nilai rendah memilih lebih banyak. | `default / default / default` | Pada jalur warna OpenCV, engine membangun ulang foreground dari region warna sehingga threshold bukan satu-satunya penentu contour. Tidak dipakai oleh VTracer. |

## VTracer

Backend meng-clamp kembali angka sebelum memanggil
`vtracer.convert_image_to_svg_py`. Nama pada kolom mapping adalah nama keyword
yang benar-benar dikirim ke binding Python VTracer.

| Nama | Tipe | Default | Range/nilai valid | Backend mapping | Efek yang diharapkan | Trade-off | Preset | Keterbatasan |
|---|---|---:|---|---|---|---|---|---|
| `colormode` | `str` | `color` | `color`, `binary` | `colormode` | Memilih tracing berwarna atau biner di VTracer. | Mode biner membuang variasi warna; mode color dapat membentuk lebih banyak layer. | `color / color / color` | Berbeda dari `color_mode`, yang mengatur preprocessing Silukman. |
| `hierarchical` | `str` | `stacked` | `stacked`, `cutout` | `hierarchical` | Memilih susunan layer bertumpuk atau cutout. | Struktur overlap dan komposisi path berbeda. | `stacked / stacked / stacked` | Dampak visual bergantung konten dan renderer; tidak ada jaminan satu mode lebih baik. |
| `mode` | `str` | `spline` | `spline`, `polygon`, `none` | `mode` | Memilih fitting spline, polygon, atau mode tanpa curve fitting VTracer. | Spline dapat menambah fitting; polygon mempertahankan segmen lurus; `none` membatasi pemodelan kurva. | `spline / spline / spline` | Label GUI “Pixel” dipetakan ke `none`; semantik rinci mengikuti versi VTracer terpasang. |
| `filter_speckle` | `int` | `4` | 0–1024 | `filter_speckle` | Menghapus kandidat region kecil menurut ambang speckle VTracer. | Nilai besar dapat mengurangi region kecil sekaligus membuang detail kecil. | `16 / 8 / 2` | Unit dan perilaku tepat berasal dari VTracer; bukan padanan langsung `min_area`. |
| `color_precision` | `int` | `6` | 1–8 | `color_precision` | Mengatur presisi pengelompokan warna VTracer. | Perubahan nilai dapat mengubah jumlah/komposisi layer warna dan biaya proses. | `5 / 6 / 8` | Tidak sama dengan `color_count`; jumlah warna keluaran tidak ditentukan langsung. |
| `layer_difference` | `int` | `16` | 0–255 | `layer_difference` | Mengatur ambang perbedaan warna antarlayer VTracer. | Ambang berbeda dapat menggabungkan atau memisahkan region warna secara berbeda. | `32 / 16 / 8` | Relasi dengan metrik kualitas harus dibuktikan per dataset. |
| `corner_threshold` | `int` | `60` | 0–180 | `corner_threshold` | Mengatur ambang sudut yang diperlakukan sebagai corner oleh VTracer. | Mengubah kompromi antara corner dan curve fitting. | `60 / 60 / 60` | Satuan/interpretasi mengikuti API VTracer; tidak digunakan OpenCV. |
| `length_threshold` | `float` | `3.5` | 3.5–10.0 | `length_threshold` | Mengatur ambang panjang segmen untuk fitting VTracer. | Nilai berbeda dapat mengubah segmentasi dan kompleksitas path. | `4.5 / 4.0 / 3.5` | Backend fallback internal memakai 4.0 hanya jika atribut hilang; config normal selalu menyediakan 3.5. |
| `max_iterations` | `int` | `16` | 1–100 | `max_iterations` | Membatasi iterasi optimizer VTracer. | Batas lebih besar memberi optimizer lebih banyak kesempatan dan dapat menambah waktu. | `10 / 10 / 16` | Tidak menjamin optimizer memakai seluruh iterasi atau menghasilkan skor lebih tinggi. |
| `splice_threshold` | `int` | `45` | 0–180 | `splice_threshold` | Mengatur ambang penyambungan spline VTracer. | Mengubah kapan segmen dapat disambungkan dan akibatnya struktur path. | `45 / 45 / 45` | Efek tepat bergantung implementasi/version VTracer. |
| `path_precision` | `int` | `8` | 0–16 | `path_precision` | Mengatur jumlah digit desimal koordinat path keluaran VTracer. | Presisi lebih tinggi dapat menambah ukuran SVG; presisi rendah meningkatkan pembulatan. | `4 / 6 / 8` | Presisi serialisasi bukan bukti akurasi visual. Postprocessing dapat menulis ulang XML tetapi tidak mengubah angka path secara eksplisit. |

## Parameter eksperimen benchmark

Field berikut bukan parameter algoritma gambar, tetapi menentukan matriks dan
eksekusi benchmark pada YAML.

| Nama YAML | Tipe | Default/keharusan | Range/nilai aktual | Mapping dan efek | Keterbatasan |
|---|---|---|---|---|---|
| `experiment.id` | `str` | wajib | String | Menjadi bagian ID direktori eksperimen. | Tidak divalidasi terhadap karakter path. |
| `experiment.repetitions` | `int` | `1` | Implementasi tidak menetapkan batas | Jumlah run terukur per kombinasi image/backend/preset. | Nilai tidak positif dapat menghasilkan nol run. |
| `experiment.warmup_runs` | `int` | `1` | Implementasi memperlakukan ≤0 sebagai tanpa warm-up | Jumlah warm-up per backend memakai image dan preset pertama. | Warm-up tidak dicatat sebagai run. Dataset kosong tidak menyediakan image pertama. |
| `experiment.timeout_seconds` | `int` | `60` | Implementasi tidak menetapkan batas | Diteruskan ke backend Potrace dan Inkscape. | Bukan timeout umum untuk backend Python Silukman/VTracer. |
| `dataset.manifest` | `str` | wajib | Path CSV | Sumber daftar image. | Path diinterpretasikan relatif terhadap working directory. |
| `dataset.split` | `str` | `test` | String, lazimnya `train`, `validation`, `test` | Filter equality pada kolom `split`. | Config loader tidak memvalidasi enum. |
| `dataset.categories` | `list[str]` | enam kategori standar | Daftar string | Filter membership pada kolom `category`. | Nama tak dikenal hanya menghasilkan subset kosong. |
| `backends` | `list[str]` | wajib, tidak kosong | `silukman`, `vtracer`, `potrace`, `inkscape` | Membentuk sumbu backend; backend tak tersedia dilewati. | Potrace/Inkscape membutuhkan executable eksternal. |
| `presets` | `list[str]` | wajib, tidak kosong | Nama pada `presets.json` | Membentuk sumbu preset. | Nama tidak dikenal gagal ketika backend memuat preset. |
| `metrics` | `list[str]` | `[]` | String metric | Disimpan dalam config eksperimen. | Evaluator saat ini menghitung set metric terintegrasi; field ini belum memfilter kalkulasi evaluator. |

## Catatan validasi

- `VectorizationConfig.__post_init__` memvalidasi pilihan dan range, tetapi
  Python tidak menegakkan type annotation pada runtime. Beberapa field baru
  gagal saat dipakai jika diberi tipe yang salah.
- `from_dict()` mengabaikan key yang tidak dikenal dan menerima bentuk lama
  `{"vtracer": {...}}`.
- Backend VTracer melakukan clamp defensif terhadap seluruh angka VTracer.
- Preset hanya mendefinisikan parameter VTracer dan preprocessing tertentu;
  parameter OpenCV serta `palette_replacements` memakai default.

