"""
src/ingestion.py — Ekstraksi teks PDF, pembersihan, dan chunking.

Menggunakan PyMuPDF (fitz) untuk mempertahankan metadata nomor halaman.
Nomor halaman mengikuti indeks PDF 1-based (halaman pertama = 1).
Nomor halaman PDF TIDAK selalu sama dengan nomor cetak buku.
"""
import re
import unicodedata
import hashlib
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


def extract_pages(pdf_path: str | Path) -> list[dict]:
    """
    Ekstrak teks dari setiap halaman PDF.

    Returns:
        List of dicts: {"page": int (1-based), "text": str, "source": str}

    Raises:
        FileNotFoundError: jika file tidak ditemukan
        ValueError: jika PDF tidak mengandung teks
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF tidak ditemukan: {pdf_path}")

    doc = fitz.open(str(pdf_path))
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text and text.strip():
            pages.append({
                "page": i + 1,  # 1-based
                "text": text.strip(),
                "source": pdf_path.name,
            })
    doc.close()

    if not pages:
        raise ValueError(
            f"PDF tidak mengandung teks yang bisa diekstrak: {pdf_path.name}. "
            "Pastikan PDF bukan scan gambar tanpa OCR."
        )

    return pages


def clean_text(text: str) -> str:
    """Pembersihan dasar teks hasil ekstraksi PDF dan normalisasi Unicode."""
    # Normalisasi unicode untuk mengurai ligatures seperti fi (\ufb01), fl (\ufb02)
    text = unicodedata.normalize("NFKD", text)
    # Ganti multiple whitespace/newline dengan single space
    text = re.sub(r"\s+", " ", text)
    # Hapus karakter kontrol kecuali newline
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list[str]:
    """
    Bagi teks menjadi chunk dengan overlap.

    Args:
        text: Teks yang akan di-chunk
        chunk_size: Jumlah karakter per chunk
        chunk_overlap: Jumlah karakter overlap antar chunk

    Returns:
        List of string chunks
    """
    if not text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size harus > 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap harus >= 0")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap harus < chunk_size")

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - chunk_overlap

    return chunks


def create_chunks_from_pages(
    pages: list[dict],
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    start_id: int = 0,
    id_prefix: str = "chunk",
) -> list[dict]:
    """
    Buat chunk dari halaman-halaman PDF dengan metadata.

    Returns:
        List of dicts dengan keys:
        - chunk_id: str
        - text: str
        - source: str
        - page: int
    """
    all_chunks = []
    chunk_counter = start_id

    for page_data in pages:
        cleaned = clean_text(page_data["text"])
        chunks = chunk_text(cleaned, chunk_size, chunk_overlap)

        for chunk_text_item in chunks:
            all_chunks.append({
                "chunk_id": f"{id_prefix}_{chunk_counter:05d}",
                "text": chunk_text_item,
                "source": page_data["source"],
                "page": page_data["page"],
            })
            chunk_counter += 1

    return all_chunks


def document_sha256(pdf_path: str | Path) -> str:
    """Kembalikan hash SHA-256 dokumen tanpa menyimpan isi dokumen pada manifest."""
    digest = hashlib.sha256()
    with open(pdf_path, "rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
