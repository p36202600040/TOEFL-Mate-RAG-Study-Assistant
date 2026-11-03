# Planning Perbaikan V2 — TOEFL Mate RAG Study Assistant

**Tanggal:** 30 Oktober 2026  
**Acuan:** `PRD — TOEFL Mate RAG Study Assistant.md` dan `reviewv2.md`  
**Status:** Rencana kerja; implementasi dan eksperimen di bawah belum dijalankan.  
**Tujuan:** menuntaskan MVP yang andal, dapat dievaluasi ulang, dan siap dipresentasikan tanpa klaim kualitas yang belum terbukti.

## 1. Kondisi awal dan sasaran

Baseline yang tercatat dalam review:

- Skor reviewer **72/100**, estimasi progres MVP sekitar **80%**; keduanya bukan metrik akurasi model.
- **49 unit test lulus**.
- Indeks berisi **4.156 chunk dari dua dokumen**.
- Hit/Recall@5 **0,32**, Precision@5 **0,104**, pada 25 pertanyaan berlabel halaman.
- Groq aktif dalam pengujian interaktif, tetapi dua run evaluasi tersimpan memiliki nol jawaban berhasil.
- Pertanyaan Indonesia tentang empat bagian TOEFL mengalami penolakan keliru.
- Format sitasi, konfigurasi model, dan dokumentasi belum konsisten.

### Sasaran hasil

1. Pertanyaan inti berbahasa Indonesia dan Inggris dapat mengambil bukti yang tepat.
2. Jawaban dan sitasi dapat ditelusuri ke dokumen, halaman, dan konteks aktual.
3. Evaluasi mencatat keberhasilan, kegagalan, konfigurasi, serta penilaian manusia dengan jujur.
4. Kegagalan ingestion atau API tidak merusak indeks aktif atau memunculkan detail sensitif.
5. README, laporan, dan demo menggunakan bukti serta konfigurasi yang sama.

**Batas lingkup:** tidak menambah login, integrasi pesan, pembayaran, fine-tuning, atau deployment produksi. Tidak menjanjikan skor reviewer tertentu setelah perbaikan.

## 2. Prinsip pelaksanaan

- Pertahankan hasil evaluasi lama sebagai bukti historis; gunakan nama run baru.
- Jangan menghapus koleksi aktif untuk mencoba model atau konfigurasi baru.
- Pisahkan eksperimen retrieval tanpa API dari evaluasi generation berbiaya API.
- Ubah satu variabel utama per eksperimen agar penyebab perubahan hasil dapat dijelaskan.
- Jangan mengubah label hanya untuk meningkatkan skor. Perubahan label wajib memiliki bukti halaman dan catatan audit.
- Jangan melakukan auto-fallback ke model LLM lain tanpa mencatat model efektifnya.
- Jangan menulis key, isi `.env`, atau kutipan panjang dokumen ke log dan laporan publik.
- Semua checklist di dokumen ini menyatakan pekerjaan yang direncanakan, bukan pekerjaan selesai.

## 3. Urutan dan dependensi

```text
Tahap 0: Amankan baseline dan kontrak data
  |-- Tahap 1: Konfigurasi dan ingestion aman
  |-- Tahap 2: Audit dataset dan perbaikan retrieval
  `-- Tahap 3: Sitasi, grounding, dan pemulihan error
             |
             v
Tahap 4: Evaluasi end-to-end dan penilaian manusia
             |
             v
