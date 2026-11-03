# Laporan Perbaikan V2 — TOEFL Mate RAG Study Assistant

**Tanggal:** 30 Oktober 2026  
**Acuan:** `PRD — TOEFL Mate RAG Study Assistant.md`, `reviewv2.md`, dan `planning_perbaikan_v2.md`  
**Status:** perbaikan inti diterapkan dan diuji; validasi manusia serta optimasi retrieval lanjutan masih terbuka.

## Ringkasan hasil

Perbaikan ini berfokus pada bukti dan keandalan, bukan menambah fitur di luar MVP. Retrieval query Indonesia kini diperkaya dengan padanan istilah Inggris yang umum secara generik; tidak ada jawaban atau nomor halaman yang di-hardcode. Pada dataset historis yang sama, Hit/Recall@5 naik dari **0,3200** menjadi **0,5600**. Pertanyaan regresi mengenai empat bagian TOEFL kini mengambil halaman PDF 35 dan berhasil dijawab oleh aplikasi dengan sitasi sumber-halaman.

Target internal Hit@5 0,70 **belum tercapai**. Hasil ini tidak boleh dipresentasikan sebagai retrieval yang sudah andal untuk seluruh jenis pertanyaan.

## Perubahan implementasi

| Area | Berkas utama | Perubahan |
|---|---|---|
| Konfigurasi model | `config.py`, `src/generator.py`, `app.py`, `scripts/evaluate.py` | Satu default `GROQ_MODEL`; UI, generator, dan evaluator mencatat/memakai konfigurasi yang sama. Parameter utama divalidasi. |
| Retrieval lintas bahasa | `src/retriever.py` | Menambah enrichment istilah Indonesia–Inggris yang generik sebelum embedding query. Nilai `top_k=0` dan threshold negatif kini ditolak. |
| Ingestion aman | `scripts/ingest_pdf.py`, `src/ingestion.py` | Ingestion membangun koleksi kandidat ber-ID unik dan manifest hash dokumen. Koleksi aktif tidak dihapus/diganti otomatis; build gagal mempertahankan indeks aktif. |
| Sitasi dan prompt | `src/prompts.py`, `src/evaluation.py` | Kontrak sitasi menjadi `[NamaDokumen.pdf, Halaman X]`; parser mendukung bentuk lama/Unicode, lalu memeriksa keberadaan source-halaman pada konteks retrieval. |
| Evaluasi | `src/evaluation.py`, `scripts/evaluate.py` | Menambah `run_id`, versi prompt/dataset, status per item, latency retrieval/generation/end-to-end, citation coverage, dan citation accuracy micro. Opsi `--limit` tersedia untuk preflight mendatang. |
| Error handling | `app.py`, `src/generator.py` | Retrieval UI memberi pesan aman saat gagal. Error rate-limit, timeout, dan model tidak tersedia disederhanakan agar detail provider/organisasi tidak tampil ke pengguna. |
| Follow-up | `app.py` | Follow-up pendek membawa pertanyaan pengguna sebelumnya ke query retrieval. Ini perbaikan parsial; kualitas referensi “bagian kedua” belum memadai. |
| Dokumentasi dan laporan | `README.md`, `scripts/build_report.py`, `evaluation/human_review_template.csv` | README menjelaskan kandidat ingestion, status historis, dan sitasi baru. PDF baru dibuat tanpa menimpa PDF lama. Template review manusia ditambahkan. |
| Test | `tests/test_config.py`, `tests/test_ingestion_safety.py`, `tests/test_evaluation_pipeline.py`, test yang diperluas | Menguji konfigurasi, keamanan koleksi aktif, status generation gagal, sitasi multi-dokumen/Unicode, dan enrichment query. |

## Pemetaan temuan review

| Temuan `reviewv2.md` | Status | Bukti / batasan |
|---|---|---|
| Konfigurasi model bercabang | Diperbaiki | Default/fallback yang berbeda disatukan ke `config.GROQ_MODEL`. Model efektif run baru: `openai/gpt-oss-120b`, dari konfigurasi lingkungan saat run. |
| Rebuild menghapus indeks aktif | Diperbaiki pada skrip baru | Kandidat dibuat terpisah; test memverifikasi indeks aktif tetap ada saat kandidat gagal. Aktivasi kandidat masih manual lewat `CHROMA_COLLECTION` agar aman. |
| Parser sitasi tidak membaca format nyata | Diperbaiki sebagian | Parser menangani sitasi sumber-halaman dan kurung Unicode; 37/40 sitasi top-k 5 dan 36/37 sitasi top-k 3 berada dalam konteks yang diretrieve. Ketepatan klaim terhadap isi halaman belum dinilai manusia. |
| Pertanyaan Indonesia inti gagal | Diperbaiki untuk regression case | AppTest menghasilkan jawaban dan konteks mencakup halaman 35. Hit@5 naik, tetapi masih 0,56. |
| Evaluasi generation historis kosong | Diperbaiki dengan run baru | Run top-k 5 memiliki 29 sukses/1 rate-limit; top-k 3 memiliki 30 sukses. Hasil historis tidak diubah. |
| Agregasi/latency evaluasi tidak jelas | Diperbaiki sebagian | Metrik micro, coverage, dan latency terpisah tersedia. Penilaian OOS masih berbasis indikator teks dan perlu review manusia. |
| Error mentah berisiko tampil | Diperbaiki sebagian | UI dan error Groq umum disanitasi. Audit keamanan menyeluruh serta seluruh jenis exception belum dilakukan. |
| Ketidakkonsistenan README/laporan | Diperbaiki sebagian | README diperbarui dan laporan V2 dibuat. `reports/methodology_evaluation.pdf` historis tetap memuat konfigurasi lama sesuai artefak aslinya. |
| Follow-up percakapan | Diperbaiki sebagian | Konteks pertanyaan sebelumnya masuk query, tetapi smoke test “Jelaskan bagian kedua tadi” masih tidak mengambil bukti Listening yang tepat. |

