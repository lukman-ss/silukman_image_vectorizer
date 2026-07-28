# Security: File Parsing and External Executables

Dokumen ini adalah audit berbasis implementasi saat ini, bukan sertifikasi
keamanan. Aplikasi desktop dan benchmark sebaiknya dijalankan dengan hak user
biasa pada data yang dipercaya atau dalam environment terisolasi.

## Trust boundary

Input yang dapat dikendalikan pihak luar meliputi image raster, SVG yang
diinspeksi/dirender, path input-output, manifest CSV, YAML/JSON config, nama
file, serta executable `potrace`, `inkscape`, dan `git` yang ditemukan melalui
`PATH`.

## Untrusted images

Raster dibaca oleh OpenCV dan pada beberapa jalur Pillow. Decoder native dapat
mempunyai vulnerability atau crash pada file rusak. Validasi saat ini memastikan
file ada dan decoder menghasilkan image, tetapi tidak melakukan content
sniffing, sandbox decoder, atau antivirus scanning.

Mitigasi realistis:

- gunakan versi OpenCV/Pillow yang masih mendapat security update;
- cocokkan format aktual, ukuran, dan checksum terhadap manifest;
- proses dataset tak tepercaya dalam container/VM tanpa secret dan tanpa akses
  tulis ke luar working directory;
- tolak file yang gagal decode dan jangan otomatis mencoba banyak decoder;
- tambahkan fuzz test dan batas dimensi sebelum decode untuk deployment yang
  menerima upload publik.

## Decompression bombs

Image berdimensi sangat besar dapat memakai sedikit ruang terkompresi tetapi
menghabiskan RAM saat decode. OpenCV tidak menyediakan proteksi
`DecompressionBombWarning` seperti Pillow, dan pipeline melakukan beberapa copy,
mask, K-Means buffer, serta rasterisasi.

Mitigasi saat ini terbatas pada aturan dataset (maksimum 4096×4096 dan 10 MB),
tetapi batas tersebut belum ditegakkan oleh loader utama. Mitigasi yang
direkomendasikan:

- periksa file size sebelum decode;
- baca header/dimensi dengan decoder terbatas lalu tolak width, height, pixel
  count, atau channel count di atas kebijakan;
- jalankan worker dengan memory/CPU limit;
- hindari memproses batch tak tepercaya secara paralel tanpa worker cap.

## Malformed SVG/XML

`app.core.postprocessing.parse_and_validate_svg` memakai
`xml.etree.ElementTree` dan hanya memeriksa syntax serta root `<svg>`.
`benchmark.evaluation.svg_metrics` memakai `defusedxml`, yang lebih aman
terhadap entity expansion. GUI dan benchmark juga merender SVG melalui Qt.

Risiko tersisa mencakup XML besar/deep, path data ekstrem, elemen eksternal,
resource reference, dan beban rasterisasi. Fallback exporter bahkan dapat
menulis raw SVG VTracer ketika parsing/postprocessing gagal.

Mitigasi:

- hanya perlakukan SVG keluaran backend lokal sebagai trusted-enough;
- gunakan `defusedxml` secara konsisten di seluruh parser;
- tetapkan batas byte, element count, nesting depth, path length, dan render
  dimensions sebelum parsing/rendering;
- tolak external references, scripts, event handlers, foreign objects, dan URL
  schemes jika SVG dari user akan dibuka;
- render input tak tepercaya di process terisolasi dengan timeout dan memory
  limit;
- jangan membuka SVG tak tepercaya di browser dengan origin/credential sensitif.

## External process execution

Benchmark menjalankan Potrace dan Inkscape, sedangkan environment capture
menjalankan Git, pip, `sysctl`, serta version command. `run_isolated_process`
memakai argument list dan `shell=False`, membuat process group baru, menerapkan
timeout, dan membunuh group saat timeout.

Risiko:

- executable palsu lebih awal di `PATH`;
- executable eksternal membaca file attacker-controlled;
- Inkscape action string memuat output path dalam satu argument;
- output/stderr sangat besar;
- process Python VTracer/Silukman tidak mendapat hard timeout yang sama.

Mitigasi:

- gunakan absolute executable path yang diverifikasi atau environment `PATH`
  minimal;
- catat versi dan hash executable untuk benchmark penting;
- jalankan baseline dalam user/container tanpa privilege dan tanpa network bila
  tidak diperlukan;
- batasi stdout/stderr, CPU, memory, file size, dan jumlah process;
- jangan menjalankan baseline dari working directory yang dapat ditulisi pihak
  tak tepercaya.