Tahap 5: Dokumentasi, instalasi bersih, dan demo
```

Tahap 4 baru dimulai setelah konfigurasi, kandidat retrieval, serta format sitasi stabil. Pekerjaan penguatan ingestion dilakukan sebelum eksperimen yang membutuhkan rebuild indeks.

## 4. Tahap 0 — Amankan baseline dan kontrak data

**Prioritas:** P0  
**Estimasi:** 1–2 jam kerja aktif.

### Pekerjaan

- [ ] Catat kondisi Git awal agar perubahan pengguna tidak tertimpa.
- [ ] Rekam baseline: versi Python/dependensi, model embedding, model LLM efektif, parameter chunk, threshold, top-k, dan identitas koleksi.
- [ ] Buat manifest indeks berisi versi skema, hash dokumen, nama sumber, jumlah chunk, dimensi/model embedding, parameter chunk, dan waktu build.
- [ ] Tentukan format `run_id`, misalnya `20261030_v2_baseline_k5`.
- [ ] Tentukan struktur hasil baru yang memuat `run_id`, versi dataset/prompt, manifest indeks, konfigurasi efektif, status per item, dan ringkasan error.
- [ ] Jalankan ulang test awal sebelum mengubah perilaku.

### Berkas sasaran

`config.py`, `src/evaluation.py`, `scripts/evaluate.py`; manifest dan utilitas tambahan bila diperlukan. Struktur akhir mengikuti pola proyek, tidak wajib membuat banyak modul baru.

### Kriteria selesai

Baseline lama tetap utuh; setiap hasil eksperimen baru dapat dikaitkan ke versi dataset, prompt, model, dan indeks tertentu tanpa menyimpan rahasia.

## 5. Tahap 1 — Satukan konfigurasi dan amankan ingestion

**Prioritas:** P0  
**Estimasi:** 3–5 jam kerja aktif.  
**Dependensi:** Tahap 0.

### 5.1 Konfigurasi tunggal

- [ ] Gunakan satu jalur resolusi model untuk UI, generator, dan evaluasi; hilangkan default model yang saling berbeda.
- [ ] Validasi parameter: `top_k > 0`, ukuran chunk positif, overlap lebih kecil daripada ukuran chunk, serta nilai threshold yang valid.
- [ ] Gunakan pemeriksaan `is None` untuk argumen opsional; jangan memakai `or` bila nilai nol perlu dibedakan dari tidak diisi.
- [ ] Catat model efektif dari request/hasil generation, bukan hanya nama dari konfigurasi awal.
- [ ] Tambahkan pemeriksaan kesiapan model Groq yang jelas; kegagalan harus menghasilkan petunjuk tindakan, bukan pergantian model diam-diam.

### 5.2 Build indeks yang aman

- [ ] Validasi seluruh path PDF dan lakukan ekstraksi sebelum mengubah indeks aktif.
- [ ] Bangun kandidat dalam koleksi baru dengan identitas unik.
- [ ] Verifikasi jumlah chunk, metadata, dimensi embedding, dan beberapa query pemeriksaan.
- [ ] Alihkan penunjuk koleksi aktif hanya setelah build sukses; penunjuk terakhir yang valid tetap tersedia untuk rollback.
- [ ] Tentukan kebijakan kegagalan parsial. Default yang disarankan: jangan aktifkan indeks baru jika ada dokumen wajib yang gagal.
- [ ] Kembalikan exit code gagal untuk build yang tidak valid; jangan melaporkan sukses saat seluruh file gagal.
- [ ] Tangani mismatch model/dimensi antara query dan indeks sebelum melakukan pencarian.

### Pengujian wajib

- [ ] PDF tidak ada, rusak, atau hanya berisi gambar tanpa OCR.
- [ ] Embedding gagal di tengah proses.
- [ ] Satu dokumen gagal dalam build multi-dokumen.
- [ ] Indeks lama tetap bisa di-query setelah build kandidat gagal.
- [ ] Aktivasi kandidat sukses dan pemulihan ke indeks sebelumnya.

**Berkas sasaran:** `config.py`, `app.py`, `src/generator.py`, `src/retriever.py`, `scripts/ingest_pdf.py`, dan test terkait.

**Kriteria selesai:** tidak ada jalur rebuild biasa yang menghapus indeks aktif sebelum kandidat tervalidasi; UI dan evaluasi menampilkan model efektif yang sama.

## 6. Tahap 2 — Audit label dan tingkatkan retrieval lintas bahasa

**Prioritas:** P0  
**Estimasi:** 4–8 jam kerja aktif, di luar unduhan model.  
**Dependensi:** manifest baseline dan ingestion aman.

### 6.1 Audit dataset

- [ ] Pertahankan dataset lama; buat versi baru bila skema atau label berubah.
- [ ] Audit 25 item in-scope terhadap PDF dan catat identitas/verifikasi manusia. Lima item OOS tetap diperiksa expected behavior-nya.
- [ ] Gunakan pasangan `source` dan `page` atau chunk ID terikat manifest, bukan nomor halaman saja.
- [ ] Perbaiki label yang terbukti kurang lengkap dengan alasan dan bukti; hitung ulang baseline terhadap label yang sama sebelum membandingkan kandidat.
- [ ] Tambahkan pertanyaan regresi Indonesia–Inggris untuk skor, bagian tes, speaking, writing, dan modul CFLT.
- [ ] Siapkan set holdout kecil yang diverifikasi manusia dan tidak dipakai memilih parameter. Jika belum tersedia, nyatakan evaluasi masih pada development set.

### 6.2 Eksperimen bertahap

| ID | Eksperimen | Variabel utama | Catatan |
|---|---|---|---|
| R0 | Baseline aktual | Tidak ada perubahan | Acuan hasil sebelum optimasi. |
| R1 | Embedding multibahasa | Model embedding | Kandidat awal yang dapat diuji: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`; periksa ketersediaan dan kompatibilitas sebelum digunakan. Indeks terpisah wajib. |
| R2 | Query bilingual/translation | Pemrosesan query | Alternatif jika R1 tidak mencukupi; terjemahan tidak boleh menambah fakta. Jika memakai API, catat biaya dan latency tahap ini. |
| R3 | Chunk berbatas kalimat/paragraf | Strategi chunk | Dilakukan hanya setelah efek embedding/query dipahami; dokumentasikan panjang dan overlap aktual. |
| R4 | Hybrid search atau reranking | Strategi ranking | Opsional bila kandidat sebelumnya belum cukup; bukan syarat implementasi awal. |

