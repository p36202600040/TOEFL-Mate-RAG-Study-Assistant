# TOEFL Mate: RAG Study Assistant 📚

## Dokumen utama untuk pengumpulan

- [Laporan metodologi evaluasi dan hasil final](reports/methodology_evaluation_final_uts_20261103.pdf)
- [Salinan hasil V2 tersanitasi untuk publikasi](evaluation/public/)

Laporan lain merupakan arsip iterasi. Angka V2 bersifat historis, bukan hasil evaluasi source-aware terbaru atau pengujian deployment. Artefak mentah V2 tetap lokal; salinan publik menghapus pesan error provider tanpa menghitung ulang metrik.

> **Status evaluasi:** prototipe; correctness dan groundedness belum divalidasi manusia. Label historis yang hanya berisi halaman tidak menentukan sumber dan tidak dihitung dalam metrik source-aware baru. Kecocokan lokasi sitasi bukan bukti dukungan klaim.

> **Indeks:** ingestion membangun koleksi kandidat, bukan mengaktifkannya otomatis. Setelah memeriksa manifest dan jumlah chunk, atur `CHROMA_COLLECTION` secara eksplisit ke nama kandidat untuk mengaktifkannya, lalu mulai ulang aplikasi. Indeks lama tanpa manifest lengkap berstatus `UNKNOWN`; kompatibilitasnya belum terbukti. Jangan hapus indeks lama untuk melakukan aktivasi.

> **Evaluasi:** dataset baru dapat memakai `relevant_sources`, misalnya `[{"source":"book.pdf","page":35}]`. Hit@k menghitung query dengan sedikitnya satu pasangan relevan; precision menghitung chunk relevan dibagi k, termasuk chunk duplikat. Retrieval gagal dan label tanpa sumber dikecualikan. Indikator frasa OOS bukan akurasi penanganan OOS. CLI menolak output yang sudah ada, tetapi checkpoint/resume belum tersedia.

**Tugas:** Ujian Tengah Semester (UTS) — Pengantar Generative AI  
**Fokus:** Prototipe RAG end-to-end yang berjalan nyata, evaluasi sistematis, laporan metodologi PDF, dan video demo.  
**Dokumen Sumber:** *The Official Guide to the TOEFL Test, Fourth Edition* (ETS, 2012).

---

## 📌 Ringkasan Proyek

**TOEFL Mate** adalah chatbot asisten pembelajaran TOEFL interaktif yang dibangun menggunakan arsitektur **Retrieval-Augmented Generation (RAG)** end-to-end. Sistem menjawab pertanyaan seputar format tes, strategi pengerjaan, dan rubrik penilaian TOEFL berdasarkan buku resmi ETS dengan menyertakan sitasi nomor halaman yang dapat diverifikasi, menjaga aturan *grounding* (tidak berhalusinasi), serta mengakui keterbatasan informasi untuk pertanyaan di luar cakupan (*out-of-scope*).

---

## 🏗️ Arsitektur Sistem

```text
[PDF Dokumen (data/)]
         │
         ▼ (PyMuPDF / fitz - 1-based indexing)
[Ekstraksi Teks per Halaman + Normalisasi Unicode]
         │
         ▼ (Chunk size: 500 chars, Overlap: 100 chars)
[Potongan Teks + Metadata sumber/halaman]
         │
         ▼ (SentenceTransformers: all-MiniLM-L6-v2)
[Vektor Embedding 384 Dimensi (Lokal)]
         │
         ▼
[ChromaDB Vector Store (L2 distance)]
         ▲
         │ (Top-k Similarity Search)
   [Pertanyaan Pengguna]
         │
         ▼
[Penyusunan Prompt Terstruktur + SOP Aturan Grounding]
         │
▼ (Groq Cloud API - model dari GROQ_MODEL)
[Generasi Jawaban Berbasis Konteks + Sitasi [NamaDokumen.pdf, Halaman X]]
         │
         ▼
[Streamlit Web UI / Pipeline Evaluasi]
```

### Komponen Kunci:
1. **Ekstraksi PDF:** PyMuPDF (`fitz`) mengekstrak teks tiap halaman secara berurutan dengan mempertahankan indeks halaman 1-based (`PDF Page 1..668`). Dilengkapi normalisasi Unicode (`NFKD`) untuk mengurai ligatur (`fi`, `fl`).
2. **Chunking:** Chunk berukuran 500 karakter dengan overlap 100 karakter untuk mempertahankan kesinambungan konteks antar batas chunk.
3. **Embedding Lokal:** Model Sentence Transformers dari `EMBEDDING_MODEL` berjalan lokal di CPU/GPU. Saat generasi, hanya potongan hasil retrieval (bukan seluruh PDF) dikirim ke Groq.
4. **Vector Store:** ChromaDB dengan persistent storage di folder `chroma_db/`, menggunakan metrik jarak L2 (`hnsw:space: l2`).
5. **Generasi LLM:** Groq API memakai satu konfigurasi `GROQ_MODEL` untuk UI, generator, dan evaluasi. SOP mewajibkan grounding serta sitasi `[NamaDokumen.pdf, Halaman X]` pada klaim faktual.
6. **Antarmuka Pengguna:** Streamlit Web UI dengan kontrol SOP (pilihan bahasa Indonesia/Inggris, gaya jawaban ringkas/bertahap, tingkat kesulitan dasar/menengah/lanjutan, slider `top_k`, dan expander cuplikan sumber halaman).