## Path traversal

Single-file CLI menerima path output yang dipilih user dan memang dapat menulis
ke lokasi yang user izinkan. Batch hanya membaca file langsung dari
`input_dir`, tetapi benchmark membangun input path dari `filename` manifest
dengan `os.path.join` tanpa memastikan hasilnya tetap berada di
`benchmark/samples`. Nilai seperti `../target` dapat keluar dari direktori
dataset. Experiment ID dan path output analysis juga belum dinormalisasi ke root
yang diizinkan.

Mitigasi:

- jangan memakai manifest/config tak tepercaya;
- resolve path lalu verifikasi `candidate.is_relative_to(allowed_root)` (atau
  pemeriksaan parent kompatibel Python 3.9);
- tolak absolute path, `..`, separator direktori, symlink escape, dan filename
  kosong pada kolom manifest;
- gunakan allowlist extension dan root output khusus;
- sebelum overwrite, pastikan target regular file atau target baru di root yang
  diizinkan.

## Temporary files

Pipeline menggunakan `NamedTemporaryFile` untuk PNG/SVG dan menghapusnya pada
`finally`. Atomic SVG writer membuat temporary file di direktori target,
`fsync`, lalu `os.replace`. Ini mengurangi partial write.

Potrace baseline memakai `tempfile.mktemp`, yang memiliki race condition antara
pembuatan nama dan penulisan file. Beberapa temporary output juga dapat tersisa
jika process dihentikan paksa.

Mitigasi:

- ganti `mktemp` dengan `NamedTemporaryFile(delete=False)` atau
  `TemporaryDirectory`;
- gunakan permission user-only dan cleanup pada `finally`;
- letakkan seluruh temporary artifact satu run dalam direktori unik;
- lakukan cleanup startup untuk directory temporary milik aplikasi yang sudah
  kedaluwarsa, tanpa mengikuti symlink.

## Command injection

Jalur external process utama tidak memakai shell dan membangun `cmd` sebagai
list, sehingga karakter shell pada path tidak dieksekusi sebagai command.
String `invocation` pada metadata Potrace hanya untuk pelaporan dan tidak
dieksekusi.

Namun input path tetap dapat menjadi option-like argument untuk tool eksternal,
dan Inkscape menggabungkan output path ke action syntax internal. Ini bukan
shell injection tetapi masih merupakan argument/action injection surface.

Mitigasi:

- validasi dan canonicalize path sebelum membangun argument;
- gunakan `--` end-of-options bila CLI mendukung;
- batasi karakter/control sequence pada filename eksperimen;
- jangan pernah mengubah runner menjadi `shell=True`;
- treat log/invocation string sebagai data dan escape saat ditampilkan di HTML.

## Resource exhaustion

Sumber beban utama:

- K-Means dan buffer jarak untuk banyak pixel/warna;
- contour/path/element dalam jumlah besar;
- SVG sangat besar atau sangat dalam;
- rasterisasi Qt;
- batch worker paralel;
- stdout/stderr process eksternal;
- jumlah kombinasi dataset × backend × preset × repetition.

Pipeline membatasi training K-Means ke 100.000 pixel dan assignment ke chunk
50.000, serta batch CLI default dua worker. External Potrace/Inkscape memiliki
timeout. Batas global CPU, RAM, disk, jumlah element, dan ukuran output belum
diterapkan.

Mitigasi:

- tetapkan maksimum pixel, input bytes, output bytes, path/element count, dan
  runtime;
- batasi worker dan total task sebelum run;
- gunakan OS/container quotas untuk CPU, RAM, process, dan disk;
- hentikan run ketika ruang disk minimum terlampaui;
- streaming/limit log process dan JSONL;
- jangan mengandalkan timeout thread untuk menghentikan native call; gunakan
  worker process yang dapat diterminasi.

## Prioritas perbaikan

1. Cegah manifest path escape dan symlink escape.
2. Terapkan batas file size, pixel count, dan SVG complexity sebelum decode atau
   render.
3. Ganti Potrace `tempfile.mktemp`.
4. Gunakan `defusedxml` dan sanitasi SVG secara konsisten.
5. Jalankan backend Python dan renderer dalam process terisolasi dengan resource
   limit.
6. Resolve dan verifikasi executable eksternal, lalu batasi output process.

Sampai mitigasi tersebut diterapkan, jangan mengekspos pipeline sebagai layanan
upload publik tanpa sandbox tambahan.

