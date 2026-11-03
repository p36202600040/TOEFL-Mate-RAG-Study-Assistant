"""
app.py — TOEFL Mate: RAG Study Assistant (Streamlit UI)

Jalankan: streamlit run app.py
"""
import streamlit as st
import sys
import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Ensure fresh env values on every run
load_dotenv(override=True)

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
import importlib
importlib.reload(config)
import src.prompts
importlib.reload(src.prompts)
import src.generator
importlib.reload(src.generator)

from src.retriever import get_chroma_client, retrieve, index_compatibility
from src.generator import generate_answer
from src.evaluation import extract_citations, validate_citations_against_contexts


# ── Page config ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TOEFL Mate — RAG Study Assistant",
    page_icon="📚",
    layout="wide",
)


# ── Helper: check prerequisites ─────────────────────────────────────────
def load_collection():
    """Load ChromaDB collection freshly to prevent stale collection references."""
    try:
        client = get_chroma_client()
        collection = client.get_collection(config.CHROMA_COLLECTION)
        count = collection.count()
        return collection, count, None
    except Exception as e:
        return None, 0, type(e).__name__


def check_api_key():
    """Check if Groq API key is configured."""
    return bool(config.GROQ_API_KEY)


def build_retrieval_query(prompt: str, messages: list[dict]) -> str:
    """Tambahkan pertanyaan terakhir untuk follow-up singkat yang ambigu."""
    follow_up_markers = ("tadi", "sebelumnya", "itu", "tersebut", "bagian kedua", "jelaskan bagian")
    if not any(marker in prompt.lower() for marker in follow_up_markers):
        return prompt
    previous_questions = [m["content"] for m in messages[:-1] if m.get("role") == "user"]
    if not previous_questions:
        return prompt
    return f"Pertanyaan sebelumnya: {previous_questions[-1]}\nPertanyaan lanjutan: {prompt}"


# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Pengaturan")
    st.caption("Sesuaikan cara TOEFL Mate menjelaskan materi.")

    st.markdown("---")

    language = st.selectbox(
        "🌐 Bahasa Jawaban",
        ["Indonesia", "English"],
        index=0,
    )

    style = st.selectbox(
        "📝 Gaya Jawaban",
        ["penjelasan bertahap", "ringkas"],
        index=0,
    )

    level = st.selectbox(
        "📊 Tingkat Kesulitan",
        ["dasar", "menengah", "lanjutan"],
        index=1,
    )

    st.markdown("---")

    top_k = st.slider("🔍 Jumlah Konteks (top-k)", 1, 10, config.TOP_K)

    st.markdown("---")

    if st.button("🗑️ Hapus Percakapan", use_container_width=True):
        st.session_state.messages = []
        st.session_state.sources = []
        st.rerun()

    st.markdown("---")
    st.caption("Jawaban bergantung pada dokumen dalam indeks aktif. Periksa informasi TOEFL terkini melalui sumber resmi.")


# ── Main content ─────────────────────────────────────────────────────────
st.title("📚 TOEFL Mate")
st.caption("Asisten belajar berbasis dokumen • Periksa sitasi dan tanggal edisi sumber")

# Check prerequisites
collection, chunk_count, col_error = load_collection()
has_api_key = check_api_key()

# Status indicators
col1, col2, col3 = st.columns(3)
with col1:
    if collection and chunk_count > 0:
        st.success(f"✅ Indeks: {chunk_count} chunks")
        try:
            if index_compatibility(collection.name) == "UNKNOWN":
                st.caption("Kompatibilitas embedding belum dapat diverifikasi dari manifest.")
        except ValueError:
            st.error("Manifest indeks tidak cocok atau tidak dapat dibaca.")
    else:
        st.error("❌ Indeks belum dibuat")
        st.info("Bangun kandidat dengan `python scripts/ingest_pdf.py`, lalu aktifkan koleksinya sesuai README.")
with col2:
    if has_api_key:
        st.success("✅ Groq API Key")
    else:
        st.error("❌ API Key belum diatur")
        st.info("Isi `GROQ_API_KEY` di file `.env`")
with col3:
    active_display_model = config.GROQ_MODEL
    st.info(f"🤖 Model: {active_display_model}")

st.markdown("---")

# ── Chat interface ───────────────────────────────────────────────────────
# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sources" not in st.session_state:
    st.session_state.sources = []

