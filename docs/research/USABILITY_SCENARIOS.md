# Silukman Image Vectorizer - Usability Scenarios

This document outlines the specific task scenarios for the usability study.

## Scenario 1: Mengonversi Logo Sederhana
- **Context:** Anda memiliki sebuah file logo PNG yang perlu diubah menjadi format vektor.
- **Task:** Buka file logo tersebut di dalam aplikasi dan konversikan menjadi SVG tanpa mengubah pengaturan apa pun.
- **Success Criteria:** File berhasil dimuat, proses vektorisasi dijalankan, dan SVG berhasil diekspor.

## Scenario 2: Menghapus Background
- **Context:** Logo yang Anda konversi memiliki latar belakang putih yang tidak diinginkan.
- **Task:** Gunakan fitur aplikasi untuk mendeteksi dan menghapus latar belakang putih dari gambar tersebut.
- **Success Criteria:** Fitur penghapus background diaktifkan, toleransi disesuaikan jika perlu, dan preview menunjukkan background telah hilang.

## Scenario 3: Memilih Preset
- **Context:** Anda ingin hasil vektor yang sangat mendetail untuk sebuah ilustrasi.
- **Task:** Pilih preset yang sesuai untuk kebutuhan "High Fidelity" dari daftar preset yang tersedia.
- **Success Criteria:** Preset berhasil dipilih dan parameter-parameter terlihat berubah sesuai dengan preset tersebut.

## Scenario 4: Menyesuaikan Hasil
- **Context:** Preset yang dipilih menghasilkan terlalu banyak path (terlalu kompleks).
- **Task:** Lakukan penyesuaian manual pada parameter (misalnya Speckle Filtering atau Color Precision) untuk menyederhanakan hasil.
- **Success Criteria:** Parameter diubah secara manual dan hasil vektor terlihat lebih sederhana atau jumlah path berkurang.

## Scenario 5: Mengganti Palette
- **Context:** Anda perlu mengganti salah satu warna pada hasil vektor ke warna spesifik lainnya.
- **Task:** Gunakan fitur palette replacement untuk mengganti satu warna ke warna lain (misal, merah ke biru).
- **Success Criteria:** Aturan pergantian warna ditambahkan dan hasil akhir merefleksikan perubahan warna tersebut.

## Scenario 6: Memproses Folder (Batch Processing)
- **Context:** Anda memiliki satu folder berisi beberapa ikon yang perlu dikonversi sekaligus dengan pengaturan yang sama.
- **Task:** Buka fitur batch processing, pilih folder sumber, tentukan folder tujuan, dan mulai proses konversi massal.
- **Success Criteria:** Proses batch berjalan sampai selesai dan file SVG dapat ditemukan di folder tujuan.

## Scenario 7: Mengekspor SVG
- **Context:** Anda telah selesai menyesuaikan pengaturan dan puas dengan preview.
- **Task:** Simpan hasil akhir vektor tersebut ke dalam direktori Documents Anda.
- **Success Criteria:** Dialog penyimpanan file (save) digunakan dan file SVG berhasil ditulis ke direktori yang dituju.

## Scenario 8: Menemukan Error File
- **Context:** Anda mencoba mengonversi sebuah file yang rusak atau bukan file gambar.
- **Task:** Masukkan file yang disediakan (file error) dan identifikasi apa yang salah berdasarkan pesan error dari aplikasi.
- **Success Criteria:** Pesan error muncul, peserta dapat membaca dan menjelaskan bahwa file tidak didukung atau rusak tanpa kebingungan.
