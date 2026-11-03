"""Bangun laporan final UTS dari artefak V2; tidak menjalankan ulang API."""
import hashlib
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak

ROOT = Path(__file__).resolve().parent.parent


def build():
    target = ROOT / "reports/methodology_evaluation_final_uts_20261103"
    pdf = target.with_suffix(".pdf")
    md = target.with_suffix(".md")
    if pdf.exists() or md.exists():
        raise FileExistsError("Output final sudah ada; tidak ditimpa.")
    paths = [ROOT / f"evaluation/results_v2_k{k}.json" for k in (5, 3)]
    runs = [json.loads(p.read_text(encoding="utf-8")) for p in paths]
    dataset = ROOT / "evaluation/test_questions.json"
    questions = json.loads(dataset.read_text(encoding="utf-8"))
    def metric(run, key):
        return run["metrics"][key]["value"]
    def row(label, key):
        return f"- {label}: k=5 {metric(runs[0], key):.4f}; k=3 {metric(runs[1], key):.4f}."
    fingerprints = "\n".join(
        f"- {p.relative_to(ROOT).as_posix()} | SHA-256: {hashlib.sha256(p.read_bytes()).hexdigest()}"
        for p in [dataset, *paths]
    )
    text = f"""# TOEFL Mate: RAG Study Assistant
## Laporan final metodologi evaluasi dan hasil UTS
Tanggal penyusunan: 3 November 2026
Mata kuliah: Intro Generative AI | Dosen: Dr. Farrikh Alzami, M.Kom.
Status dokumen: laporan final untuk artefak yang tersedia; evaluasi kualitas jawaban belum tervalidasi manusia secara menyeluruh.

## Ringkasan eksekutif
TOEFL Mate merupakan prototipe asisten belajar berbasis Retrieval-Augmented Generation (RAG). Sistem mengekstrak PDF, membentuk chunk dan embedding lokal, melakukan pencarian di ChromaDB, lalu meminta model melalui Groq menyusun jawaban berdasarkan konteks. Streamlit menyediakan antarmuka chat, pengaturan respons, sitasi, dan cuplikan konteks.
Laporan ini menyajikan dua eksperimen historis tanggal 30 Oktober 2026 pada 30 pertanyaan: top-k 5 dan top-k 3. Run k=5 menghasilkan 29 jawaban dan satu kegagalan rate-limit; run k=3 menghasilkan 30 jawaban. Nilai Hit@5 adalah 0,5600 dan Hit@3 adalah 0,4400. Angka tersebut memakai label halaman historis, bukan label sumber-halaman yang telah diverifikasi.
Pengujian kode diulang pada sesi penyusunan laporan dan menghasilkan 67 test lulus, satu warning. Tidak dilakukan pemanggilan API, pembangunan ulang indeks, re-scoring source-aware, atau penilaian manusia baru untuk menghasilkan laporan ini.
Kesimpulan: pipeline dan evaluasi otomatis telah diimplementasikan, tetapi angka retrieval dan indikator sitasi tidak membuktikan correctness atau groundedness. Istilah final merujuk pada konsistensi laporan, bukan validasi produk yang telah selesai.

## 1. Tujuan dan pertanyaan evaluasi
- Menilai apakah konteks yang diambil memuat halaman yang dilabeli relevan.
- Membandingkan hasil historis konfigurasi top-k 5 dan 3, tanpa menyimpulkan sebab-akibat atau signifikansi statistik.
- Mengamati keberadaan sitasi, kecocokan halaman label, indikator penolakan pertanyaan di luar cakupan, dan latency.
- Mengidentifikasi kebutuhan review manusia untuk correctness, dukungan klaim, serta relevansi respons penolakan.
---PAGE---
## 2. Data, arsitektur, dan konfigurasi eksperimen
Dokumen utama yang dinyatakan dalam proyek adalah The Official Guide to the TOEFL Test, Fourth Edition (ETS, 2012). Nomor halaman evaluasi mengacu pada urutan halaman PDF 1-based, bukan otomatis nomor cetak buku. Edisi lama tidak boleh dianggap sebagai informasi kebijakan TOEFL terkini. Isi koleksi aktual dan provenance indeks tetap perlu diaudit; laporan tidak menegaskan bahwa semua isi indeks telah diverifikasi.
Alur ingestion: PDF -> PyMuPDF -> normalisasi teks per halaman -> chunking -> Sentence Transformers -> penyimpanan vektor dan metadata di ChromaDB.
Alur pertanyaan: input -> embedding query -> pencarian konteks -> penyusunan prompt -> Groq -> jawaban dan sitasi. Konteks yang ditemukan bukan dengan sendirinya bukti bahwa setiap klaim jawaban benar.
Konfigurasi berikut diambil dari metadata run V2, bukan dari environment saat laporan dibuat:
- Embedding: all-MiniLM-L6-v2.
- Model generasi: openai/gpt-oss-120b melalui Groq.
- Ukuran chunk: 500 karakter; overlap: 100 karakter.
- Top-k: 5 dan 3; relevance threshold: 1,5; vector store proyek menggunakan jarak L2.
- Dataset version: historical_test_questions; prompt version: canonical-source-page-citations-v2.
- Run k=5: {runs[0]['config']['run_id']} | {runs[0]['config']['timestamp']}.
- Run k=3: {runs[1]['config']['run_id']} | {runs[1]['config']['timestamp']}.
Threshold jarak bukan probabilitas benar. Metadata run lama belum cukup untuk memverifikasi dimensi/provenance indeks, fingerprint prompt aktual, seluruh parameter generasi, ataupun kesetaraan lingkungan kedua run. Karena itu reproduksi persis tidak dijamin.

## 3. Dataset dan prosedur
Dataset tersimpan memuat {len(questions)} pertanyaan: 10 factual, 10 conceptual, 5 retrieval_citation, dan 5 out_of_scope. Sebanyak 25 pertanyaan in-scope menjadi denominator metrik retrieval historis dan coverage; lima OOS menjadi denominator indikator frasa penolakan.
Setiap item memuat ID, kategori, pertanyaan, reference_answer, relevant_pages, dan evaluator_notes. Catatan label adalah dokumentasi penyusunan, bukan bukti bahwa audit sumber independen sudah dilakukan. Label historis tidak menentukan nama sumber sehingga tidak memadai untuk evaluasi source-aware.
Prosedur eksperimen historis: jalankan dataset pada masing-masing k, simpan halaman/chunk/jarak hasil retrieval, jawaban, sitasi, latency, dan status tiap item, lalu agregasikan metrik. Tidak ada pengulangan multi-seed, interval kepercayaan, atau uji statistik yang dilaporkan. Dua run ini bukan benchmark umum semua pertanyaan TOEFL.
---PAGE---
## 4. Definisi metrik dan denominator
Hit@k historis: nilai 1 jika setidaknya satu halaman hasil top-k ada pada relevant_pages, selain itu 0; dirata-rata atas 25 item berlabel. Artefak memakai nama recall_at_k, tetapi definisinya query-level hit, bukan recall fraksi seluruh dokumen relevan.
Precision@k historis: jumlah chunk top-k yang halamannya cocok dengan label dibagi k, kemudian dirata-rata atas 25 item. Chunk pada halaman yang sama dapat terhitung berulang; ini bukan precision atas halaman unik. Hasil kurang dari k tetap menggunakan denominator k.
Kecocokan sitasi dengan label halaman (historical citation_accuracy_micro): jumlah kemunculan sitasi dengan halaman yang cocok label dibagi seluruh kemunculan sitasi yang masuk agregasi. Ini tidak memeriksa kebenaran klaim, tidak memverifikasi sumber label, dan tidak layak disebut akurasi faktual sitasi.
Coverage sitasi historis: jawaban in-scope yang memiliki minimal satu sitasi terbaca dibagi 25 pertanyaan in-scope. Pada k=5 denominator tersebut termasuk satu generation gagal. Definisi evaluator terbaru berbeda: memakai jawaban in-scope yang berhasil. Angka lama tidak dikonversi diam-diam ke definisi baru.
Indikator frasa OOS historis: proporsi lima jawaban OOS yang memuat salah satu frasa pengakuan keterbatasan. Walaupun key artefak bernama out_of_scope_handling, hasil ini bukan akurasi OOS; jawaban dapat memuat frasa penolakan sekaligus mengarang informasi.
Validitas lokasi sitasi: memeriksa apakah pasangan sumber-halaman ada pada konteks retrieval. Ini terpisah dari kecocokan label dan terpisah lagi dari dukungan isi sumber terhadap klaim.
Latency: retrieval dirata-rata atas 30 item; generation dan end-to-end hanya atas jawaban berhasil (29 untuk k=5, 30 untuk k=3). End-to-end yang direkam tidak dianggap sama dengan penjumlahan dua rata-rata komponen karena dapat mencakup overhead dan denominator berbeda. Pengukuran lokal bukan SLA server VPS.
Correctness dan groundedness: belum dinilai manusia. Tidak diberikan skor numerik, dan tidak digantikan dengan metrik sitasi atau jumlah test.

## 5. Perubahan evaluator setelah run historis
Evaluator terbaru menerima relevant_sources berupa pasangan source dan page. Label lama relevant_pages diberi SOURCE_UNKNOWN dan tidak dihitung dalam agregasi source-aware. Retrieval yang gagal juga dikecualikan; jumlah item yang memenuhi syarat harus dilaporkan agar kegagalan tidak tersamarkan.
Tidak ada hasil run source-aware baru dalam laporan ini. Perbaikan evaluator, parser sitasi, sanitasi error, dan pemeriksaan manifest tidak secara retroaktif memperbaiki jawaban atau angka V2.
---PAGE---
## 6. Hasil eksperimen historis
Semua nilai berikut disalin dari metrics pada dua JSON V2, tanpa re-scoring.
{row('Hit@k; n=25 per run', 'recall_at_k')}
{row('Precision@k; n=25 per run', 'precision_at_k')}
{row('Kecocokan sitasi-label halaman; denominator 40 dan 37 sitasi', 'citation_accuracy_micro')}
{row('Coverage sitasi historis; denominator 25 per run', 'citation_coverage')}
{row('Indikator frasa OOS; denominator 5 per run', 'out_of_scope_handling')}
{row('Rata-rata retrieval dalam detik; n=30 per run', 'avg_retrieval_latency_seconds')}
{row('Rata-rata generation dalam detik; n=29 dan 30', 'avg_generation_latency_seconds')}
{row('Rata-rata end-to-end dalam detik; n=29 dan 30', 'avg_end_to_end_latency_seconds')}
Generation berhasil: k=5 sebanyak 29/30; k=3 sebanyak 30/30. Item concept_01 pada k=5 gagal dengan HTTP 429 (rate-limit). Pesan mentah penyedia tidak direproduksi karena dapat mengandung metadata akun. Kegagalan API bukan jawaban yang salah secara semantik, tetapi tetap merupakan kegagalan layanan pada run tersebut.

## 7. Interpretasi hasil
Hit@5 setara 14 dari 25 pertanyaan menemukan minimal satu halaman label; Hit@3 setara 11 dari 25. Secara deskriptif, k=5 memiliki cakupan hit lebih tinggi pada sampel ini, sedangkan precision sedikit lebih rendah (0,1920 dibanding 0,2000). Kedua precision tidak berarti 19,2% atau 20% jawaban benar: unitnya chunk terhadap label halaman.
Rata-rata end-to-end k=5 lebih tinggi daripada k=3 pada dua run tersebut. Tidak dapat dipastikan bahwa k saja penyebabnya karena kondisi API, panjang jawaban, dan stochasticity tidak dikontrol dalam eksperimen berulang. Perbandingan ini belum mengukur kualitas pedagogis maupun dukungan faktual per klaim.
Coverage 0,56/0,52 menunjukkan keberadaan sitasi terbaca, bukan kualitas sitasi. Indikator OOS 0,80/0,60 hanya menunjukkan frasa pengakuan keterbatasan. Tidak ada dasar untuk mengklaim chatbot memiliki akurasi keseluruhan 80%, bebas halusinasi, atau seluruh responsnya grounded.
Target internal Hit@5 0,70 yang tercatat pada outline proyek belum tercapai oleh hasil historis 0,56. Target ini bukan ambang kelulusan dosen yang dinyatakan dalam soal.
---PAGE---
## 8. Analisis kasus dari artefak
Kasus fact_01 pada k=5 menanyakan rentang skor tiap bagian dan skor total. Label historis menunjuk halaman PDF 35. Halaman yang diambil adalah 207, 36, 204, 298, dan 36; sehingga Hit@5 bernilai 0 terhadap label tersebut.
Jawaban mengutip halaman 207 dan 298. Keduanya tercatat berada dalam konteks retrieval, tetapi tidak cocok dengan label 35. Ini memperlihatkan perbedaan validitas lokasi sitasi dan kecocokan label. Jawaban juga menyatakan bahwa total 0-120 tidak dapat dikonfirmasi eksplisit dari cuplikan, lalu memberikan penalaran tentang total teoritis. Kasus ini menunjukkan perlunya review terhadap kelengkapan dan dukungan klaim; bukan bukti kuantitatif groundedness seluruh sistem.
Kasus concept_01 pada k=5 menunjukkan dampak rate-limit pada kelengkapan eksperimen: retrieval dan label dapat tersedia, tetapi generation tidak menghasilkan jawaban berhasil. Karena itu laporan harus menampilkan status per item dan denominator, bukan hanya satu angka agregat.

## 9. Pengujian kode dan iterasi
Perintah yang dijalankan ulang pada sesi penyusunan: python -m pytest tests/ -q.
Hasil: 67 passed, 1 warning, durasi 34,89 detik pada lingkungan lokal. Warning PytestRemovedIn10Warning berasal dari plugin anyio yang menggunakan alias CallSpec2. Hasil ini bukan pengujian beban, audit keamanan, uji deployment, maupun penilaian manusia atas jawaban.
Cakupan test antara lain ekstraksi/chunking, retrieval, parser sitasi, konfigurasi, sanitasi error, keluaran evaluasi, label historis, pasangan sumber-halaman, mismatch manifest, dan klarifikasi ordinal pada AppTest tanpa API.
Iterasi terbaru memisahkan kecocokan label dari lokasi sitasi, mencegah fallback retrieval diam-diam, memeriksa model/dimensi ketika manifest mendukung, serta menjelaskan bahwa cuplikan retrieval bukan bukti klaim. Indeks lama yang manifest-nya tidak lengkap tetap UNKNOWN, bukan dinyatakan kompatibel.

## 10. Rancangan review manusia (belum dilaksanakan untuk laporan ini)
Gunakan pertanyaan, jawaban, reference_answer, konteks retrieval, dan PDF asli. Nilai correctness (0 salah, 1 sebagian benar, 2 benar/lengkap), groundedness per klaim (didukung/tidak didukung/tidak dapat dinilai), serta ketepatan sumber-halaman. Nilai juga relevansi penolakan OOS dan ada tidaknya informasi karangan.
Sebaiknya dua anggota menilai secara independen, mencatat alasan dan halaman bukti, lalu mendiskusikan perbedaan. Nyatakan jumlah sampel aktual, aturan pemilihan, dan penyebut metrik. Ini adalah protokol lanjutan, bukan hasil penilaian yang sudah diperoleh.
---PAGE---
## 11. Keterbatasan dan ancaman validitas
- Dataset kecil, satu domain, serta label historis belum mempunyai sumber terverifikasi. Kecocokan nomor halaman antar dokumen dapat menimbulkan false match.
- Edisi sumber lama; klaim tentang format dan kebijakan TOEFL terbaru memerlukan sumber terkini.
- Chunking berbasis karakter dan ekstraksi tanpa OCR dapat memutus konteks, tabel, atau informasi visual. Retrieval yang kurang tepat membatasi jawaban.
- Tidak ada review manusia lengkap, pengulangan eksperimen, atau estimasi ketidakpastian statistik. Deteksi frasa OOS berpotensi salah positif dan salah negatif.
- Provenance dan fingerprint indeks run historis belum terbukti. Manifest saja bukan bukti bahwa seluruh vektor benar-benar berasal dari model yang disebut.
- Evaluator telah berubah setelah run historis. Angka V2 tidak dapat dibandingkan langsung dengan agregasi source-aware baru.
- Checkpoint/resume evaluasi terverifikasi dan uji concurrency output belum tersedia. Latency lokal tidak mewakili VPS multi-pengguna.

## 12. Kesimpulan dan status pengumpulan
Proyek telah mengimplementasikan pipeline RAG end-to-end dan menjalankan dua eksperimen historis dengan hasil serta kegagalan yang tercatat. Hasil memberikan bukti kemampuan menemukan sebagian halaman relevan dan menyajikan respons, tetapi belum membuktikan kualitas jawaban secara menyeluruh. Kontribusi iterasi terbaru adalah peningkatan integritas evaluasi dan transparansi, bukan kenaikan skor generation yang telah diukur.
Laporan ini menjadi versi rujukan untuk presentasi metodologi dan hasil, menggantikan narasi laporan lama yang tidak konsisten; artefak lama tetap dipertahankan. Untuk demonstrasi, tampilkan source code, alur RAG, satu jawaban beserta konteks, ringkasan hasil, dan keterbatasan. Video maksimal lima menit sesuai soal UTS.
GitHub, VPS aaPanel, dan domain webnyaadam.my.id merupakan rencana distribusi pengguna; publikasi dan keberhasilan deployment belum diverifikasi dalam laporan ini. Jangan menyebut aplikasi sudah online sebelum diuji. Jangan unggah API key, .env, atau materi berhak cipta tanpa izin. Embedding lokal tidak berarti seluruh pemrosesan lokal karena konteks generasi dikirim ke Groq.

## 13. Reproduksi dan artefak rujukan
Jalankan aplikasi dari root proyek: python -m streamlit run app.py. Siapkan dependensi, konfigurasi rahasia, model, dan koleksi yang benar menurut README. Pembangunan koleksi kandidat tidak otomatis mengaktifkannya.
Untuk pengujian kode: python -m pytest tests/ -q. Untuk run evaluasi baru, periksa python scripts/evaluate.py --help, gunakan output baru, catat environment dan provenance indeks, serta siapkan label sumber-halaman yang direview. Run baru bukan reproduksi persis run V2 bila konfigurasi atau evaluator berbeda.
Sumber laporan: README.md; src/evaluation.py; evaluation/test_questions.json; evaluation/results_v2_k5.json; evaluation/results_v2_k3.json; reports/optimasi_integritas_ui.md; reports/demo_outline.md; dan output pytest pada sesi penyusunan. Soal UTS menjadi dasar jenis deliverable, bukan dasar skor kelulusan tertentu.
---PAGE---
## Lampiran A. Identitas artefak
Fingerprint berikut dihitung saat laporan dibuat untuk membantu mendeteksi perubahan berkas. Fingerprint ini bukan bukti kebenaran label maupun provenance indeks historis.
{fingerprints}

## Lampiran B. Panduan membaca laporan saat demo
- Tampilkan tujuan dan diagram alur secara singkat; bedakan ingestion dan runtime.
- Pada bagian hasil, jelaskan bahwa Hit@5 0,56 adalah hit halaman berlabel pada 25 pertanyaan, bukan akurasi jawaban 56%.
- Sebutkan satu generation gagal karena rate-limit pada run k=5.
- Tampilkan contoh fact_01 untuk membedakan sitasi berada di konteks dan klaim benar-benar didukung.
- Jelaskan bahwa 67 test lulus memeriksa perilaku kode, bukan menggantikan evaluasi manusia.
- Tunjukkan source code GitHub dan aplikasi domain hanya setelah URL dan akses publik benar-benar diuji.

## Lampiran C. Pernyataan transparansi
Laporan disusun dengan bantuan asisten AI berdasarkan kode, artefak JSON, dan catatan proyek. Tidak ada skor correctness atau groundedness manusia yang direkayasa. Anggota kelompok tetap bertanggung jawab membaca, memeriksa, dan menjelaskan isi laporan sebelum pengumpulan.
"""
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="FinalTitle", fontName="Helvetica-Bold", fontSize=21, leading=26, spaceAfter=15, textColor=colors.HexColor("#153455")))
    styles.add(ParagraphStyle(name="FinalHeading", fontName="Helvetica-Bold", fontSize=12, leading=16, spaceBefore=12, spaceAfter=7, textColor=colors.HexColor("#176b82")))
    styles.add(ParagraphStyle(name="FinalBody", fontName="Helvetica", fontSize=9.5, leading=14, spaceAfter=7, splitLongWords=True))
    story = []
    for line in text.splitlines():
        if not line.strip():
            continue
        if line == "---PAGE---":
            story.append(PageBreak())
        else:
            name = "FinalTitle" if line.startswith("# ") else "FinalHeading" if line.startswith("## ") else "FinalBody"
            content = line.lstrip("# ") if line.startswith("#") else line
            story.append(Paragraph(escape(content), styles[name]))
    def footer(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(1.8 * cm, 1.1 * cm, "TOEFL Mate | Metodologi dan hasil | Final UTS 03-11-2026")
        canvas.drawRightString(A4[0] - 1.8 * cm, 1.1 * cm, str(doc.page))
    with pdf.open("xb") as output:
        doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=1.8*cm, rightMargin=1.8*cm, topMargin=1.5*cm, bottomMargin=1.7*cm, title="TOEFL Mate - Metodologi Evaluasi dan Hasil Final UTS")
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
    with md.open("x", encoding="utf-8") as output:
        output.write(text.replace("---PAGE---", "---"))
    print(pdf)
    print(md)


if __name__ == "__main__":
    build()