---

## 📁 Struktur Direktori

```text
UTS TOEFL Mate RAG Study Assistant/
├── app.py                      # Aplikasi Streamlit Web UI
├── config.py                   # Konfigurasi terpusat & environment loader
├── requirements.txt            # Dependensi Python
├── .env.example                # Template konfigurasi rahasia
├── .gitignore                  # Git ignore untuk secrets, database, & PDF
├── README.md                   # Dokumentasi instalasi dan penggunaan
├── data/                       # Tempat penyimpanan file PDF sumber
│   ├── eBook_TOEFL_Official_Guide_4e.pdf
│   └── PRE-TEST & MODUL BK CFLT 2026.pdf
├── scripts/
│   ├── ingest_pdf.py           # Ingestion PDF ke ChromaDB
│   ├── evaluate.py             # Evaluasi otomatis dataset pengujian
│   └── build_report.py         # Pembuat laporan metodologi evaluasi PDF
├── src/
│   ├── __init__.py
│   ├── ingestion.py            # Modul ekstraksi & chunking teks
│   ├── embeddings.py           # Modul Sentence Transformers lokal
│   ├── retriever.py            # Modul ChromaDB indexing & retrieval
│   ├── generator.py            # Modul generasi LLM via Groq API
│   ├── prompts.py              # System of Prompts (SOP) & prompt template
│   └── evaluation.py           # Logika penghitungan metrik (Recall, Precision, OOS)
├── evaluation/
│   ├── test_questions.json     # Dataset 30 pertanyaan berlabel terverifikasi
│   ├── results.json            # Hasil evaluasi aktual baseline (top_k=5)
│   ├── results.csv             # Hasil evaluasi tabular baseline
│   ├── results_k3.json         # Hasil evaluasi perbandingan (top_k=3)
│   └── results_k3.csv          # Hasil evaluasi tabular perbandingan
├── tests/
│   ├── test_ingestion.py       # Unit test pembersihan & chunking
│   ├── test_retrieval.py       # Unit test embedding & ChromaDB
│   └── test_citations.py       # Unit test prompt, sitasi, & metrik
└── reports/
    └── methodology_evaluation.pdf  # Laporan evaluasi metodologi PDF
```

---

## 🚀 Panduan Instalasi & Menjalankan Aplikasi

### 1. Prasyarat Lingkungan
- Python 3.11 atau lebih baru (Diuji pada Python 3.13.6 Windows 64-bit).
- Git (opsional).

### 2. Instalasi Dependensi
Buka terminal (PowerShell atau Command Prompt) pada direktori proyek:

```powershell
pip install -r requirements.txt
```

### 3. Konfigurasi Lingkungan (`.env`)
Salin file template `.env.example` menjadi `.env`:

```powershell
Copy-Item .env.example .env
```

Buka file `.env` dan masukkan API Key Groq Anda:
```dotenv
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=100
TOP_K=5
RELEVANCE_THRESHOLD=1.5
```

### 4. Ingestion PDF ke ChromaDB
Pastikan PDF sumber berada di dalam folder `data/`. Jalankan skrip ingestion:

```powershell
python scripts/ingest_pdf.py
```

Skrip membangun **koleksi kandidat** dan manifest audit di `chroma_db/manifests/`; koleksi aktif tidak dihapus atau diganti otomatis. Setelah memverifikasi kandidat, aktifkan nama koleksi yang dicetak skrip melalui `CHROMA_COLLECTION` di `.env`, lalu restart aplikasi. Jika build gagal, indeks aktif tetap digunakan.

### 5. Menjalankan Web UI Streamlit
Jalankan aplikasi web lokal:

```powershell
python -m streamlit run app.py
```
Aplikasi akan otomatis terbuka pada browser di `http://localhost:8501`.

---

## 🧪 Pengujian Unit (Unit Tests)

Jalankan rangkaian unit test lengkap menggunakan `pytest`:

```powershell
python -m pytest tests/ -v
```

**Hasil pengujian harus selalu dibaca dari run terbaru.** Komponen teruji:
  - `test_ingestion.py`: Pembersihan spasi, karakter kontrol, normalisasi unicode, chunking dengan overlap, validasi batas argumen.
  - `test_retrieval.py`: Embedding dimensi, konsistensi representasi vektor, pembuatan koleksi ChromaDB, pencarian query berbasis kemiripan L2, filtering threshold.
   - `test_citations.py`: prompt dwibahasa, sitasi sumber-halaman, variasi Unicode, dan validasi terhadap konteks multi-dokumen.
   - `test_config.py`, `test_ingestion_safety.py`, dan `test_evaluation_pipeline.py`: validasi konfigurasi, keamanan build kandidat, serta status evaluasi gagal/parsial.

