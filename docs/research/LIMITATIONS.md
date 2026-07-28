# Limitations

Dokumen ini membatasi interpretasi teknis dan empiris Silukman Image Vectorizer.
Ia harus dibaca bersama protocol, parameter reference, dan hasil mentah
benchmark.

## Bergantung pada VTracer

Preset bawaan memilih backend VTracer dan pipeline utama memerlukan package
`vtracer`. Perubahan API, perilaku, performa, atau ketersediaan wheel VTracer
dapat memengaruhi Silukman. Jalur GUI mempunyai fallback ke OpenCV pada kondisi
tertentu, tetapi layanan kanonik CLI/benchmark tidak menjamin fallback otomatis.

## Bukan algoritma vectorization baru

Silukman mengorkestrasi loading, preprocessing, konfigurasi backend, ekspor,
postprocessing, GUI, CLI, dan benchmark. Backend utamanya adalah VTracer;
alternatif legacy menggunakan contour OpenCV. Karena itu hasil tidak boleh
dipresentasikan sebagai algoritma tracing fundamental baru tanpa kontribusi
algoritmik tambahan yang terpisah dan dibuktikan.

## Metrik raster tidak sepenuhnya menangkap kualitas SVG

MAE, RMSE, PSNR, SSIM, histogram, dan edge metric dihitung setelah SVG
dirasterisasi. Metric tersebut tidak sepenuhnya mengukur:

- editability dan struktur semantik;
- kualitas topology, overlap, hole, dan grouping;
- kelancaran curve pada zoom tinggi;
- stabilitas rendering lintas SVG renderer;
- aksesibilitas atau kesesuaian produksi;
- kompleksitas yang dirasakan editor manusia.

Sebaliknya, ukuran file, jumlah path, dan jumlah command juga bukan ukuran
kualitas visual secara langsung.

## Dataset mungkin terbatas

Dataset dapat kecil, terkurasi, tidak seimbang, atau bias terhadap synthetic dan
digital artwork. Hasil pada enam kategori repository tidak otomatis berlaku
untuk distribusi image dunia nyata, scan historis, medical image, cartography,
atau domain lain. Jumlah sample per kategori, sumber, lisensi, dan exclusion
harus selalu dilaporkan.

## Subjektivitas kualitas visual

Penilaian manusia dipengaruhi konteks penggunaan, zoom, display, renderer, dan
preferensi terhadap detail versus kesederhanaan. Qualitative sheet membantu
inspeksi transparan tetapi tidak menggantikan studi pengguna atau penilaian
blind oleh beberapa evaluator.

## Tool baseline memiliki kemampuan berbeda

VTracer mendukung tracing berwarna; Potrace berorientasi bitmap biner; Inkscape
CLI menggunakan workflow dan kontrol yang berbeda; Silukman menambahkan tahap
pre/postprocessing. Parameter tidak selalu mempunyai padanan satu-ke-satu.
Perbandingan tidak kompatibel harus di-skip atau diberi caveat, bukan dipaksa
menjadi ranking universal.

## Hasil dipengaruhi hardware

Runtime dan memory bergantung CPU, core count, RAM, OS scheduler, beban latar,
filesystem, build native, dan cache. Memory native juga diukur berbeda:
`getrusage` di macOS/Linux dan `tracemalloc` di Windows. Angka performa antar
mesin tidak sebanding tanpa kontrol dan pelaporan environment.

## Foto mungkin tidak cocok untuk vectorization

Foto mengandung warna kontinu, tekstur, noise, dan detail frekuensi tinggi.
Vektorisasi dapat menghasilkan SVG besar dengan banyak region tanpa menjadi
representasi yang lebih berguna daripada raster. Kesetiaan raster yang tinggi
tidak dengan sendirinya membuktikan SVG efektif untuk diedit, dikirim, atau
dirender.

## Parameter belum tentu optimal

Preset `low_complexity`, `balanced`, dan `high_fidelity` adalah konfigurasi
bawaan, bukan optimum global atau optimum per kategori. Nilai dapat berasal dari
heuristik dan belum tentu sudah dituning dengan prosedur nested validation.
Tuning pada test set akan membiasakan hasil dan harus dihindari.

## Cross-platform variance

Perbedaan versi Python, OpenCV, Qt/PySide6, VTracer, compiler, font/rendering,
floating-point, process spawning, dan filesystem dapat mengubah runtime,
rendering, metadata, atau byte output. K-Means diberi seed, tetapi determinisme
byte-identik lintas platform tidak dijamin. Output timestamp metadata juga
menghalangi byte-identical SVG antar-run.

## Batasan implementasi tambahan

- Jalur GUI dan layanan kanonik belum memakai orkestrasi yang sepenuhnya sama.
- Timeout sinkron belum benar-benar ditegakkan untuk backend Python.
- Estimasi point count pada postprocessing adalah heuristik berbasis angka dalam
  path data, bukan parser lengkap perintah SVG.
- Validasi SVG aplikasi hanya memeriksa XML dan root `<svg>`; evaluator metric
  memakai parser aman terpisah.
- Field `metrics` pada YAML benchmark belum memfilter metric yang dihitung.
- Qualitative report saat ini belum menanamkan raster asli dan SVG secara penuh.
- `peak_memory_bytes` adapter Silukman dapat bernilai nol karena layanan
  vektorisasi belum melacak memory secara langsung.

Setiap publikasi atau release note yang menyatakan hasil kualitas harus merujuk
ke raw results dan menyebut batasan relevan di atas.