## Konfigurasi efektif nonrahasia

| Parameter | Run top-k 5 dan top-k 3 |
|---|---|
| Embedding | `all-MiniLM-L6-v2` |
| Model generation efektif | `openai/gpt-oss-120b` |
| Chunk size / overlap | 500 / 100 karakter |
| Threshold L2 | 1,5; semakin kecil berarti vektor lebih mirip, bukan probabilitas benar |
| Sumber indeks aktif saat evaluasi | 4.156 chunk: 3.911 Official Guide dan 245 modul CFLT, menurut pemeriksaan sebelum perbaikan |
| Halaman | Indeks PDF 1-based, bukan selalu nomor cetak buku |

Embedding dijalankan lokal. Hanya konteks hasil retrieval yang dikirim ke Groq untuk generation; seluruh PDF tidak dikirim.

## Hasil eksperimen retrieval dan generation

Semua angka memakai `evaluation/test_questions.json` historis: 25 pertanyaan in-scope berlabel halaman dan 5 pertanyaan OOS. Definisi proyek untuk Recall@K adalah **Hit@K**: satu jika sedikitnya satu halaman target ada pada top-k, lalu dirata-ratakan per query.

| Run | Top-k | Hit/Recall@K | Precision@K | Generation sukses/gagal | Citation accuracy micro | Citation coverage | OOS handling otomatis | Rata-rata latency generation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Historis baseline | 5 | 0,3200 | 0,1040 | 0 / 30 | Tidak tersedia | Tidak tersedia | Tidak tersedia | Tidak tersedia |
| V2 baseline | 5 | **0,5600** | **0,1920** | 29 / 1 | 0,3250 (40 sitasi) | 0,5600 | 0,8000 | 10,3043 dtk |
| Historis variasi | 3 | 0,2400 | 0,1333 | 0 / 30 | Tidak tersedia | Tidak tersedia | Tidak tersedia | Tidak tersedia |
| V2 variasi | 3 | **0,4400** | **0,2000** | 30 / 0 | 0,3243 (37 sitasi) | 0,5200 | 0,6000 | 7,7086 dtk |

Catatan integritas:

- Run V2 top-k 5 berstatus `PARTIAL_OR_NOT_RUN` karena satu request menerima rate limit. Error disimpan sebagai status item; pesan yang ditampilkan aplikasi kini aman.
- Run V2 top-k 3 berstatus `COMPLETE` dengan 30 jawaban generation berhasil.
- Citation accuracy di atas membandingkan nomor halaman sitasi dengan label halaman dataset. Ini **bukan** bukti semua klaim jawaban didukung isi konteks.
- OOS handling masih deteksi otomatis berbasis indikator keterbatasan; harus ditinjau manusia agar jawaban yang juga mengarang fakta tidak salah dianggap berhasil.
- Latency tidak memisahkan variasi jaringan/provider dan bukan benchmark performa produksi.
- Kenaikan Hit@5 adalah 6 dari 25 query tambahan dibanding baseline historis. Target internal 0,70 belum terpenuhi.

## Bukti pengujian aktual

| Pemeriksaan | Hasil |
|---|---|
| Unit/integration-like tests lokal | **59 passed**, 1 warning deprecation dari dependency AnyIO/pytest |
| `pip check` | `No broken requirements found.` |
| Syntax compile Python | Berhasil untuk seluruh berkas Python yang ditemukan |
| AppTest — pertanyaan Indonesia skor TOEFL | Tidak ada exception; jawaban menyebut Reading/Listening/Speaking/Writing 0–30, total 0–120, dan konteks mencakup halaman 35 |
| AppTest — pertanyaan OOS biaya 2025 | Tidak ada exception; aplikasi menyatakan informasi spesifik tidak tersedia dalam sumber |
| AppTest — bahasa Inggris/gaya ringkas dan hapus chat | Tidak ada exception; kontrol diterapkan dan riwayat berhasil dikosongkan |
| AppTest — follow-up “bagian kedua tadi” | Tidak ada exception, tetapi retrieval belum mengambil konteks Listening yang tepat; dicatat sebagai keterbatasan |
| Test keamanan ingestion | Indeks aktif fixture tetap ada ketika build kandidat dengan PDF hilang gagal |
| Browser visual/instalasi bersih | **Belum diverifikasi.** AppTest digunakan karena alat kendali Chrome tidak tersedia. |

