# Testing & Coverage Documentation

## Fokus Prioritas Coverage
Pengujian difokuskan pada kehandalan logika utama yang berjalan secara *headless* (tanpa GUI) karena pengujian integrasi aplikasi PySide6 membutuhkan *X11 display* atau *virtual framebuffer* yang rapuh pada CI/CD.

Area prioritas yang dites secara mendalam:
- **`app.core`**: `vectorization_service`, `result`, `exceptions`, `preprocessing`, `postprocessing`.
- **`benchmark.runner`**: *Experiment runner*, pembuatan *hash config*, konfigurasi YAML, dan *environment capture*.
- **`benchmark.evaluation`**: *Metrics calculation* (SVG complexity, dll).
- **`benchmark.analysis`**: Validasi kegagalan (*failure analysis*), klasifikasi kesalahan, dan agregasi statistik dari JSONL mentah.

## Pengecualian Coverage (*Omitted Areas*)

Area berikut secara eksplisit **dikecualikan** dari perhitungan target *code coverage* pada file `pyproject.toml`, dengan alasan sbb:

### 1. Graphical User Interface (`app.ui/*` & `app.cli.py`)
Semua berkas yang menangani PySide6 (MainWindow, *widgets*, dan *event loops* interaktif) tidak dievaluasi oleh *unit tests* reguler.
- **Alasan**: *UI testing* membutuhkan interaksi pengguna langsung, rentan *flaky*, dan menambah waktu eksekusi secara eksponensial. Aplikasi utama sudah dilindungi oleh pengujian arsitektur *core*.

### 2. File Generator Teks & Plot (`benchmark.analysis.*_generator.py`)
Skrip-skrip ini bertugas menghasilkan keluaran visual (*PDF/PNG plots*) atau Markdown/LaTeX (*tables*).
- **Alasan**: Sangat tidak bermakna memvalidasi kode HTML/LaTeX yang dihasilkan karena rentan berubah mengikuti selera format.
- File yang di-omit: `plot_generator.py`, `table_generator.py`, dan `report_generator.py`.

### 3. File Asset & Resource (`app.resources/*`)
Aset statis.
- **Alasan**: Bukan berupa skrip operasional yang memiliki *flow control*.

## Aturan Coverage Tambahan
- Kondisi pengecualian diatur pada blok `[tool.coverage.report]`, misalnya blok `if __name__ == '__main__':` dan blok kode `pragma: no cover` pada *handling* eksepsi tidak terduga (*unexpected environment crashes*).
- Kami tidak menulis "tes kosong" atau pengujian palsu sekadar untuk menaikkan angka persentase. Kualitas dari *coverage* > Kuantitas dari *coverage*.