# Display chat history
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Show sources for assistant messages
        if message["role"] == "assistant" and i < len(st.session_state.sources):
            sources = st.session_state.sources[i]
            if sources:
                with st.expander("📚 Konteks hasil pencarian (bukan bukti dukungan klaim)", expanded=False):
                    for src in sources:
                        page = src.get("page", "?")
                        source = src.get("source", "Dokumen")
                        distance = src.get("distance", 0)
                        text_preview = src.get("text", "")[:220]
                        st.markdown(
                            f"📖 **{source}** — **Halaman PDF {page}** *(Distance: {distance:.4f}; bukan probabilitas)*\n\n"
                            f"> {text_preview}..."
                        )

# Chat input
if prompt := st.chat_input("Tanyakan tentang TOEFL... (ID/EN)"):
    # Validate prerequisites
    if not collection or chunk_count == 0:
        st.error(
            "⚠️ Indeks belum dibuat. Jalankan terlebih dahulu:\n\n"
            "```\npython scripts/ingest_pdf.py\n```"
        )
    elif not has_api_key:
        st.error(
            "⚠️ GROQ_API_KEY belum diatur. Buat file `.env` dan isi:\n\n"
            "```\nGROQ_API_KEY=your_key_here\n```"
        )
    else:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.sources.append(None)  # Placeholder for user msg

        with st.chat_message("user"):
            st.markdown(prompt)

        # Retrieve and generate
        with st.chat_message("assistant"):
            retrieval_failed = False
            ambiguous_reference = bool(re.search(r"\b(?:bagian|poin|item)\s+(?:pertama|kedua|ketiga|keempat|\d+)|\b(?:first|second|third|fourth)\s+(?:part|item|section)\b", prompt, re.I))
            try:
                with st.spinner("🔍 Mencari konteks yang relevan..."):
                    if ambiguous_reference:
                        contexts = []
                    else:
                        retrieval_query = build_retrieval_query(prompt, st.session_state.messages)
                        contexts = retrieve(retrieval_query, top_k=top_k, collection=collection)
            except Exception:
                retrieval_failed = True
                contexts = []
                st.error(
                    "⚠️ Pencarian konteks gagal. Periksa indeks dan model embedding, "
                    "lalu coba lagi."
                )

            if ambiguous_reference:
                answer = ("Bagian yang mana? Sebutkan nama atau topiknya agar saya tidak salah merujuk."
                          if language == "Indonesia" else
                          "Which part do you mean? Please name the topic so I can find the right context.")
                sources_display = []
            elif retrieval_failed:
                answer = "Pencarian konteks gagal karena kesalahan teknis. Silakan coba lagi."
                sources_display = []
            elif not contexts:
                answer = (
                    "Maaf, saya tidak menemukan konteks yang relevan dalam dokumen "
                    "untuk pertanyaan ini. Coba ubah kata kunci atau pertanyaan Anda."
                )
                sources_display = []
            else:
                with st.spinner("💭 Menyusun jawaban..."):
                    # Build chat history for context
                    chat_hist = [
                        m for m in st.session_state.messages[:-1]
                        if m["role"] in ("user", "assistant")
                    ]

                    result = generate_answer(
                        question=prompt,
                        contexts=contexts,
                        chat_history=chat_hist if chat_hist else None,
                        language=language,
                        style=style,
                        level=level,
                        model=config.GROQ_MODEL,
                    )

                if result["error"]:
                    answer = f"⚠️ Terjadi kesalahan: {result['error']}"
                    sources_display = []
                else:
                    answer = result["answer"]
                    sources_display = contexts
                    citations = validate_citations_against_contexts(extract_citations(answer), contexts)
                    if not citations:
                        st.info("Tidak ada sitasi yang dapat dibaca. Penolakan murni tidak selalu memerlukan sitasi; periksa klaim faktual secara manual.")
                    elif any(not citation["in_retrieved_context"] for citation in citations):
                        st.warning("Sebagian sitasi tidak ditemukan dalam konteks pencarian.")

                    # Show latency
                    st.caption(f"⏱️ {result['latency_seconds']}s | 🤖 {result['model']}")

            st.markdown(answer)

            # Show sources
            if sources_display:
                with st.expander("📚 Konteks hasil pencarian (bukan bukti dukungan klaim)", expanded=False):
                    for src in sources_display:
                        page = src.get("page", "?")
                        source = src.get("source", "Dokumen")
                        distance = src.get("distance", 0)
                        text_preview = src.get("text", "")[:220]
                        st.markdown(
                            f"📖 **{source}** — **Halaman PDF {page}** *(Distance: {distance:.4f}; bukan probabilitas)*\n\n"
                            f"> {text_preview}..."
                        )

        # Save to session state
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.sources.append(sources_display)