## Artefak yang dihasilkan

| Artefak | Keterangan |
|---|---|
| `evaluation/results_v2_k5.json` dan `.csv` | Run baseline V2 top-k 5, termasuk satu rate-limit |
| `evaluation/results_v2_k3.json` dan `.csv` | Run variasi V2 top-k 3, semua generation berhasil |
| `evaluation/human_review_template.csv` | Template kosong untuk review manusia; belum diisi dan tidak boleh dianggap penilaian manusia |
| `reports/methodology_evaluation_v2.pdf` | Laporan baru dari run V2 baseline dan variasi; tidak mengganti laporan historis |
| `reports/perbaikan_v2.md` | Laporan perbaikan ini |

## Cara menjalankan

```powershell
# Unit test
python -m pytest tests/ -q

# Ingestion aman: membuat kandidat, tidak mengganti indeks aktif otomatis
python scripts/ingest_pdf.py

# Preflight terbatas di masa depan
python scripts/evaluate.py --top_k 5 --limit 1 --output evaluation/preflight_v3.json

# Evaluasi baru, jangan menimpa hasil historis
python scripts/evaluate.py --top_k 5 --output evaluation/results_v3_k5.json
python scripts/evaluate.py --top_k 3 --output evaluation/results_v3_k3.json

# Laporan baru
python scripts/build_report.py --results evaluation/results_v3_k5.json --comparison evaluation/results_v3_k3.json --output reports/methodology_evaluation_v3.pdf

# Aplikasi
python -m streamlit run app.py
```

Untuk mengaktifkan kandidat ingestion, salin tepat nama koleksi kandidat yang dicetak oleh skrip ke `CHROMA_COLLECTION` pada `.env`, lalu restart Streamlit. Jangan tulis isi `.env` ke laporan atau commit.

## Penilaian manusia

Status **belum dilakukan**. Gunakan `evaluation/human_review_template.csv` untuk menilai answer correctness, groundedness, perilaku OOS, dan dukungan sitasi. Jangan mengubah `NOT_RATED` menjadi status lain tanpa pemeriksaan manusia yang benar-benar dilakukan serta identitas/tanggal penilai.

## Keterbatasan dan pekerjaan tersisa

1. Hit@5 0,56 masih di bawah target internal 0,70. Kandidat model embedding multibahasa tidak tersedia di cache lokal saat diperiksa; eksperimen model baru tidak dijalankan agar tidak mengunduh model besar atau membangun indeks aktif tanpa persetujuan.
2. Satu request top-k 5 terkena rate limit. Mekanisme checkpoint/resume batch belum ditambahkan; evaluator kini setidaknya menyimpan status item sehingga run dapat diaudit.
3. Follow-up referensial masih lemah; perlu strategi query rewriting atau reranking yang diuji, bukan sekadar menambahkan riwayat.
4. Citation parsing dan validitas lokasi sudah diperbaiki, tetapi correctness, groundedness, serta dukungan klaim memerlukan review manusia.
5. OOS handling belum memakai rubrik manusia dan belum diuji terhadap jawaban campuran secara penuh.
6. PDF laporan V2 menggunakan run top-k 5 yang parsial dan dengan jujur diberi status evaluasi parsial. Buat laporan final dari baseline sukses penuh bila diperlukan.
7. Instalasi bersih Windows, audit riwayat Git, pengujian visual browser/mobile, dan video demo belum diverifikasi/dibuat oleh pekerjaan ini.

## Checklist acceptance criteria PRD

| Kriteria | Status |
|---|---|
| Instalasi bersih Windows dari README | Belum diverifikasi |
| Indeks dibangun tanpa mengirim seluruh PDF ke LLM | Terpenuhi secara desain; hanya konteks retrieval dikirim saat generation |
| Retrieval dan generation Groq berjalan | Terpenuhi, dibuktikan run V2 dan AppTest; satu request terkena rate limit |
| Jawaban menampilkan sumber/halaman yang dapat diverifikasi | Sebagian terpenuhi; format/parsing/konteks ada, dukungan klaim manusia belum selesai |
| Mengakui konteks tidak cukup | Sebagian terpenuhi; contoh OOS berhasil, evaluasi rubrik manusia belum selesai |
| Evaluasi menyimpan hasil aktual/konfigurasi | Terpenuhi untuk run V2 |
| Unit test berjalan | Terpenuhi: 59 passed |
| Laporan PDF hasil aktual atau jelas belum diuji | Terpenuhi: PDF V2 menyatakan evaluasi parsial |
| Panduan demo maksimal 5 menit | Ada; perlu diperbarui lagi bila ingin menampilkan angka V2 |
| Tidak ada secret dalam source control | Pemeriksaan file saat ini mendukung; audit riwayat Git belum dilakukan |
