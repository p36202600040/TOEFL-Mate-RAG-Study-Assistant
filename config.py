"""
config.py — Konfigurasi utama TOEFL Mate RAG Study Assistant.

Semua rahasia dibaca dari .env; tidak ada API key yang di-hardcode.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
EVALUATION_DIR = PROJECT_ROOT / "evaluation"
REPORTS_DIR = PROJECT_ROOT / "reports"

# ── PDF ingestion ────────────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))       # karakter per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))  # overlap antar chunk

# ── Embedding ────────────────────────────────────────────────────────────
# Model sentence-transformers yang ringan dan tersedia secara lokal
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "all-MiniLM-L6-v2"
)

# ── ChromaDB ─────────────────────────────────────────────────────────────
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "toefl_mate")

# ── Retrieval ────────────────────────────────────────────────────────────
TOP_K = int(os.getenv("TOP_K", "5"))
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "1.5"))
# ChromaDB menggunakan L2 distance secara default.
# Semakin kecil nilainya, semakin mirip. Threshold 1.5 bersifat permisif;
# sesuaikan berdasarkan eksperimen.

# ── Groq API ─────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
# Nama model harus sesuai dengan model yang tersedia di Groq pada saat digunakan.
# Verifikasi di https://console.groq.com/docs/models

GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "2048"))
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.2"))

# ── UI defaults ──────────────────────────────────────────────────────────
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "Indonesia")
DEFAULT_STYLE = os.getenv("DEFAULT_STYLE", "penjelasan bertahap")
DEFAULT_LEVEL = os.getenv("DEFAULT_LEVEL", "menengah")

