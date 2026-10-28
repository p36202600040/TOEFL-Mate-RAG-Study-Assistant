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
- Jalankan `python scripts/evaluate.py`
- Tunjukkan output: metrik Recall@5, Precision@5, Citation Accuracy, OOS Handling, Latency
- Buka `evaluation/results.json` dan tunjukkan detail
- Jalankan `python scripts/build_report.py`
- Buka PDF laporan

### 4:15–4:45 — Unit Tests
- Jalankan `pytest tests/ -v`
- Tunjukkan semua test pass
- Jelaskan cakupan test: ingestion, retrieval, citations

### 4:45–5:00 — Penutup
- Ringkasan: pipeline RAG end-to-end yang berjalan
- Keterbatasan: edisi 2012, penilaian manual belum lengkap
- Terima kasih

---

## Catatan untuk Perekam
- Pastikan `.env` sudah berisi `GROQ_API_KEY` yang valid
- Pastikan ingestion sudah dijalankan sebelumnya (atau rekam dari awal)
- Gunakan resolusi layar yang cukup besar agar teks terbaca
- Jangan tampilkan API key di layar
- Jika ada error, jelaskan dan perbaiki — jujur lebih baik daripada sempurna