Jalankan top-k 5 yang sama terlebih dahulu. Bandingkan top-k 3 sesudah kandidat utama dipilih. Threshold perlu dikalibrasi per model; nilai jarak dari model berbeda tidak langsung dapat dibandingkan.

### Metrik dan bukti

- Hit@5, memakai definisi Recall@5 proyek, dengan label sumber-halaman.
- Precision@5 sebagai proxy berbasis label yang sudah diaudit; jelaskan bahwa ini bukan penilaian relevansi semantik seluruh chunk.
- Jumlah query berhasil dan gagal, bukan persentase saja.
- Contoh konteks yang membaik, memburuk, dan tetap gagal.
- Latency retrieval cold/warm, ukuran indeks, serta biaya tambahan jika ada.
- Hasil dipisahkan per bahasa/sumber jika jumlah sampel memungkinkan; jangan menyebut perubahan signifikan secara statistik tanpa analisis memadai.

### Kriteria selesai

- [ ] Pertanyaan empat bagian TOEFL dalam bahasa Indonesia mengambil bukti skor/bagian yang benar.
- [ ] Kandidat terpilih mengungguli baseline pada dataset berlabel identik dan tidak merusak skenario inti Inggris.
- [ ] Target internal **Hit@5 minimal 0,70** pada development set yang diaudit. Target ini bukan kewajiban PRD atau hasil yang sudah dicapai; jika belum tercapai, tulis gap dan lanjutkan perbaikan tanpa memanipulasi label.
- [ ] Seluruh keputusan pemilihan kandidat tercatat, termasuk eksperimen yang gagal.

**Berkas sasaran:** `src/embeddings.py`, `src/retriever.py`, `src/ingestion.py`, `evaluation/`, dan test retrieval.

## 7. Tahap 3 — Rapikan sitasi, grounding, dan penanganan error

**Prioritas:** P0 untuk sitasi dan error; P1 untuk penyempurnaan UX.  
**Estimasi:** 3–5 jam kerja aktif.

### 7.1 Kontrak sitasi

