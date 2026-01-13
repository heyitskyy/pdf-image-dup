# PDF Image Duplicate Checker (Robust)

Aplikasi untuk mengecek apakah **gambar-gambar di dalam PDF** sudah pernah ada sebelumnya pada kumpulan PDF lain (database lokal). Mendukung deteksi **gambar yang sama** meskipun mengalami perubahan seperti:

- Perbedaan warna/brightness
- Grayscale
- Crop (ringan–sedang, tergantung kasus)
- Kompresi/resize dari PDF

Project ini menyimpan PDF & hasil ekstraksi di **folder lokal** dan menyimpan metadata/fingerprint di **SQLite**.

---

## ✨ Fitur

- ✅ Extract **embedded images** dari PDF (PDF digital)
- ✅ Fallback render halaman menjadi image (untuk PDF scan / tanpa embedded image)
- ✅ Fingerprint berbasis perceptual hash + edge hash (lebih tahan perubahan warna/brightness)
- ✅ Deteksi duplicate antar PDF yang sudah pernah di-ingest
- ✅ Output report per PDF dalam `report.json`
- ✅ Bisa ingest **1 file** atau **1 folder PDF (batch)**
- ✅ Dashboard **Streamlit** untuk upload & lihat hasil dengan cepat

---

## 🧰 Tech Stack

- Python 3.x
- PyMuPDF (`pymupdf`) untuk PDF processing
- Pillow + ImageHash untuk fingerprint
- SQLite untuk metadata database
- Streamlit untuk dashboard

---

## 📁 Struktur Project

```
pdf-image-dup/
├── run.py
├── src/
│   ├── ingest_pdf.py
│   ├── ingest_folder.py
│   ├── streamlit_app.py
│   ├── db.py
│   ├── pdf_extract.py
│   ├── fingerprint.py
│   ├── matcher.py
│   └── config.py
└── storage/
    ├── pdfs/          # semua PDF yang sudah di-ingest
    ├── images/        # hasil extract/render per pdf_id
    ├── uploads/       # temp upload (streamlit)
    └── app.db         # SQLite database
```

---

## ✅ Prasyarat

- Windows (tested)
- Python terinstall (disarankan 3.10+)
- (Opsional) Git untuk cloning repo

**Cek Python:**

```powershell
py --version
```

---

## 🚀 Instalasi

### 1) Clone repo

```bash
git clone (https://github.com/heyitskyy/pdf-image-dup)
cd pdf-image-dup
```

### 2) Buat virtual environment

```powershell
py -m venv venv
.\venv\Scripts\activate
```

### 3) Install dependencies

```powershell
pip install -r requirements.txt
```

Jika kamu belum punya `requirements.txt`, install manual:

```powershell
pip install pymupdf pillow imagehash streamlit pandas
```

---

## ▶️ Cara Pakai (CLI)

### A) Ingest 1 PDF

```powershell
py .\src\ingest_pdf.py "C:\path\to\file.pdf"
```

**Hasil tersimpan di:**
- `storage/pdfs/` (salinan PDF)
- `storage/images/pdf_<id>/` (hasil gambar + report.json)
- `storage/app.db` (SQLite)

### B) Ingest 1 Folder PDF (Batch)

**Recursive (include subfolder):**

```powershell
py .\src\ingest_folder.py "D:\DatasetPDF"
```

**Non-recursive:**

```powershell
py .\src\ingest_folder.py "D:\DatasetPDF" --no-recursive
```

---

## 🖥️ Cara Pakai (Streamlit Dashboard)

**Jalankan:**

```powershell
py -m streamlit run .\src\streamlit_app.py
```

Lalu buka URL yang muncul (biasanya):
- http://localhost:8501

**Fitur dashboard:**
- Upload PDF
- Lihat tabel hasil DUP/NEW
- Preview image (PDF baru vs referensi)
- Download `report.json`

---

## 📝 Output & Report

Setiap ingest menghasilkan `report.json` di:

```
storage/images/pdf_<id>/report.json
```

**Contoh isi (ringkas):**
- `is_duplicate: true/false`
- `match.old_pdf_filename`
- `match.old_page`
- `match.score`, `phash_dist`, `dhash_dist`, `ehash_dist`

---

## ⚙️ Konfigurasi

Buka `src/config.py` untuk mengubah:
- DPI render untuk PDF scan (misal 200 → 300)
- Threshold matching hash

---

## 🧪 Testing yang Disarankan

1. Ingest PDF A (original)
2. Buat PDF B yang berisi gambar sama tapi:
   - Di-crop
   - Diubah brightness/warna
   - Diubah grayscale
3. Ingest PDF B → hasil seharusnya terdeteksi DUP pada gambar terkait

---
