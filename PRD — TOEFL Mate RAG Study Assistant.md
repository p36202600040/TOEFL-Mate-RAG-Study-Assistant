# PRD — TOEFL Mate: RAG Study Assistant

**Status:** MVP untuk UTS Pengantar Generative AI  
**Target:** Prototipe RAG end-to-end, evaluasi sistematis, laporan PDF, dan video demo maksimal 5 menit.  
**Dokumen sumber:** *The Official Guide to the TOEFL Test, Fourth Edition* (ETS, 2012), PDF yang disediakan kelompok.

## 1. Tujuan

Membangun chatbot pembelajaran TOEFL yang menjawab pertanyaan berdasarkan dokumen PDF melalui pipeline Retrieval-Augmented Generation (RAG). Jawaban harus menyertakan rujukan halaman yang relevan, mengakui jika informasi tidak ditemukan, dan dapat dievaluasi dengan eksperimen yang bisa diulang.

Proyek dinilai dari pipeline yang benar-benar berjalan dan evaluasi yang jujur—bukan hanya tampilan chatbot.

## 2. Pengguna dan kebutuhan

- Mahasiswa/pelajar yang ingin memahami materi TOEFL dari dokumen sumber.
- Penguji/dosen yang perlu melihat pipeline, sumber jawaban, metodologi, metrik, dan hasil pengujian.
- Pengembang yang perlu dapat memasang dan menjalankan proyek dari README.

## 3. Batasan MVP

**Termasuk:**
- Aplikasi web lokal menggunakan Streamlit.
- Ingestion PDF: ekstraksi teks, pembersihan dasar, chunking, embedding, penyimpanan vector database.
- Retrieval top-k, penyusunan prompt berbasis konteks, generasi jawaban melalui Groq API.
- Sitasi halaman sumber untuk konteks yang digunakan.
- Riwayat percakapan selama sesi, tombol hapus/percakapan baru, dan tampilan sumber yang dipakai.
- Pengaturan dasar melalui SOP (System of Prompts): bahasa jawaban, tingkat penjelasan, dan aturan menjawab hanya berdasarkan konteks.
- Skrip evaluasi, dataset pertanyaan berlabel, hasil metrik, unit test, laporan evaluasi PDF, dan panduan demo.
- Pesan kesalahan yang jelas jika API key, model, dokumen, atau indeks tidak tersedia.

**Tidak termasuk untuk MVP satu hari:**
- Integrasi Telegram/WhatsApp, login multi-user, deployment produksi, pembayaran, fine-tuning, atau klaim bahwa sistem menggantikan instruktur TOEFL.
- Mengirim seluruh PDF ke LLM. Hanya potongan teks hasil retrieval yang boleh dikirim untuk generasi.

## 4. Stack yang disarankan

- Python 3.11
- Streamlit — antarmuka web
- PyMuPDF — ekstraksi PDF dan nomor halaman
- Sentence Transformers — embedding lokal
- ChromaDB — vector store lokal
- Groq SDK/API — generasi jawaban
- `python-dotenv` — konfigurasi rahasia
- `pytest` — unit test
- `reportlab` atau library Python yang stabil — pembuatan laporan PDF

Pilih model embedding yang kompatibel dan tersedia secara nyata. Nama model LLM Groq harus berasal dari konfigurasi dan diverifikasi terhadap model yang tersedia saat implementasi; jangan mengasumsikan nama model. Jika dependensi atau API berubah, dokumentasikan pilihan aktual di README.

## 5. Alur sistem wajib

1. Pengguna meletakkan PDF di folder `data/`.
2. Skrip ingestion mengekstrak teks per halaman dan mempertahankan metadata nomor halaman.
3. Teks dibersihkan secara minimal lalu dibagi menjadi chunk dengan overlap yang dapat dikonfigurasi.
4. Chunk di-embed secara lokal dan disimpan ke ChromaDB beserta `source`, `page`, dan `chunk_id`.
5. Pertanyaan pengguna di-embed dan digunakan untuk mengambil top-k chunk yang relevan.
6. Prompt generation berisi pertanyaan, konteks retrieval, aturan grounding, dan format sitasi.
7. LLM menjawab berdasarkan konteks. Jika konteks tidak cukup, sistem menyatakan keterbatasan dan tidak mengarang fakta.
8. UI menampilkan jawaban serta sumber/nomor halaman yang dapat dibuka atau diperiksa.
9. Pipeline evaluasi dapat menjalankan pertanyaan uji dengan konfigurasi yang tercatat dan menyimpan hasil aktual.

## 6. Persyaratan fungsional

### FR-01 — Ingestion
- Ada perintah terpisah untuk membangun/memperbarui indeks.
- PDF yang gagal dibaca atau tidak memiliki teks memberi pesan yang jelas.
- Nomor halaman harus konsisten dan terdokumentasi (misalnya indeks halaman PDF 1-based); jangan menyamakan nomor halaman PDF dengan nomor cetak buku jika berbeda.
- Simpan metadata pada setiap chunk.

