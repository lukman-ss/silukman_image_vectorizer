# Baseline Fairness Rules

Dokumen ini mendefinisikan protokol dan aturan ketat untuk melakukan komparasi performa dan kualitas antara Silukman Vectorizer dan _tool_ _baseline_ eksternal (VTracer, Potrace, Inkscape). 

Tujuannya adalah mencegah klaim performa yang keliru (*misleading*), memastikan perbandingan parameter yang setara (_apples-to-apples_), dan menjaga integritas akademik *benchmark*.

## 1. Tujuan Perbandingan
*Benchmark* _baseline_ dilakukan untuk:
- Mengukur kontribusi nyata dari *preprocessing* (kuantisasi, _blur_) dan *post-processing* Silukman dibandingkan eksekusi VTracer *bare-metal*.
- Mengevaluasi kecepatan (*throughput*) dan efisiensi memori dari berbagai _engine_ raster-ke-vektor.
- Mengidentifikasi batasan spesifik dari masing-masing algoritma terhadap kelas gambar tertentu (fotografi vs ikon).

## 2. Task Compatibility & Subset Dataset
Setiap *tool* memiliki spesialisasi desain yang tidak boleh dilanggar.
**Aturan Utama**: Jangan pernah membandingkan *tool* pada kategori gambar di luar spesifikasi teknisnya.
- **Potrace**: Secara matematis hanya bisa memproses gambar biner (1-bit). **Hanya** diujikan pada dataset kategori `binary_graphic` dan `monochrome_silhouette`. Menjalankan Potrace untuk foto *full-color* lalu menghitung skor kualitasnya adalah pelanggaran protokol.
- **VTracer / Silukman / Inkscape**: Dapat dievaluasi pada semua kategori (`logo`, `icon`, `illustration`, `complex_artwork`, `photograph`).

## 3. Aturan Resolusi
Semua gambar input harus dipertahankan pada resolusi aslinya selama *benchmark*.
*Downscaling* atau *upscaling* sebelum masuk ke *engine vectorizer* dilarang keras karena memengaruhi metrik *CPU time* dan komputasi memori.

## 4. Aturan Background & Alpha Channel
- Jika *tool* (seperti VTracer/Silukman) secara bawaan mendukung *alpha channel*, transparansi harus dibiarkan apa adanya.
- Jika *tool* (seperti Potrace) tidak mendukung *alpha channel*, gambar harus diratakan (*alpha compositing*) di atas _background_ solid (putih, `rgb(255, 255, 255)`) **sebelum** perhitungan vektorisasi dimulai.

## 5. Aturan Preprocessing
- Waktu yang dihabiskan untuk melakukan *preprocessing* spesifik format (misal, mengonversi PNG transparan ke BMP biner untuk Potrace) **tidak boleh** dimasukkan ke dalam metrik `wall_clock_time` atau `cpu_time`.
- Pengukuran performa *core* harus benar-benar dibatasi secara eksklusif pada saat pemanggilan fungsi/CLI utama _engine_.

## 6. Aturan Timeout
Batas waktu maksimal untuk satu gambar adalah:
- **Default**: 60 Detik untuk gambar resolusi tinggi / kompleks.
- **Strict**: 10 Detik untuk Potrace / vektor biner dasar.
Jika melampaui *timeout*, *benchmark* dicatat sebagai **Failed** (Time Out), bukan diabaikan.

## 7. Aturan Failure (Kegagalan)
Setiap _error_ (*crash*, memori habis/OOM, *invalid output*) harus dilaporkan dengan metrik kualitas di-_hardcode_ menjadi `null` (None). Mengisi metrik kualitas dengan angka `0` dilarang karena akan merusak perhitungan agregat (misal, RMSE=0 bermakna sempurna).

## 8. Aturan Preset
- **Silukman vs VTracer Direct**: Harus menggunakan konfigurasi parameter VTracer yang **identik** (misal `filter_speckle`, `corner_threshold`).
- **Inkscape**: Karena Inkscape versi 1.0+ tidak mengizinkan injeksi variabel *trace bitmap* dengan stabil lewat terminal, konfigurasi ini dianggap *black-box* (*GUI preference fallback*). Fakta ini wajib didokumentasikan di *log benchmark*.

## 9. Aturan Hardware
Seluruh eksekusi *benchmark baseline* harus dijalankan pada mesin tunggal, di OS yang sama, tanpa intervensi latar belakang. Limitasi pembacaan *native memory* di Windows (_tracemalloc_ tidak bisa menangkap _C-extensions_) harus dicatat. macOS/Linux `getrusage` adalah standar emas untuk pelaporan memori.

## 10. Aturan Repeated Runs (Warm-up)
- **Warm-up**: Fungsi/CLI wajib dieksekusi satu kali sebelum _timer_ diaktifkan. Ini mencegah bias performa dari *library loading*, inisialisasi JIT, atau *caching disk*.
- Parameter metrik diukur dari _run_ stabil setelah *warm-up*.

## 11. Potensi Bias & Larangan Cherry-Picking
- **Larangan Keras**: Dilarang menghapus sampel (gambar) dari *dataset benchmark* hanya karena suatu algoritma gagal menanganinya (*cherry-picking*). 
- Jika suatu _engine_ buruk terhadap teks tipis, sampel teks tipis harus tetap berada di *dataset* untuk mengekspos kelemahan tersebut secara ilmiah. Bias harus dilaporkan di metrik akhir.
