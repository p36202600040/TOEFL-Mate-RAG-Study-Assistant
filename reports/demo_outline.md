# 🎬 Demo Outline — TOEFL Mate: RAG Study Assistant

**Durasi target:** Maksimal 5 menit  
**Format:** Screen recording dengan narasi

---

## Timestamp dan Alur Demo

### 0:00–0:30 — Pembukaan
- Perkenalan: "TOEFL Mate — RAG Study Assistant"
- Tujuan: Chatbot belajar TOEFL berbasis RAG dari buku resmi ETS
- Tampilkan README dan struktur proyek

### 0:30–1:00 — Arsitektur & Stack
- Jelaskan alur pipeline: PDF → Chunking → Embedding → ChromaDB → Retrieval → Groq → Jawaban
- Tampilkan diagram arsitektur sederhana
- Sebutkan stack: Python, Streamlit, PyMuPDF, Sentence Transformers, ChromaDB, Groq

### 1:00–1:30 — Ingestion PDF
- Jalankan `python scripts/ingest_pdf.py`
- Tunjukkan output: jumlah halaman, jumlah chunks, waktu proses
- Jelaskan: chunk size, overlap, metadata halaman

### 1:30–3:00 — Demo Chatbot (Streamlit UI)
- Jalankan `streamlit run app.py`
- **Pertanyaan faktual:** "Apa saja bagian utama tes TOEFL iBT?"
  - Tunjukkan jawaban dengan sitasi halaman
  - Buka expander "Sumber yang digunakan"
- **Pertanyaan konseptual:** "Bagaimana strategi menjawab soal Reading?"
  - Tunjukkan penjelasan bertahap
- **Pertanyaan out-of-scope:** "Berapa biaya tes TOEFL tahun 2024?"
  - Tunjukkan bahwa sistem mengakui keterbatasan
- **Ubah pengaturan:**
  - Ganti bahasa ke English
  - Ganti gaya ke ringkas
  - Tunjukkan perbedaan jawaban
- **Hapus percakapan:** klik tombol "Hapus Percakapan"

### 3:00–3:30 — Pengaturan SOP
- Tunjukkan sidebar pengaturan: bahasa, gaya, tingkat
- Jelaskan aturan grounding di system prompt

### 3:30–4:15 — Evaluasi
- Tunjukkan `evaluation/results_v2_k5.json` dan `evaluation/results_v2_k3.json`, bukan hasil historis yang kosong.
- Jelaskan definisi Recall@K proyek sebagai Hit@K: setidaknya satu halaman target ada di top-k.
- Tunjukkan angka aktual V2: top-k 5 Hit@5 0,5600 dan Precision@5 0,1920; top-k 3 Hit@3 0,4400 dan Precision@3 0,2000.
- Jelaskan secara jujur bahwa run top-k 5 memiliki satu rate-limit, sedangkan top-k 3 memiliki 30 generation berhasil.
- Tunjukkan bahwa correctness dan groundedness masih membutuhkan review manusia melalui `evaluation/human_review_template.csv`.
- Buka `reports/methodology_evaluation_v2.pdf`; sebutkan status evaluasi parsial, bukan mengklaim hasil final.

### 4:15–4:45 — Unit Tests
- Jalankan `pytest tests/ -v`
- Tunjukkan semua test pass
- Jelaskan cakupan test: ingestion, retrieval, citations

### 4:45–5:00 — Penutup
- Ringkasan: pipeline RAG end-to-end yang berjalan
- Keterbatasan: edisi 2012, Hit@5 belum mencapai target internal 0,70, dan penilaian manusia belum lengkap
- Terima kasih

---

## Catatan untuk Perekam
- Pastikan `.env` sudah berisi `GROQ_API_KEY` yang valid
- Pastikan ingestion sudah dijalankan sebelumnya (atau rekam dari awal)
- Gunakan resolusi layar yang cukup besar agar teks terbaca
- Jangan tampilkan API key di layar
- Jika ada error, jelaskan dan perbaiki — jujur lebih baik daripada sempurna
