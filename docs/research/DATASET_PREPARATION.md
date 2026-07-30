# Dataset Preparation Guide

This document outlines the guidelines and standards for building the experimental benchmark dataset used by the Silukman Image Vectorizer.

## Tujuan Dataset
Dataset ini dirancang khusus untuk mengevaluasi performa dan fidelitas visual (visual fidelity) dari algoritma raster-to-vector yang digunakan oleh Silukman Vectorizer. Dataset bertujuan untuk mengukur metrik seperti: akurasi ekstraksi garis, jumlah path, jumlah elemen, ukuran file SVG, dan kecepatan pemrosesan terhadap berbagai karakteristik grafis raster.

## Inclusion Criteria
Gambar yang dimasukkan ke dalam dataset harus memenuhi kriteria berikut:
- Merupakan gambar raster murni dengan ekstensi yang didukung (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`).
- Resolusi gambar tidak kurang dari 128x128 pixel dan tidak lebih dari 4096x4096 pixel.
- Terdapat kejelasan mengenai atribusi dan kreator.
- Gambar harus secara visual mencerminkan salah satu dari kategori spesifik di bawah ini.

## Exclusion Criteria
Gambar akan ditolak apabila:
- Mengandung _watermark_, teks _copyright_, atau _overlay_ buatan yang merusak struktur gambar.
- Lisensi tidak jelas, abu-abu, atau _All Rights Reserved_.
- Terdapat indikasi _content tampering_ atau korupsi data internal.
- Ukuran file melebihi 10 Megabyte.

## Kategori
Kategori gambar diklasifikasikan ke dalam 6 tipe spesifik yang mendikte pendekatan vektorisasi:
1. **logo**: Logo geometris warna datar, tipografi tajam.
2. **icon**: Simbol sederhana, biasanya monokromatik.
3. **illustration**: Seni digital, gambar vektor yang di-_rasterize_.
4. **complex_artwork**: Digital painting yang kompleks, mengandung gradien dan percampuran layer intensif.
5. **photograph**: Tangkapan kamera dunia nyata, penuh _noise_ dan gradien kontinyu.
6. **binary_graphic**: Grafis hitam putih murni (dokumen _scan_, line art).

## Target Jumlah Sampel
Untuk memastikan distribusi pengujian, target dataset awal adalah minimal **100 gambar per kategori**, dengan distribusi `split` yang proporsional. Namun jumlah ini bukan batasan akhir melainkan _baseline_ statis eksperimen pertama.

## Sumber Gambar Legal
Prioritaskan pengambilan data dari sumber _open-source_ atau platform dengan lisensi terbuka, contohnya:
- **Wikimedia Commons** (Public Domain, CC0, CC-BY)
- **Unsplash, Pexels, Pixabay** (jika mematuhi lisensi terbarunya yang ekuivalen redistribusi, periksa syarat dan ketentuan).
- **Public Domain SVG archives** yang telah dikonversi secara sengaja (dan reprodusibel) ke raster PNG.

## Aturan Lisensi
- Setiap aset **harus** memiliki lisensi redistribusi yang legal dan terdokumentasi (e.g. `CC0`, `CC BY 4.0`, `MIT`, `Public Domain`).
- Tidak boleh mengambil aset berlisesi `CC BY-NC` atau `CC BY-ND` apabila menghalangi validitas publikasi turunan modifikasi (tergantung target komersialisasi). Sangat disarankan hanya menggunakan ranah `CC0` atau `CC-BY`.
- Naskah asli lisensi harus disalin utuh ke folder `benchmark/licenses/`.

## Aturan Atribusi
- Kolom `creator` dalam manifest tidak boleh kosong apabila penciptanya diketahui.
- Tautan asli (source URL) **harus** disertakan di manifest untuk tujuan _cross-check_ keabsahan sumber.

## Aturan Preprocessing
- Sangat dilarang untuk melakukan _downscaling_, _sharpening_, atau manipulasi Photoshop pada gambar yang akan di-_commit_ ke dalam *samples*.
- Jika ingin melakukan manipulasi untuk keperluan stress-test (seperti _adding synthetic noise_), varian gambar ini harus didaftarkan secara terpisah dengan `image_id` yang berbeda dan dicatat dalam kolom `notes`.

## Aturan Naming
- Penamaan file harus mengikuti konvensi snake_case dan diawali dengan kategori, lalu nama singkat.
- Contoh: `logo_acme_corp.png`, `icon_magnifying_glass.webp`.
- Penamaan file (`filename`) harus sama persis dengan yang tertulis di dalam file manifest.

## Aturan Checksum
Setiap gambar wajib dihitung **SHA-256 hash**-nya secara absolut sebelum dicatatkan.
- Jika gambar diubah meski hanya 1 pixel atau 1 bit metadata, file tersebut dianggap sebagai entitas data baru dan SHA-256 di dalam manifest harus diperbarui.

## Aturan Split
Setiap entri gambar harus dilabeli split dengan distribusi konvensional:
- **train** (80%): Digunakan untuk menyesuaikan _hyperparameters_ atau pengenalan _presets_ secara iteratif.
- **validation** (10%): Digunakan untuk memvalidasi algoritma selama perancangan preset.
- **test** (10%): Tidak boleh dilihat/diproses selama tahap kalibrasi/tuning eksperimen, digunakan eksklusif untuk final benchmark.

## Cara Menambahkan Gambar
1. Unduh gambar asli dan pastikan lisensinya cocok.
2. Hitung SHA-256 (`shasum -a 256 <file>`).
3. Beri nama file sesuai **Aturan Naming** dan pindahkan ke direktori `benchmark/samples/`.
4. Jika lisensinya baru (belum ada di folder lisensi), tambahkan ke `benchmark/licenses/`.
5. Buka `benchmark/datasets/real_world/dataset_manifest.csv` dan tambahkan baris data sesuai metadata.
6. Jalankan validator.

## Cara Menjalankan Validator
Validator digunakan untuk memastikan tidak ada dataset yang _corrupt_ atau melanggar skema.
Jalankan perintah ini di root folder proyek:
```bash
python3 -m benchmark.scripts.validate_dataset
```
Atau jika ingin melihat laporan dalam bentuk JSON:
```bash
python3 -m benchmark.scripts.validate_dataset --json
```
_Commit_ tidak boleh dilakukan apabila validator masih mengeluarkan **Critical Error** (exit code `1`).

## Batasan Dataset (Limitations)
Penting untuk dicatat bahwa **dataset ini tidak diklaim merepresentasikan distribusi gambar dunia nyata secara universal**. Dataset ini bersifat sangat terkurasi dan bias pada gambar buatan grafis (synthetic/digital). Performa *vectorizer* yang sangat tinggi pada dataset ini belum tentu berkorelasi 1:1 terhadap stabilitas algoritma saat dihadapkan pada artefak kompresi JPG ekstrem dan gambar _low-fidelity_ di _wild environment_ tak terduga.
