# 🎤 PANDUAN PRESENTASI & DEMO: TOEFL MATE RAG STUDY ASSISTANT

Dokumen ini adalah ringkasan skenario dan poin-poin penting yang harus dijelaskan saat **presentasi atau rekaman video demonstrasi UTS (Maksimal 5 Menit)** untuk mata kuliah *Introduction to Generative AI*.

---

## 📌 Ringkasan Eksekutif Proyek
- **Nama Proyek:** TOEFL Mate — RAG Study Assistant
- **Fungsi Utama:** Chatbot pembelajaran TOEFL berbasis Retrieval-Augmented Generation (RAG) yang menjawab pertanyaan berdasarkan buku resmi ETS dengan menyertakan sitasi halaman, cuplikan sumber, dan guardrail anti-halusinasi (*grounded generation*).
- **Dokumen Sumber:** *The Official Guide to the TOEFL Test, 4th Edition* (ETS, 2012) — 668 Halaman PDF.
- **Prinsip Utama UTS:** Sistem berjalan nyata (*end-to-end*), evaluasi empiris jujur tanpa data rekayasa, dan batasan dokumen dijelaskan secara transparan.

---

## ⏱️ Alur & Naskah Demo (5 Menit)

```
[0:00 - 0:45] Pembukaan & Latar Belakang
      │
[0:45 - 1:45] Arsitektur Sistem & Pipeline RAG
      │
[1:45 - 3:30] Live Demo Antarmuka Web (Streamlit UI)
      │       ├── Skenario 1: Pertanyaan Faktual & Verifikasi Sitasi Halaman
      │       ├── Skenario 2: Pertanyaan Konseptual & Strategi
      │       ├── Skenario 3: Pertanyaan Out-of-Scope (Anti-Halusinasi)
      │       └── Skenario 4: Kontrol SOP Sidebar & Ganti Bahasa
      │
[3:30 - 4:30] Hasil Evaluasi Eksperimental (top_k=5 vs top_k=3)
      │
[4:30 - 5:00] Keterbatasan, Etika, & Penutup
```

---

### Bagian 1: Pembukaan & Latar Belakang (0:00 - 0:45)
**Yang Ditampilkan:** Slide Judul / Tampilan Awal Streamlit  
**Poin yang Harus Diucapkan:**
> *"Selamat pagi/siang Bapak/Ibu dosen dan rekan-rekan sekalian. Saya mempersembahkan TOEFL Mate, asisten belajar TOEFL berbasis Retrieval-Augmented Generation (RAG). Masalah yang sering dihadapi pelajar TOEFL adalah tebalnya buku panduan resmi ETS yang mencapai lebih dari 650 halaman. TOEFL Mate hadir untuk membantu navigasi materi, format tes, dan strategi pengerjaan dengan jawaban yang terbukti berakar pada dokumen resmi disertai rujukan halaman yang akurat."*

---

### Bagian 2: Arsitektur & Teknologi Sistem (0:45 - 1:45)
**Yang Ditampilkan:** Diagram Arsitektur / Terminal Ingestion  
**Poin yang Harus Diucapkan:**
> *"Arsitektur sistem dibangun dari ujung ke ujung tanpa mockup:*
> 1. *Ekstraksi PDF:* Menggunakan PyMuPDF dengan nomor halaman 1-based yang konsisten serta normalisasi Unicode untuk mengurai karakter ligatur.
> 2. *Chunking & Embedding:* Teks dibagi menjadi 3.911 chunk (ukuran 500 karakter, overlap 100 karakter). Embedding dilakukan 100% lokal di CPU menggunakan model `all-MiniLM-L6-v2` (384 dimensi), sehingga isi buku tidak perlu dikirim ke server pihak ketiga.
> 3. *Vector Store:* ChromaDB persisten dengan indeks jarak kemiripan L2.
> 4. *Generasi LLM:* Menggunakan Groq API dengan waktu inferensi sub-detik, dikawal oleh System of Prompts (SOP) ketat yang melarang halusinasi dan mewajibkan sitasi `[Halaman X]`.*"

---

### Bagian 3: Live Demo Antarmuka Web (1:45 - 3:30)
**Yang Ditampilkan:** Browser `http://localhost:8501` (Streamlit)

#### Skenario A: Pertanyaan Faktual & Verifikasi Sitasi
- **Prompt yang Diketik:**
  ```text
  Apa saja 4 bagian tes TOEFL iBT dan berapa rentang skornya?
  ```
- **Hal yang Ditunjukkan ke Penonton:**
  - Kecepatan respons (⏱️ ~1.7 detik).
  - Kelengkapan jawaban: Reading (0-30), Listening (0-30), Speaking (0-30), Writing (0-30), Total (0-120).
  - **Sitasi Halaman:** Tunjukkan `[Halaman 18]` dan `[Halaman 35]`.
  - **Expander "📚 Sumber yang digunakan":** Buka dropdown untuk membuktikan 5 potongan teks asli yang diambil dari ChromaDB beserta nilai jarak L2-nya.

