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
CHROMA_MANIFEST_DIR = CHROMA_DIR / "manifests"

# ── Retrieval ────────────────────────────────────────────────────────────
TOP_K = int(os.getenv("TOP_K", "5"))
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "1.5"))
# ChromaDB menggunakan L2 distance secara default.
# Semakin kecil nilainya, semakin mirip. Threshold 1.5 bersifat permisif;
# sesuaikan berdasarkan eksperimen.

# ── Groq API ─────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
# Satu-satunya default model. UI, generator, dan evaluasi wajib memakai nilai ini.
# Nama aktual dapat dioverride melalui .env setelah diverifikasi pada akun Groq pengguna.
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()

GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "2048"))
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.2"))

# ── UI defaults ──────────────────────────────────────────────────────────
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "Indonesia")
DEFAULT_STYLE = os.getenv("DEFAULT_STYLE", "penjelasan bertahap")
DEFAULT_LEVEL = os.getenv("DEFAULT_LEVEL", "menengah")


def validate_settings() -> None:
    """Validasi konfigurasi non-rahasia sebelum ingestion/evaluasi dijalankan."""
    if CHUNK_SIZE <= 0:
        raise ValueError("CHUNK_SIZE harus lebih besar dari 0")
    if CHUNK_OVERLAP < 0 or CHUNK_OVERLAP >= CHUNK_SIZE:
        raise ValueError("CHUNK_OVERLAP harus >= 0 dan lebih kecil dari CHUNK_SIZE")
    if TOP_K <= 0:
        raise ValueError("TOP_K harus lebih besar dari 0")
    if RELEVANCE_THRESHOLD < 0:
        raise ValueError("RELEVANCE_THRESHOLD harus >= 0")
    if not EMBEDDING_MODEL.strip():
        raise ValueError("EMBEDDING_MODEL tidak boleh kosong")
    if not GROQ_MODEL:
        raise ValueError("GROQ_MODEL tidak boleh kosong")
