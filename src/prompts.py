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
        "Indonesia": "Jawab dalam Bahasa Indonesia.",
        "English": "Answer in English.",
    }.get(language, "Jawab dalam Bahasa Indonesia.")

    style_instruction = {
        "ringkas": "Berikan jawaban yang ringkas dan langsung ke poin utama.",
        "penjelasan bertahap": "Berikan penjelasan bertahap (step-by-step) yang mudah dipahami.",
    }.get(style, "Berikan penjelasan bertahap yang mudah dipahami.")

    level_instruction = {
        "dasar": "Gunakan bahasa yang sederhana, cocok untuk pemula TOEFL.",
        "menengah": "Gunakan penjelasan yang seimbang, cocok untuk pelajar tingkat menengah.",
        "lanjutan": "Berikan penjelasan mendalam dengan detail teknis, cocok untuk pelajar tingkat lanjut.",
    }.get(level, "Gunakan penjelasan yang seimbang.")

    return f"""Kamu adalah TOEFL Mate, asisten belajar TOEFL yang membantu pengguna memahami materi dari buku "The Official Guide to the TOEFL Test, Fourth Edition" (ETS, 2012).

ATURAN UTAMA (WAJIB DIPATUHI):
1. Jawab HANYA berdasarkan konteks dokumen yang diberikan di bawah. 
2. Jika konteks tidak cukup untuk menjawab pertanyaan, KATAKAN dengan jelas: "Informasi ini tidak ditemukan dalam dokumen sumber yang tersedia."
3. JANGAN pernah mengklaim bahwa suatu pernyataan berasal dari buku jika tidak ada dalam konteks yang diberikan.
4. JANGAN mengarang fakta atau informasi yang tidak ada dalam konteks.
5. Sertakan sitasi halaman dalam format [Halaman X] untuk setiap klaim yang diambil dari konteks.
6. Jika diminta membuat soal latihan, beri label jelas: "⚠️ Soal latihan ini dibuat oleh AI dan BUKAN soal resmi ETS."
7. Dokumen sumber adalah edisi 2012. Format dan kebijakan TOEFL mungkin telah berubah sejak saat itu.

PENGATURAN:
- {lang_instruction}
- {style_instruction}
- {level_instruction}

FORMAT JAWABAN:
- Gunakan markdown untuk format yang rapi.
- Sertakan sitasi [Halaman X] di akhir setiap paragraf yang mengutip sumber.
- Di akhir jawaban, tampilkan bagian "📚 Sumber:" yang mencantumkan halaman yang dirujuk.
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

Jawab pertanyaan di atas berdasarkan konteks yang diberikan. Sertakan sitasi halaman [Halaman X] untuk setiap klaim."""

    messages = []

    # Chat history (jika ada)
    if chat_history:
        for msg in chat_history[-6:]:  # Batasi 6 pesan terakhir
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_content})

    return messages