### FR-02 — Retrieval dan generation
- Top-k, chunk size, overlap, dan model embedding dapat dikonfigurasi.
- Tampilkan sumber yang diambil, bukan hanya jawaban akhir.
- Prompt melarang model mengklaim bahwa pernyataan berasal dari buku jika tidak didukung konteks.
- Sediakan ambang relevansi yang dapat dikonfigurasi jika metode vector store mendukungnya; jelaskan arti nilai distance/score yang digunakan.
- Jangan mengklaim skor retrieval sebagai probabilitas kebenaran.

### FR-03 — UI
- UI sederhana, rapi, responsif, dan berbahasa Indonesia secara default.
- Pengguna dapat bertanya dalam bahasa Indonesia atau Inggris.
- Tampilkan indikator proses dan pesan error yang bisa ditindaklanjuti.
- Tampilkan sumber/halaman dan cuplikan singkat konteks yang digunakan.
- Jangan menampilkan API key atau stack trace sensitif.

### FR-04 — SOP / prompt controls
Sediakan pengaturan minimal untuk:
- Bahasa jawaban: Indonesia/Inggris.
- Gaya: ringkas atau penjelasan bertahap.
- Tingkat kesulitan: dasar/menengah/lanjutan.
- Aturan grounding: hanya gunakan konteks dokumen untuk klaim tentang isi buku; jika tidak cukup, katakan tidak ditemukan.
- Pertanyaan latihan yang dibuat model harus orisinal, diberi label sebagai latihan buatan AI, dan tidak diklaim sebagai soal resmi ETS.

### FR-05 — Keamanan dan copyright
- Rahasia hanya dibaca dari `.env`; sediakan `.env.example` tanpa nilai rahasia.
- `.env`, PDF sumber, indeks privat, cache, dan kredensial masuk `.gitignore` bila sesuai.
- Jangan mencetak API key di log.
- Jangan mereproduksi atau mendistribusikan bagian besar buku. Gunakan kutipan seperlunya untuk menjelaskan jawaban dan berikan rujukan.
- Tambahkan peringatan bahwa dokumen adalah edisi 2012 dan tidak otomatis mewakili format TOEFL terkini.

## 7. Metodologi evaluasi wajib

Buat setidaknya 30 pertanyaan yang telah diperiksa manusia berdasarkan PDF:
- 10 pertanyaan faktual dengan jawaban eksplisit.
- 10 pertanyaan konseptual yang membutuhkan sintesis informasi.
- 5 pertanyaan yang memeriksa relevansi retrieval dan sitasi.
- 5 pertanyaan di luar cakupan dokumen.

Setiap item dataset minimal berisi `id`, `category`, `question`, `reference_answer` (jika relevan), `relevant_pages` dan/atau `relevant_chunk_ids` yang diverifikasi, serta catatan penilai. Jangan membuat jawaban acuan atau label relevansi palsu. Pertanyaan out-of-scope harus memiliki expected behavior berupa pengakuan bahwa sumber tidak memadai.

### Metrik
- **Recall@5:** apakah setidaknya chunk relevan yang diberi label muncul di lima hasil retrieval teratas; jelaskan definisi agregasi yang dipakai.
- **Precision@5:** jumlah hasil relevan di top 5 dibagi 5, jika label relevansi memadai.
- **Citation accuracy:** sitasi halaman yang benar / seluruh sitasi yang diperiksa.
- **Answer correctness:** jawaban yang memenuhi rubrik terhadap jawaban acuan / jawaban yang dinilai.
- **Groundedness:** klaim faktual yang didukung konteks / seluruh klaim faktual yang diperiksa.
- **Out-of-scope handling:** jumlah pertanyaan di luar cakupan yang diakui dengan benar / total pertanyaan out-of-scope.
- **Latency:** waktu respons per pertanyaan dan rata-rata; catat bila cold start atau unduhan model memengaruhi pengukuran.

Untuk metrik berbasis penilaian manusia, sediakan rubrik yang eksplisit dan tandai status penilaian. Jangan menyamarkan penilaian manual sebagai metrik otomatis. Laporkan jumlah sampel, konfigurasi, tanggal, kondisi API, dan keterbatasan. Jangan mengarang hasil; angka harus berasal dari run evaluasi yang nyata.

### Analisis eksperimen
- Jalankan evaluasi baseline dengan konfigurasi yang dicatat.
- Jika waktu memungkinkan, bandingkan satu variasi yang jelas, misalnya `top_k=3` vs `top_k=5`, dengan dataset dan kondisi yang sama.
- Simpan pertanyaan, hasil retrieval, jawaban, sitasi, waktu, skor, dan error untuk audit.
- Analisis setidaknya tiga contoh: berhasil, salah/kurang tepat, dan out-of-scope. Jika tidak ditemukan kesalahan tertentu, jangan dibuat-buat; jelaskan contoh yang benar-benar muncul.
- Unit test bukan pengganti evaluasi kualitas jawaban.

## 8. Output/deliverables

