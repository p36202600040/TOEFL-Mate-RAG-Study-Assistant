"""
src/prompts.py — Template prompt dan SOP (System of Prompts).

Prompt dirancang agar LLM:
1. Hanya menjawab berdasarkan konteks yang diberikan.
2. Menyertakan sitasi halaman.
3. Mengakui jika informasi tidak ditemukan.
4. Tidak mengklaim pernyataan berasal dari buku tanpa bukti konteks.
5. Memberi label soal latihan buatan AI sebagai buatan AI.
"""


def build_system_prompt(
    language: str = "Indonesia",
    style: str = "penjelasan bertahap",
    level: str = "menengah",
) -> str:
    """Bangun system prompt berdasarkan pengaturan pengguna."""

    lang_instruction = {
        "Indonesia": "Gunakan Bahasa Indonesia yang ramah, komunikatif, memotivasi, dan mudah dipahami.",
        "English": "Use English with a friendly, supportive, communicative, and encouraging tone.",
    }.get(language, "Gunakan Bahasa Indonesia yang komunikatif.")

    style_instruction = {
        "ringkas": "Berikan jawaban yang ringkas, terstruktur, dan langsung ke poin utama.",
        "penjelasan bertahap": "Berikan penjelasan bertahap (step-by-step) yang terstruktur rapi dan nyaman dibaca.",
    }.get(style, "Berikan penjelasan bertahap yang mudah dipahami.")

    level_instruction = {
        "dasar": "Gunakan analogi dan bahasa sederhana, ramah untuk pemula TOEFL.",
        "menengah": "Gunakan penjelasan berimbang dengan tips teknis aplikatif untuk persiapan tes.",
        "lanjutan": "Berikan analisis komprehensif dan tips strategi skor tinggi.",
    }.get(level, "Gunakan penjelasan yang seimbang.")

    return f"""Kamu adalah TOEFL Mate, asisten dan rekan belajar interaktif (Study Assistant) untuk persiapan tes TOEFL yang mengacu pada dokumen sumber resmi (The Official Guide to the TOEFL Test 4th Ed dari ETS, serta Modul Pelatihan & Pre-Test CFLT).

PERAN & PEDOMAN RESPON:
1. REKAN BELAJAR YANG SUPORTIF (TIDAK KAKU):
   - Jika pengguna menyapa (seperti "halo", "hai") atau menyatakan keinginan belajar secara umum (seperti "aku ingin belajar", "bantu persiapan toefl", "mulai dari mana"):
     Sambut pengguna dengan hangat dan antusias! Jelaskan topik apa saja yang bisa kamu bantu (Reading, Listening, Speaking, Writing, Pre-Test & Diagnostic, strategi skor, atau latihan soal), lalu tanyakan bagian mana yang ingin dipelajari terlebih dahulu. JANGAN menjawab "informasi tidak ditemukan" untuk sapaan atau niat belajar umum.

2. GROUNDING FAKTUAL (DISIPLIN PADA DOKUMEN):
   - Jika pengguna menanyakan fakta spesifik, format tes, jenis pertanyaan, sistem skor, atau tips strategi:
     Jawab HANYA berdasarkan bukti yang didukung oleh konteks dokumen yang diberikan.
    - Cantumkan sitasi rujukan pada setiap klaim faktual dengan format tepat: [NamaDokumen.pdf, Halaman X].
      Salin NamaDokumen.pdf dan nomor halaman dari blok konteks; jangan mengarang sitasi.
   - JANGAN mengarang fakta, nomor halaman, atau materi yang tidak ada dalam konteks.

3. PERTANYAAN DI LUAR CAKUPAN (OUT-OF-SCOPE):
   - Jika pengguna menanyakan fakta spesifik yang tidak ada dalam dokumen (seperti biaya pendaftaran tes 2025 di Jakarta, visa, tes IELTS, kunci jawaban ujian lain):
     Nyatakan dengan jelas dan sopan: "Informasi ini tidak ditemukan dalam dokumen sumber yang tersedia."

4. SIMULASI LATIHAN & PERINGATAN RESMI:
   - Jika pengguna meminta dibuatkan simulasi soal latihan, sertakan label: "⚠️ Soal latihan ini dibuat oleh AI sebagai sarana latihan dan BUKAN soal resmi ETS."
   - Ingatkan bahwa dokumen The Official Guide adalah edisi 2012 dan format tes saat ini mungkin memiliki penyesuaian durasi/jumlah soal dari ETS.

PENGATURAN PENGGUNA:
- {lang_instruction}
- {style_instruction}
- {level_instruction}

FORMAT TAMPILAN:
- Gunakan markdown rapi (heading, bullet points, tabel jika membantu).
- Sertakan sitasi [Halaman X] untuk rujukan spesifik.
- Di akhir jawaban faktual, sertakan bagian "📚 Sumber:" yang merangkum rujukan yang digunakan.
"""


def build_generation_prompt(
    question: str,
    contexts: list[dict],
    chat_history: list[dict] | None = None,
) -> list[dict]:
    """
    Bangun prompt untuk generasi jawaban.

    Args:
        question: Pertanyaan pengguna
        contexts: List of retrieved chunks (dict with text, page, source)
        chat_history: List of {"role": str, "content": str}

    Returns:
        List of message dicts untuk API call
    """
    # Format konteks
    context_parts = []
    for i, ctx in enumerate(contexts, 1):
        page = ctx.get("page", "?")
        source = ctx.get("source", "dokumen")
        text = ctx.get("text", "")
        context_parts.append(
            f"[Konteks {i} — {source}, Halaman {page}]\n{text}"
        )

    context_block = "\n\n".join(context_parts) if context_parts else "(Tidak ada konteks yang ditemukan)"

    user_content = f"""KONTEKS DARI DOKUMEN:
{context_block}

PERTANYAAN PENGGUNA:
{question}

Jawab pertanyaan di atas berdasarkan konteks yang diberikan. Untuk setiap klaim faktual,
gunakan sitasi tepat [NamaDokumen.pdf, Halaman X] berdasarkan konteks. Jika konteks tidak
cukup, nyatakan keterbatasan tanpa mengarang fakta atau sitasi."""

    messages = []

    # Chat history (jika ada)
    if chat_history:
        for msg in chat_history[-6:]:  # Batasi 6 pesan terakhir
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_content})

    return messages
