"""
app.py — TOEFL Mate: RAG Study Assistant (Streamlit UI)

Jalankan: streamlit run app.py
"""
import streamlit as st
import sys
import os
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

from src.retriever import get_chroma_client, get_or_create_collection, retrieve
from src.generator import generate_answer


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
        collection = get_or_create_collection(client)
        count = collection.count()
        return collection, count, None
    except Exception as e:
        return None, 0, str(e)


def check_api_key():
    """Check if Groq API key is configured."""
    return bool(config.GROQ_API_KEY)


# ── Sidebar ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/book-and-pencil.png", width=60)
    st.title("⚙️ Pengaturan")

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
    st.caption(
        "📖 **Sumber Dokumen Terdaftar:**\n\n"
        "1. *The Official Guide to the TOEFL Test, 4th Ed.* (ETS, 2012)\n"
        "2. *Pre-Test & Modul Pelatihan TOEFL* (CFLT UDINUS)\n\n"
        "⚠️ Edisi 2012 — format resmi TOEFL mungkin memiliki penyesuaian terkini.\n\n"
        "🤖 Dibuat untuk UTS Pengantar Generative AI"
    )


# ── Main content ─────────────────────────────────────────────────────────
st.title("📚 TOEFL Mate")
st.caption("RAG Study Assistant — Belajar TOEFL dari buku resmi ETS")

# Check prerequisites
collection, chunk_count, col_error = load_collection()
has_api_key = check_api_key()

# Status indicators
col1, col2, col3 = st.columns(3)
with col1:
    if collection and chunk_count > 0:
        st.success(f"✅ Indeks: {chunk_count} chunks")
    else:
        st.error("❌ Indeks belum dibuat")
        st.info("Jalankan: `python scripts/ingest_pdf.py`")
with col2:
    if has_api_key:
        st.success("✅ Groq API Key")
    else:
        st.error("❌ API Key belum diatur")
        st.info("Isi `GROQ_API_KEY` di file `.env`")
with col3:
    active_display_model = os.getenv("GROQ_MODEL", config.GROQ_MODEL)
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
                with st.expander("📚 Sumber yang digunakan", expanded=False):
                    for src in sources:
                        page = src.get("page", "?")
                        source = src.get("source", "Dokumen")
                        distance = src.get("distance", 0)
                        text_preview = src.get("text", "")[:220]
                        st.markdown(
                            f"📖 **{source}** — **Halaman {page}** *(Distance: {distance:.4f})*\n\n"
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
            with st.spinner("🔍 Mencari konteks yang relevan..."):
                contexts = retrieve(prompt, top_k=top_k, collection=collection)

            if not contexts:
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
                        model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip(),
                    )

                if result["error"]:
                    answer = f"⚠️ Terjadi kesalahan: {result['error']}"
                    sources_display = []
                else:
                    answer = result["answer"]
                    sources_display = contexts

                    # Show latency
                    st.caption(f"⏱️ {result['latency_seconds']}s | 🤖 {result['model']}")

            st.markdown(answer)

            # Show sources
            if sources_display:
                with st.expander("📚 Sumber yang digunakan", expanded=False):
                    for src in sources_display:
                        page = src.get("page", "?")
                        source = src.get("source", "Dokumen")
                        distance = src.get("distance", 0)
                        text_preview = src.get("text", "")[:220]
                        st.markdown(
                            f"📖 **{source}** — **Halaman {page}** *(Distance: {distance:.4f})*\n\n"
                            f"> {text_preview}..."
                        )

        # Save to session state
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.sources.append(sources_display)