1. Source code lengkap dan terstruktur.
2. `README.md` dengan instalasi, konfigurasi `.env`, ingestion, menjalankan aplikasi, menjalankan tes, menjalankan evaluasi, dan membuat PDF.
3. `evaluation/test_questions.json` berisi dataset berlabel yang telah diverifikasi.
4. `evaluation/results.json` dan ringkasan CSV/Markdown berisi hasil aktual.
5. `reports/methodology_evaluation.pdf` yang memuat:
   - tujuan dan pertanyaan penelitian;
   - sumber data dan batasannya;
   - arsitektur dan konfigurasi RAG;
   - proses pembuatan dataset uji;
   - definisi metrik dan rubrik;
   - hasil aktual, tabel, analisis kesalahan;
   - keterbatasan, etika/copyright, dan kesimpulan.
6. Video demo dengan durasi maksimal 5 menit. Sediakan outline/timestamp untuk merekam; jangan mengklaim video telah dibuat atau diunggah oleh aplikasi.
7. `.env.example`, `requirements.txt`, `.gitignore`, dan unit test.

Jika hasil evaluasi belum dijalankan, PDF harus jelas berstatus “rancangan evaluasi / belum diuji”; jangan mengisi hasil fiktif.

## 9. Struktur folder yang dituju

```text
toefl-mate/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── data/                       # PDF lokal; jangan commit jika berhak cipta
├── scripts/
│   ├── ingest_pdf.py
│   ├── evaluate.py
│   └── build_report.py
├── src/
│   ├── ingestion.py
│   ├── embeddings.py
│   ├── retriever.py
│   ├── generator.py
│   ├── prompts.py
│   └── evaluation.py
├── evaluation/
│   ├── test_questions.json
│   ├── results.json
│   └── results.csv
├── tests/
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   └── test_citations.py
└── reports/
    ├── methodology_evaluation.pdf
    └── demo_outline.md
```

Struktur boleh disederhanakan jika itu meningkatkan keandalan MVP, tetapi pemisahan ingestion, retrieval, generation, evaluasi, dan UI harus tetap jelas.

## 10. Kriteria penerimaan

MVP diterima jika:
- Instalasi bersih mengikuti README berhasil di Windows.
- Indeks dapat dibuat dari PDF tanpa mengirim seluruh PDF ke LLM.
- Pertanyaan pengguna memicu retrieval dan generasi melalui Groq API.
- Jawaban menampilkan sumber dan nomor halaman yang dapat diverifikasi.
- Sistem mengakui saat konteks tidak cukup.
- Skrip evaluasi berjalan dan menyimpan hasil aktual serta konfigurasi.
- Unit test berjalan; kegagalan yang diketahui didokumentasikan.
- PDF laporan dibuat dari hasil aktual atau secara jelas diberi label belum diuji.
- Ada panduan demo yang muat dalam lima menit.
- Tidak ada secret/API key yang masuk source control.

## 11. Prioritas pengerjaan

**P0 — wajib:** ingestion → vector store → retrieval → Groq → sitasi → UI → evaluasi dasar → README.  
**P1 — setelah P0 stabil:** rubrik penilaian manual, perbandingan konfigurasi, PDF laporan otomatis, UI lebih rapi.  
**P2 — jangan dikerjakan sebelum MVP selesai:** Telegram/WhatsApp, login, deployment produksi, fitur yang tidak mendukung rubrik UTS.

## 12. Prompt eksekusi untuk coding agent

Baca `prd.md` ini sampai selesai sebelum mengubah file. Periksa struktur proyek dan PDF sumber yang tersedia. Implementasikan TOEFL Mate sebagai MVP RAG end-to-end sesuai PRD, dengan prioritas pada alur yang benar-benar berjalan dan evaluasi yang dapat direproduksi. Gunakan Python 3.11, Streamlit, PyMuPDF, Sentence Transformers lokal, ChromaDB, Groq API, dotenv, dan pytest kecuali ada kendala nyata; jika harus mengganti teknologi, jelaskan alasannya di README.

Kerjakan langsung di workspace: buat source code, ingestion script, UI, konfigurasi SOP, dataset evaluasi, skrip evaluasi, unit test, README, dan pembuat laporan PDF. Jangan berhenti pada rencana atau pseudocode. Jangan mengarang nama model yang tidak tersedia, hasil evaluasi, jawaban acuan, label relevansi, atau klaim keberhasilan. Untuk data yang belum dapat diverifikasi, tandai `TODO`/`NOT RUN` dan jelaskan cara menyelesaikannya. Jangan pernah menaruh API key di source code.

Setelah implementasi, jalankan pemeriksaan yang tersedia: instalasi/dependency check, unit test, ingestion jika PDF tersedia, dan evaluasi jika API key tersedia. Perbaiki error yang dapat diperbaiki. Akhiri dengan ringkasan file yang dibuat, perintah menjalankan aplikasi/ingestion/evaluasi/laporan, hasil tes yang benar-benar dijalankan, hambatan yang tersisa, dan checklist deliverables UTS. Jangan mengklaim tugas selesai jika ada bagian penting yang belum dijalankan.