---

## 📊 Pipeline Evaluasi & Pembuatan Laporan PDF

### 1. Dataset Evaluasi (`evaluation/test_questions.json`)
Dataset terdiri atas **30 pertanyaan** yang telah diverifikasi manusia terhadap teks PDF asli:
- **10 Pertanyaan Faktual:** Memiliki jawaban eksplisit dalam dokumen dengan label halaman PDF terverifikasi.
- **10 Pertanyaan Konseptual:** Membutuhkan sintesis lintas paragraf/bab.
- **5 Pertanyaan Sitasi & Relevansi:** Menguji presisi pengambilan fakta spesifik.
- **5 Pertanyaan Out-of-Scope:** Pertanyaan di luar buku panduan (misal: biaya tes tahun 2025, visa Australia, IELTS, UTBK) dengan target sistem mengakui keterbatasan.

### 2. Menjalankan Evaluasi
Jalankan skrip evaluasi baseline (`top_k=5`) ke berkas baru agar artefak historis tidak tertimpa:
```powershell
python scripts/evaluate.py --top_k 5 --output evaluation/results_v2_k5.json
```

Jalankan evaluasi variasi komparasi (`top_k=3`):
```powershell
python scripts/evaluate.py --top_k 3 --output evaluation/results_v2_k3.json
```

### 3. Status hasil historis dan interpretasi metrik

| Metrik Evaluasi | Baseline (`top_k=5`) | Variasi (`top_k=3`) | Keterangan & Definisi |
| :--- | :---: | :---: | :--- |
| **Recall@K** | **0.3200** (32.0%) | **0.2400** (24.0%) | Proporsi query yang berhasil memuat minimal 1 halaman target di top-K |
| **Precision@K** | **0.1040** (10.4%) | **0.1333** (13.3%) | Rata-rata proporsi chunk relevan terhadap total chunk yang diambil |
| **Citation Accuracy** | *Belum dihasilkan* | *Belum dihasilkan* | Run historis tidak memiliki jawaban generation |
| **OOS Handling** | *Tergantung Groq API* | *Tergantung Groq API* | Proporsi pertanyaan di luar cakupan yang diakui secara jujur |
| **Avg Latency** | *Tergantung Groq API* | *Tergantung Groq API* | Waktu respon generasi LLM per pertanyaan (detik) |
| **Answer Correctness** | *Review Manual* | *Review Manual* | Kesesuaian jawaban terhadap kunci jawaban acuan |
| **Groundedness** | *Review Manual* | *Review Manual* | Proporsi klaim jawaban yang didukung oleh konteks dokumen |

> **Status historis:** run ini mengevaluasi retrieval karena seluruh generation gagal saat API key belum dikonfigurasi. Jangan gunakan nilai ini untuk mengklaim correctness, groundedness, sitasi, OOS, atau latency generation.
> **Analisis Trade-Off retrieval:**
> Peningkatan `top_k` dari 3 menjadi 5 meningkatkan **Recall** sebesar **+33.3% relatif** (dari 0.2400 ke 0.3200), membuktikan jendela konteks yang lebih luas membantu menemukan halaman target. Sebaliknya, **Precision** menurun dari 0.1333 menjadi 0.1040 akibat masuknya potongan teks non-target.

### 4. Membangun Laporan PDF Metodologi
Jalankan skrip generator PDF berbasis ReportLab:
```powershell
python scripts/build_report.py
```
Untuk hasil baru, gunakan output baru agar laporan historis tetap terjaga:
```powershell
python scripts/build_report.py --results evaluation/results_v2_k5.json --comparison evaluation/results_v2_k3.json --output reports/methodology_evaluation_v2.pdf
```

---

## ⚖️ Keterbatasan, Etika, dan Hak Cipta

1. **Batasan Sumber Buku:** Dokumen yang digunakan adalah *The Official Guide to the TOEFL Test, 4th Edition* (ETS, 2012). Peserta tes harus memahami bahwa beberapa kebijakan terkini (seperti durasi tes dan jumlah soal yang diperpendek pada reformasi 2019/2023) mungkin berbeda dengan edisi 2012 ini.
2. **Hak Cipta:** Konten buku adalah hak cipta Educational Testing Service (ETS) dan McGraw-Hill. Sistem ini hanya menggunakan kutipan kontekstual ringkas untuk tujuan studi akademik (Fair Use) dan **tidak mendistribusikan ulang PDF lengkap**.
3. **Bukan Pengganti Instruktur:** Sistem berfungsi sebagai alat bantu belajar dan navigasi referensi, bukan pengganti pelatihan resmi atau instruktur profesional.
4. **Soal Latihan Buatan AI:** Jika model diminta membuat soal latihan, sistem wajib menyertakan label bahwa soal tersebut adalah simulasi AI dan bukan materi resmi ETS.
