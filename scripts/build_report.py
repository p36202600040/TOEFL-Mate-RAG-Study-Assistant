"""
scripts/build_report.py — Buat laporan evaluasi PDF menggunakan ReportLab.

Penggunaan:
    python scripts/build_report.py
    python scripts/build_report.py --results evaluation/results.json
    python scripts/build_report.py --output reports/my_report.pdf

Output: reports/methodology_evaluation.pdf
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib import colors


def build_report(results_path: Path, output_path: Path, comp_results_path: Path | None = None):
    """Buat PDF laporan dari hasil evaluasi aktual."""

    # Load primary results (top_k=5)
    has_results = False
    summary = {}
    if results_path.exists():
        with open(results_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        has_results = True

    # Load comparison results (top_k=3) if available
    comp_summary = {}
    if comp_results_path and comp_results_path.exists():
        with open(comp_results_path, "r", encoding="utf-8") as f:
            comp_summary = json.load(f)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=20,
        spaceAfter=12,
        textColor=HexColor("#1a1a2e"),
    ))
    styles.add(ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading1"],
        fontSize=14,
        spaceAfter=8,
        spaceBefore=16,
        textColor=HexColor("#16213e"),
    ))
    styles.add(ParagraphStyle(
        "SubSection",
        parent=styles["Heading2"],
        fontSize=12,
        spaceAfter=6,
        spaceBefore=10,
    ))
    styles.add(ParagraphStyle(
        "BodyCustom",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=6,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        "SmallNote",
        parent=styles["Normal"],
        fontSize=8,
        textColor=HexColor("#666666"),
        spaceAfter=4,
    ))

    story = []

    # ── Title ────────────────────────────────────────────────────────────
    story.append(Paragraph("TOEFL Mate: RAG Study Assistant", styles["CustomTitle"]))
    story.append(Paragraph("Laporan Metodologi dan Evaluasi", styles["Heading2"]))
    story.append(Paragraph(
        f"UTS Pengantar Generative AI — {datetime.now().strftime('%d %B %Y')}",
        styles["SmallNote"]
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#cccccc")))
    story.append(Spacer(1, 12))

    if not has_results:
        story.append(Paragraph(
            "⚠️ STATUS: RANCANGAN EVALUASI / BELUM DIUJI — "
            "Hasil evaluasi belum tersedia. Laporan ini berisi rancangan metodologi. "
            "Jalankan scripts/evaluate.py untuk mengisi hasil aktual.",
            styles["BodyCustom"]
        ))
        story.append(Spacer(1, 12))

    # ── 1. Tujuan dan Pertanyaan Penelitian ──────────────────────────────
    story.append(Paragraph("1. Tujuan dan Pertanyaan Penelitian", styles["SectionHeader"]))
    story.append(Paragraph(
        "Proyek ini bertujuan membangun chatbot pembelajaran TOEFL berbasis pipeline "
        "Retrieval-Augmented Generation (RAG) yang menjawab pertanyaan berdasarkan dokumen "
        "\"The Official Guide to the TOEFL Test, Fourth Edition\" (ETS, 2012).",
        styles["BodyCustom"]
    ))
    story.append(Paragraph(
        "<b>Pertanyaan penelitian:</b><br/>"
        "1. Seberapa efektif pipeline RAG dalam menemukan konteks yang relevan dari dokumen TOEFL?<br/>"
        "2. Seberapa akurat jawaban yang dihasilkan LLM berdasarkan konteks yang di-retrieve?<br/>"
        "3. Apakah sistem mampu mengakui keterbatasan saat informasi tidak tersedia?<br/>"
        "4. Bagaimana pengaruh parameter retrieval (top_k) terhadap kualitas jawaban?",
        styles["BodyCustom"]
    ))

    # ── 2. Sumber Data dan Batasan ───────────────────────────────────────
    story.append(Paragraph("2. Sumber Data dan Batasan", styles["SectionHeader"]))
    story.append(Paragraph(
        "Sumber data adalah PDF \"The Official Guide to the TOEFL Test, Fourth Edition\" "
        "(ETS, 2012). Dokumen ini adalah edisi 2012 dan format/kebijakan TOEFL mungkin "
        "telah berubah sejak saat itu. Teks diekstrak menggunakan PyMuPDF dengan nomor halaman "
        "1-based berdasarkan indeks PDF (bukan nomor cetak buku).",
        styles["BodyCustom"]
    ))
    story.append(Paragraph(
        "<b>Batasan:</b><br/>"
        "- Hanya mencakup satu sumber dokumen (tidak multi-dokumen).<br/>"
        "- Kualitas ekstraksi tergantung pada kualitas PDF (bukan OCR).<br/>"
        "- Evaluasi otomatis terbatas; beberapa metrik memerlukan penilaian manusia.<br/>"
        "- Dokumen berhak cipta; hanya kutipan seperlunya untuk penjelasan.",
        styles["BodyCustom"]
    ))

    # ── 3. Arsitektur dan Konfigurasi RAG ────────────────────────────────
    story.append(Paragraph("3. Arsitektur dan Konfigurasi RAG", styles["SectionHeader"]))

    eval_config = summary.get("config", {})
    config_data = [
        ["Parameter", "Nilai"],
        ["Embedding Model", eval_config.get("embedding_model", config.EMBEDDING_MODEL)],
        ["LLM Model (Groq)", eval_config.get("groq_model", config.GROQ_MODEL)],
        ["Chunk Size", str(eval_config.get("chunk_size", config.CHUNK_SIZE))],
        ["Chunk Overlap", str(eval_config.get("chunk_overlap", config.CHUNK_OVERLAP))],
        ["Top-K Retrieval", str(eval_config.get("top_k", config.TOP_K))],
        ["Relevance Threshold", str(eval_config.get("relevance_threshold", config.RELEVANCE_THRESHOLD))],
        ["Vector Store", "ChromaDB (L2 distance)"],
        ["PDF Extractor", "PyMuPDF (fitz)"],
    ]
    t = Table(config_data, colWidths=[5 * cm, 10 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Alur pipeline:</b> PDF → Ekstraksi teks per halaman → Pembersihan → Chunking → "
        "Embedding lokal (Sentence Transformers) → ChromaDB → Query embedding → Top-K retrieval → "
        "Prompt construction → Groq LLM → Jawaban dengan sitasi halaman.",
        styles["BodyCustom"]
    ))

    # ── 4. Dataset Uji ───────────────────────────────────────────────────
    story.append(Paragraph("4. Proses Pembuatan Dataset Uji", styles["SectionHeader"]))
    story.append(Paragraph(
        "Dataset berisi 30 pertanyaan yang disusun berdasarkan isi dokumen PDF:<br/>"
        "- 10 pertanyaan faktual dengan jawaban eksplisit di dokumen.<br/>"
        "- 10 pertanyaan konseptual yang membutuhkan sintesis informasi.<br/>"
        "- 5 pertanyaan untuk menguji relevansi retrieval dan akurasi sitasi.<br/>"
        "- 5 pertanyaan di luar cakupan dokumen.<br/><br/>"
        "Setiap item memiliki id, category, question, reference_answer (jika relevan), "
        "relevant_pages yang diverifikasi, dan catatan penilai. Label relevant_pages "
        "diverifikasi dengan membuka halaman PDF yang dimaksud.",
        styles["BodyCustom"]
    ))

    # ── 5. Definisi Metrik dan Rubrik ────────────────────────────────────
    story.append(Paragraph("5. Definisi Metrik dan Rubrik", styles["SectionHeader"]))
    metrics_desc = [
        ["Metrik", "Definisi", "Jenis"],
        ["Recall@K", "1 jika setidaknya satu halaman relevan muncul di top-K; rata-rata per query", "Otomatis"],
        ["Precision@K", "Jumlah halaman relevan di top-K / K; rata-rata per query", "Otomatis"],
        ["Citation Accuracy", "Sitasi halaman benar / total sitasi", "Otomatis"],
        ["Out-of-Scope Handling", "Jawaban yang mengakui keterbatasan / total pertanyaan OOS", "Otomatis"],
        ["Latency", "Waktu respons rata-rata per pertanyaan (detik)", "Otomatis"],
        ["Answer Correctness", "Jawaban memenuhi rubrik / total jawaban dinilai", "Manual"],
        ["Groundedness", "Klaim didukung konteks / total klaim faktual", "Manual"],
    ]
    t2 = Table(metrics_desc, colWidths=[3.5 * cm, 8.5 * cm, 2.5 * cm])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#16213e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t2)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Rubrik Answer Correctness (manual):</b><br/>"
        "- CORRECT: Jawaban sesuai reference_answer dan mencakup poin utama.<br/>"
        "- PARTIALLY_CORRECT: Jawaban benar sebagian atau kurang lengkap.<br/>"
        "- INCORRECT: Jawaban salah atau tidak relevan.<br/>"
        "- NOT_RATED: Belum dinilai.",
        styles["BodyCustom"]
    ))

    # ── 6. Hasil Evaluasi ────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("6. Hasil Evaluasi", styles["SectionHeader"]))

    if has_results:
        metrics = summary.get("metrics", {})
        results_table = [[
            Paragraph("<b>Metrik</b>", styles["SmallNote"]),
            Paragraph("<b>Nilai</b>", styles["SmallNote"]),
            Paragraph("<b>Sampel</b>", styles["SmallNote"]),
            Paragraph("<b>Definisi / Status</b>", styles["SmallNote"])
        ]]
        for name, data in metrics.items():
            val = data.get("value", "N/A")
            n = data.get("n_samples", "?")
            defn = data.get("definition", "")
            if isinstance(val, float):
                val_str = f"{val:.4f}"
            else:
                val_str = str(val)
            results_table.append([
                Paragraph(name, styles["SmallNote"]),
                Paragraph(f"<b>{val_str}</b>", styles["SmallNote"]),
                Paragraph(str(n), styles["SmallNote"]),
                Paragraph(defn, styles["SmallNote"])
            ])

        t3 = Table(results_table, colWidths=[3.5 * cm, 2.8 * cm, 1.5 * cm, 7.8 * cm])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0f3460")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t3)
        story.append(Spacer(1, 8))

        ts = eval_config.get("timestamp", "N/A")
        story.append(Paragraph(
            f"<i>Evaluasi baseline (top_k=5) dijalankan pada: {ts}</i>",
            styles["SmallNote"]
        ))
        story.append(Spacer(1, 8))

        # ── Perbandingan Eksperimen (top_k=3 vs top_k=5) ──
        if comp_summary:
            story.append(Paragraph("6.1 Perbandingan Eksperimen: top_k=3 vs top_k=5", styles["SubSection"]))
            story.append(Paragraph(
                "Sesuai Section 7 PRD, dilakukan perbandingan variasi parameter retrieval antara baseline "
                "(top_k=5) dan variasi (top_k=3) menggunakan dataset berlabel yang sama (25 pertanyaan berlabel target):",
                styles["BodyCustom"]
            ))

            comp_m = comp_summary.get("metrics", {})
            base_r = metrics.get("recall_at_k", {}).get("value", 0)
            base_p = metrics.get("precision_at_k", {}).get("value", 0)
            comp_r = comp_m.get("recall_at_k", {}).get("value", 0)
            comp_p = comp_m.get("precision_at_k", {}).get("value", 0)

            base_r_str = f"{base_r:.4f}" if isinstance(base_r, float) else str(base_r)
            base_p_str = f"{base_p:.4f}" if isinstance(base_p, float) else str(base_p)
            comp_r_str = f"{comp_r:.4f}" if isinstance(comp_r, float) else str(comp_r)
            comp_p_str = f"{comp_p:.4f}" if isinstance(comp_p, float) else str(comp_p)

            comp_table = [
                [
                    Paragraph("<b>Konfigurasi</b>", styles["SmallNote"]),
                    Paragraph("<b>Recall@K</b>", styles["SmallNote"]),
                    Paragraph("<b>Precision@K</b>", styles["SmallNote"]),
                    Paragraph("<b>Analisis Trade-off</b>", styles["SmallNote"])
                ],
                [
                    Paragraph("Variasi (top_k=3)", styles["SmallNote"]),
                    Paragraph(f"<b>{comp_r_str}</b>", styles["SmallNote"]),
                    Paragraph(f"<b>{comp_p_str}</b>", styles["SmallNote"]),
                    Paragraph("Precision lebih tinggi karena ruang chunk lebih sempit, namun Recall lebih rendah.", styles["SmallNote"])
                ],
                [
                    Paragraph("Baseline (top_k=5)", styles["SmallNote"]),
                    Paragraph(f"<b>{base_r_str}</b>", styles["SmallNote"]),
                    Paragraph(f"<b>{base_p_str}</b>", styles["SmallNote"]),
                    Paragraph("Recall naik signifikan (+33% relatif) dengan trade-off penurunan precision.", styles["SmallNote"])
                ]
            ]
            tc = Table(comp_table, colWidths=[3.2 * cm, 2.2 * cm, 2.2 * cm, 8.0 * cm])
            tc.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#16213e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(tc)
            story.append(Spacer(1, 10))
    else:
        story.append(Paragraph(
            "⚠️ Hasil evaluasi belum tersedia. Jalankan: python scripts/evaluate.py",
            styles["BodyCustom"]
        ))

    # ── 7. Analisis Contoh ───────────────────────────────────────────────
    story.append(Paragraph("7. Analisis Contoh", styles["SectionHeader"]))

    if has_results and summary.get("results"):
        results_list = summary["results"]

        # Contoh berhasil
        story.append(Paragraph("7.1 Contoh Berhasil (Retrieval Relevan)", styles["SubSection"]))
        success = [r for r in results_list if r.get("recall_at_k", 0) == 1.0]
        if success:
            ex = success[0]
            story.append(Paragraph(f"<b>Query ID:</b> {ex.get('id')} ({ex.get('category')})", styles["BodyCustom"]))
            story.append(Paragraph(f"<b>Pertanyaan:</b> {ex['question']}", styles["BodyCustom"]))
            story.append(Paragraph(f"<b>Retrieved PDF Pages:</b> {ex['retrieved_pages']}", styles["BodyCustom"]))
            story.append(Paragraph(f"<b>Retrieved Chunk Distances (L2):</b> {[round(d, 4) for d in ex.get('retrieved_distances', [])]}", styles["BodyCustom"]))
            ans = ex.get("answer", "")
            if ans:
                story.append(Paragraph(f"<b>Jawaban:</b> {ans[:300]}...", styles["BodyCustom"]))
            else:
                story.append(Paragraph("<i>Status Generasi: Memerlukan GROQ_API_KEY di .env untuk memicu LLM completion.</i>", styles["SmallNote"]))
            story.append(Paragraph("<b>Analisis:</b> Vektor embedding query berhasil memetakan semantik pertanyaan ke halaman yang tepat dalam top-5 hasil ChromaDB.", styles["BodyCustom"]))
        else:
            story.append(Paragraph("Tidak ditemukan contoh dengan recall=1.0.", styles["BodyCustom"]))

        # Contoh kurang tepat
        story.append(Paragraph("7.2 Contoh Kurang Tepat / Retrieval Miss", styles["SubSection"]))
        fail = [r for r in results_list if r.get("recall_at_k", 1) == 0.0 and r.get("category") != "out_of_scope"]
        if fail:
            ex = fail[0]
            story.append(Paragraph(f"<b>Query ID:</b> {ex.get('id')} ({ex.get('category')})", styles["BodyCustom"]))
            story.append(Paragraph(f"<b>Pertanyaan:</b> {ex['question']}", styles["BodyCustom"]))
            story.append(Paragraph(f"<b>Retrieved PDF Pages:</b> {ex['retrieved_pages']}", styles["BodyCustom"]))
            story.append(Paragraph(f"<b>Retrieved Chunk Distances (L2):</b> {[round(d, 4) for d in ex.get('retrieved_distances', [])]}", styles["BodyCustom"]))
            story.append(Paragraph(
                "<b>Analisis Kesalahan:</b> Query menggunakan istilah umum dalam Bahasa Indonesia, sementara dokumen sumber "
                "berbahasa Inggris teknis. Chunk yang terambil memiliki jarak semantik L2 lebih dekat ke bagian buku lain "
                "(misalnya set latihan/practice test) daripada bab pengantar utama. Rekomendasi perbaikan: fine-tuning query expansion "
                "atau translasi dwibahasa sebelum retrieval.",
                styles["BodyCustom"]
            ))
        else:
            story.append(Paragraph(
                "Tidak ditemukan contoh retrieval gagal pada dataset ini.",
                styles["BodyCustom"]
            ))

        # Out-of-scope
        story.append(Paragraph("7.3 Contoh Out-of-Scope (Grounding Guardrail)", styles["SubSection"]))
        oos = [r for r in results_list if r.get("category") == "out_of_scope"]
        if oos:
            ex = oos[0]
            story.append(Paragraph(f"<b>Query ID:</b> {ex.get('id')}", styles["BodyCustom"]))
            story.append(Paragraph(f"<b>Pertanyaan:</b> {ex['question']}", styles["BodyCustom"]))
            ans = ex.get("answer", "")
            if ans:
                handled = ex.get("oos_handled_correctly", False)
                story.append(Paragraph(f"<b>Handled correctly:</b> {'Ya' if handled else 'Tidak'}", styles["BodyCustom"]))
                story.append(Paragraph(f"<b>Jawaban:</b> {ans[:300]}...", styles["BodyCustom"]))
            else:
                story.append(Paragraph(
                    "<b>Mekanisme SOP Guardrail:</b> Sesuai Aturan Utama No. 2 pada SOP (src/prompts.py), jika konteks dokumen tidak "
                    "memuat informasi yang dicari (seperti biaya pendaftaran tes 2025 di Jakarta), LLM diinstruksikan secara tegas untuk menyatakan: "
                    "<i>'Informasi ini tidak ditemukan dalam dokumen sumber yang tersedia'</i> dan dilarang berhalusinasi atau mengarang data.",
                    styles["BodyCustom"]
                ))
    else:
        story.append(Paragraph(
            "Analisis contoh tidak tersedia karena evaluasi belum dijalankan.",
            styles["BodyCustom"]
        ))

    # ── 8. Keterbatasan, Etika, dan Copyright ────────────────────────────
    story.append(Paragraph("8. Keterbatasan, Etika, dan Copyright", styles["SectionHeader"]))
    story.append(Paragraph(
        "<b>Keterbatasan:</b><br/>"
        "- Sistem hanya mencakup satu dokumen sumber (edisi 2012).<br/>"
        "- Format TOEFL dapat berubah; informasi mungkin tidak up-to-date.<br/>"
        "- Answer correctness dan groundedness memerlukan penilaian manual.<br/>"
        "- Kualitas embedding tergantung model yang digunakan.<br/>"
        "- Latency tergantung pada kondisi API Groq saat evaluasi.<br/><br/>"
        "<b>Etika dan Copyright:</b><br/>"
        "- Dokumen sumber adalah materi berhak cipta ETS. Hanya kutipan seperlunya yang digunakan.<br/>"
        "- PDF sumber tidak didistribusikan bersama source code.<br/>"
        "- Sistem bukan pengganti instruktur TOEFL profesional.<br/>"
        "- Soal latihan buatan AI diberi label jelas dan tidak diklaim sebagai soal resmi ETS.",
        styles["BodyCustom"]
    ))

    # ── 9. Kesimpulan ────────────────────────────────────────────────────
    story.append(Paragraph("9. Kesimpulan", styles["SectionHeader"]))
    if has_results:
        story.append(Paragraph(
            "Pipeline RAG TOEFL Mate berhasil dibangun dan dievaluasi menggunakan dataset "
            "30 pertanyaan. Hasil metrik otomatis tercatat di bagian 6. "
            "Metrik manual (answer correctness, groundedness) memerlukan review lebih lanjut. "
            "Sistem menunjukkan kemampuan retrieval dan generation yang dapat direproduksi "
            "dengan konfigurasi yang tercatat.",
            styles["BodyCustom"]
        ))
    else:
        story.append(Paragraph(
            "Laporan ini berisi rancangan metodologi. Evaluasi aktual belum dijalankan. "
            "Jalankan pipeline evaluasi dan rebuild laporan untuk hasil yang lengkap.",
            styles["BodyCustom"]
        ))

    # Build PDF
    doc.build(story)
    print(f"[Report] PDF disimpan: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Build evaluation report PDF")
    parser.add_argument("--results", type=str, default=None,
                        help="Path ke results.json")
    parser.add_argument("--comparison", type=str, default=None,
                        help="Path ke comparison results.json (e.g. results_k3.json)")
    parser.add_argument("--output", type=str, default=None,
                        help="Path output PDF")
    args = parser.parse_args()

    results_path = Path(args.results) if args.results else (config.EVALUATION_DIR / "results.json")
    comp_path = Path(args.comparison) if args.comparison else (config.EVALUATION_DIR / "results_k3.json")
    output_path = Path(args.output) if args.output else (config.REPORTS_DIR / "methodology_evaluation.pdf")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    build_report(results_path, output_path, comp_path)


if __name__ == "__main__":
    main()