- [ ] Tetapkan satu format keluaran, misalnya `[eBook_TOEFL_Official_Guide_4e.pdf, Halaman 35]`.
- [ ] Parser menghasilkan pasangan sumber-halaman, bukan integer halaman saja.
- [ ] Normalisasi spasi Unicode dan tanda kurung alternatif yang benar-benar muncul pada output model.
- [ ] Jangan menebak sumber untuk sitasi halaman tunggal bila ada lebih dari satu kemungkinan.
- [ ] Periksa apakah sitasi merujuk ke konteks retrieval aktual; tandai sitasi tidak valid secara eksplisit.
- [ ] Bedakan validitas lokasi sitasi dari dukungan faktual terhadap klaim. Dukungan klaim tetap membutuhkan pemeriksaan tersendiri.
- [ ] Tambahkan test sitasi bernama dokumen, `[Page X]`, tanda kurung Unicode, halaman tidak ada, sumber salah, dan klaim tanpa sitasi.

### 7.2 Grounding dan percakapan

- [ ] Tegaskan dokumen adalah bukti, bukan instruksi baru bagi sistem.
- [ ] Pertahankan label soal buatan AI dan peringatan edisi 2012.
- [ ] Batasi reproduksi teks panjang; berikan ringkasan dan rujukan sebagai alternatif.
- [ ] Pisahkan sapaan dari pertanyaan faktual agar sapaan tidak bergantung pada keberhasilan retrieval.
- [ ] Uji follow-up seperti “jelaskan bagian kedua tadi”. Jika perlu, buat query mandiri dari riwayat tanpa mengubah pertanyaan asli dalam log.
- [ ] Pastikan penolakan karena konteks kurang tidak menyatakan bahwa materi pasti tidak ada di seluruh buku.

### 7.3 Error dan UX minimum

- [ ] Bungkus retrieval dan generation dengan penanganan error yang dapat ditindaklanjuti.
- [ ] Bedakan API key tidak tersedia, model tidak tersedia, timeout, rate limit, indeks kosong, dan mismatch embedding.
- [ ] Sanitasi error menggunakan key aktif; jangan tampilkan exception mentah atau stack trace ke pengguna.
- [ ] Ganti label sumber menjadi “konteks yang diambil” bila belum diketahui chunk mana yang mendukung jawaban.
- [ ] Jelaskan bahwa nomor halaman adalah indeks PDF 1-based dan distance bukan probabilitas kebenaran.
- [ ] Jadikan daftar dokumen pada UI berasal dari indeks aktif, bukan teks statis.

**Berkas sasaran:** `src/prompts.py`, `src/generator.py`, `src/evaluation.py`, `app.py`, dan test sitasi/UI.

**Kriteria selesai:** contoh sitasi aktual dapat diparse, sumber ambigu tidak dinilai benar otomatis, error umum tidak memunculkan detail sensitif, dan kontrol UI tetap berjalan.

## 8. Tahap 4 — Evaluasi end-to-end dan penilaian manusia

**Prioritas:** P0 untuk bukti generation; P1 untuk penyempurnaan analisis.  
**Estimasi:** 3–6 jam kerja aktif, ditambah waktu API dan pemeriksaan manusia.  
**Dependensi:** konfigurasi, retrieval, dan sitasi sudah stabil.

### 8.1 Perbaikan pipeline metrik

- [ ] Simpan status per item: sukses, gagal retrieval, gagal generation, dan belum dinilai.
- [ ] Simpan model efektif, konteks yang diperlukan untuk audit lokal, sitasi hasil parser, error tersanitasi, serta waktu tiap tahap.
- [ ] Pisahkan latency retrieval, generation, dan end-to-end; catat cold start dan ringkas rata-rata/median serta p95 dengan jumlah sampelnya.
- [ ] Hitung citation accuracy micro sesuai total sitasi yang diperiksa; jika macro juga disajikan, beri label terpisah.
- [ ] Laporkan citation coverage agar jawaban tanpa sitasi tidak menghilang dari penilaian.
- [ ] Laporkan tingkat keberhasilan API serta denominator setiap metrik. Hasil kosong bukan otomatis kegagalan OOS ataupun nilai kualitas nol tanpa keterangan.
- [ ] Jangan menyatakan OOS berhasil hanya karena ada frasa “tidak ditemukan”. Periksa apakah jawaban juga mengarang fakta.
- [ ] Simpan hash/version konteks; snapshot yang berisi kutipan dokumen disimpan lokal dan ditinjau sebelum distribusi.