#### Skenario B: Pertanyaan Konseptual / Sintesis
- **Prompt yang Diketik:**
  ```text
  Apa perbedaan antara tugas Independent Speaking dan Integrated Speaking?
  ```
- **Hal yang Ditunjukkan ke Penonton:**
  - Penjelasan bertahap yang mensintesis bab Speaking: Independent (Question 1-2 berbasis pendapat pribadi) vs Integrated (Question 3-6 memadukan teks bacaan, audio kuliah, dan berbicara).

#### Skenario C: Pertanyaan Out-of-Scope (Uji Guardrail Anti-Halusinasi)
- **Prompt yang Diketik:**
  ```text
  Berapa biaya pendaftaran tes TOEFL tahun 2025 di Jakarta dalam Rupiah?
  ```
- **Respon Sistem:**
  ```text
  Informasi ini tidak ditemukan dalam dokumen sumber yang tersedia.
  ```
- **Poin yang Ditekankan:**
  > *"Sistem tidak berhalusinasi atau mengarang biaya. Karena dokumen sumber adalah buku terbitan 2012, sistem mematuhi aturan SOP untuk menolak menjawab pertanyaan di luar dokumen."*

#### Skenario D: Fitur Sidebar (SOP Controls)
- Tunjukkan fitur sidebar:
  - Ganti **Bahasa Jawaban** ke *English*.
  - Ganti **Gaya Jawaban** ke *ringkas*.
  - Tunjukkan slider **Jumlah Konteks (top-k)**.
  - Klik tombol **🗑️ Hapus Percakapan** untuk menunjukkan sesi kembali bersih.

---

### Bagian 4: Evaluasi Eksperimental & Temuan Kunci (3:30 - 4:30)
**Yang Ditampilkan:** File `evaluation/results.csv` atau Laporan PDF Metodologi  
**Poin yang Harus Diucapkan:**
> *"Untuk memenuhi persyaratan UTS yang terukur, kami membangun dataset 30 pertanyaan berlabel terverifikasi (10 faktual, 10 konseptual, 5 sitasi, 5 out-of-scope). Kami melakukan eksperimen perbandingan antara `top_k=5` (baseline) vs `top_k=3`:*
> - *Pada `top_k=5`: Recall@5 mencapai 0.3200 (32%) dan Precision@5 adalah 0.1040.*
> - *Pada `top_k=3`: Recall@3 adalah 0.2400 (24%) dan Precision@3 meningkat menjadi 0.1333.*
> - *Analisis Trade-off:* Meningkatkan top_k dari 3 ke 5 memberikan peningkatan **Recall sebesar +33.3% relatif**, yang sangat penting agar konteks jawaban yang dicari tidak terlewatkan, dengan kompensasi sedikit penurunan presisi."*

---

### Bagian 5: Keterbatasan, Etika, & Penutup (4:30 - 5:00)
**Yang Ditampilkan:** Halaman Laporan PDF / Slide Penutup  
**Poin yang Harus Diucapkan:**
> *"Tiga hal yang kami garis bawahi sebagai batasan dan etika:*
> 1. *Edisi Dokumen:* Buku ini adalah edisi 2012, sehingga beberapa aturan durasi tes telah diperbarui oleh ETS. Kami menyertakan disclaimer di UI dan laporan.
> 2. *Hak Cipta:* Dokumen sumber berhak cipta ETS dan McGraw-Hill, sehingga sistem hanya menggunakan kutipan seperlunya dan tidak mendistribusikan ulang file PDF penuh.
> 3. *Unit Testing:* Seluruh 49 unit test passing 100% di Windows.
> *Demikian presentasi prototipe RAG TOEFL Mate. Terima kasih."*

---

## 📋 Checklist Kesiapan Sebelum Rekam Video Demo
- [ ] Streamlit sudah berjalan di latar belakang (`python -m streamlit run app.py`).
- [ ] Browser sudah terbuka di `http://localhost:8501`.
- [ ] File `.env` sudah terisi dengan `GROQ_API_KEY` aktif.
- [ ] Tab kedua browser / PDF viewer sudah membuka [`reports/methodology_evaluation.pdf`](file:///d:/001%20Road%20to%20M%20KOM/SEMESTER%201/Introduction%20to%20Generative%20AI/UTS%20TOEFL%20Mate%20RAG%20Study%20Assistant/reports/methodology_evaluation.pdf).
- [ ] Audio mikrofon jernih dan resolusi layar diatur minimal 1080p (Full HD).