### 8.2 Rubrik manusia

| Metrik | Aturan penilaian yang direncanakan |
|---|---|
| Answer correctness | `CORRECT`, `PARTIALLY_CORRECT`, `INCORRECT`, `NOT_RATED`. Metrik utama = jumlah `CORRECT` / jumlah jawaban yang dinilai; kategori parsial dilaporkan terpisah. |
| Groundedness | Pecah jawaban menjadi klaim faktual; tandai didukung/tidak didukung/tidak dapat dinilai dari konteks. Rasio dukungan dihitung dengan denominator eksplisit. Jawaban tanpa klaim diberi N/A, bukan otomatis 100%. |
| OOS handling | Berhasil bila mengakui keterbatasan sumber dan tidak memberikan fakta spesifik yang tidak didukung. |
| Sitasi | Bedakan format terbaca, lokasi ada dalam konteks, dan isi halaman benar-benar mendukung klaim. |

- [ ] Nilai seluruh jawaban in-scope pada baseline final dan seluruh lima OOS.
- [ ] Catat penilai, tanggal, alasan skor, dan bukti konteks.
- [ ] Jika ada penilai kedua, gunakan subset untuk memeriksa konsistensi dan catat cara menyelesaikan perbedaan.

### 8.3 Pelaksanaan run

- [ ] Jalankan preflight satu pertanyaan dan pastikan jawaban tidak kosong sebelum batch.
- [ ] Tentukan budget API; dua konfigurasi dengan 30 pertanyaan berarti sekitar 60 generation request, belum termasuk retry/preflight.
- [ ] Jalankan baseline top-k 5 dan variasi top-k 3 dengan dataset, prompt, model, dan indeks yang sama.
- [ ] Simpan checkpoint per pertanyaan dan dukung resume agar gangguan API tidak mengulang semua request.
- [ ] Jika API gagal, tandai evaluasi parsial dan jangan membuat angka generation fiktif.
- [ ] Analisis tiga contoh nyata: berhasil, kurang tepat, dan OOS.

**Kriteria selesai:** run baru memiliki status lengkap untuk 30 item, kegagalan API ditindaklanjuti atau diungkapkan, penilaian manusia tercatat, dan seluruh angka laporan dapat ditelusuri ke data run. Jangan melabeli evaluasi lengkap jika masih ada generation gagal yang belum dijelaskan.

## 9. Tahap 5 — Dokumentasi, pengujian akhir, dan pengumpulan

**Prioritas:** P1  
**Estimasi:** 2–4 jam kerja aktif, di luar rekaman video.  
**Dependensi:** hasil Tahap 4 tersedia.

- [ ] Sinkronkan README, `.env.example`, generator PDF, outline demo, dan panduan presentasi dengan konfigurasi efektif.
- [ ] Hapus klaim “satu dokumen”, “sub-detik”, atau generation teruji yang tidak sesuai bukti.
- [ ] Tegaskan embedding berlangsung lokal, tetapi chunk retrieval dikirim ke Groq untuk generation.
- [ ] Generator laporan menentukan status dari keberhasilan run, bukan sekadar keberadaan JSON.
- [ ] Bangun PDF baru dari hasil baru; jangan menimpa laporan lama sebelum isi baru diperiksa.
- [ ] Pin versi dependensi yang terbukti berjalan atau sediakan lock file; uji instalasi di virtual environment Windows yang bersih.
- [ ] Jalankan seluruh unit test serta AppTest untuk pertanyaan Indonesia, Inggris, OOS, multi-dokumen, ganti kontrol, dan hapus chat.
- [ ] Lakukan pemeriksaan visual browser desktop/mobile; bila alat otomatis tidak tersedia, catat hasil pemeriksaan manual pengguna.
- [ ] Rekam video maksimal lima menit, termasuk satu keterbatasan nyata dan bukti sumber.
- [ ] Periksa paket pengumpulan: tidak ada `.env`, key, indeks privat, PDF sumber berhak cipta, atau snapshot kutipan berlebihan.

**Kriteria selesai:** dokumentasi dapat diikuti pada instalasi bersih, PDF konsisten dengan hasil run, demo tersedia, dan paket pengumpulan tidak menyertakan materi yang seharusnya privat.

## 10. Rencana artefak

Nama berikut adalah usulan; folder/file belum dibuat oleh dokumen planning ini.

```text
evaluation/
|-- test_questions.json                 # Dataset historis, dipertahankan
|-- test_questions_v2.json              # Label sumber-halaman dan audit verifikasi
|-- human_review_v2.csv                 # Penilaian dan catatan manusia
`-- runs/
    |-- <run_id>_retrieval.json
    |-- <run_id>_results.json
    |-- <run_id>_results.csv
    `-- <run_id>_summary.md

reports/
|-- methodology_evaluation_v2.pdf
`-- demo_outline.md

tests/
|-- test_config.py
|-- test_ingestion_safety.py
|-- test_evaluation_pipeline.py
`-- test_app.py
```

Manifest/snapshot indeks disimpan di area lokal yang sesuai dan tidak berisi kredensial. Snapshot konteks berhak cipta tidak otomatis menjadi bagian paket publik.

## 11. Estimasi dan strategi bila waktu terbatas

Total perkiraan **16–30 jam kerja aktif**, tidak termasuk antrean API, unduhan besar, rekaman, dan koordinasi penilai. Estimasi bukan janji durasi; evaluasi awal dapat mengubah kebutuhan pekerjaan.

### Paket minimum sebelum presentasi

1. Satukan model efektif dan format sitasi.
2. Perbaiki retrieval pertanyaan Indonesia inti berdasarkan eksperimen terukur.
3. Jalankan evaluasi generation baru dan nilai jawabannya secara manual.
4. Sinkronkan PDF serta naskah dengan hasil aktual.
5. Selesaikan smoke test dan video.

Jika hanya tersedia satu hari, tunda hybrid search, reranker, pembuka PDF, dan penyempurnaan visual. **Jangan** mengorbankan keamanan indeks ketika rebuild, kejujuran hasil, atau pencatatan kegagalan untuk mengejar tampilan selesai.

## 12. Definition of Done

- [ ] Baseline dan hasil historis tetap tersedia.
- [ ] Indeks aktif aman saat build kandidat gagal.
- [ ] UI, generator, dan evaluasi menggunakan konfigurasi efektif yang konsisten.
- [ ] Pertanyaan inti Indonesia dan Inggris memiliki bukti retrieval yang benar.
- [ ] Target retrieval tercapai atau gap dinyatakan eksplisit; label tidak dimanipulasi.
- [ ] Sitasi memuat sumber-halaman dan dapat diverifikasi terhadap konteks.
- [ ] Evaluasi end-to-end 30 item memiliki hasil serta status kegagalan yang dapat diaudit.
- [ ] Correctness, groundedness, dan OOS dinilai dengan rubrik dan jumlah sampel jelas.
- [ ] Unit test, test integrasi terkontrol, dan smoke test UI lulus; kendala tersisa didokumentasikan.
- [ ] Instalasi Windows bersih berhasil mengikuti README.
- [ ] PDF dan demo maksimal lima menit memakai hasil aktual.
- [ ] Tidak ada rahasia atau PDF sumber privat dalam paket pengumpulan.

**Keputusan akhir:** rilis sebagai MVP tervalidasi hanya setelah bukti memenuhi kriteria penerimaan PRD. Jika masih ada blocker, gunakan label “prototipe / evaluasi parsial” beserta batasannya, bukan klaim selesai penuh.
