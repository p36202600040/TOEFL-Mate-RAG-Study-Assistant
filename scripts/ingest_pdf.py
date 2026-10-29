"""
scripts/ingest_pdf.py — Skrip ingestion PDF ke ChromaDB.

Penggunaan:
    python scripts/ingest_pdf.py                    # Semua PDF di data/
    python scripts/ingest_pdf.py data/mybook.pdf    # Satu file spesifik

Nomor halaman mengikuti indeks PDF 1-based.
"""
import sys
import time
from pathlib import Path

# Tambahkan project root ke path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.ingestion import extract_pages, create_chunks_from_pages
from src.retriever import get_chroma_client, get_or_create_collection, index_chunks


def ingest_pdf(pdf_path: Path, collection, start_id: int = 0) -> int:
    """Ingest satu file PDF ke collection yang diberikan. Returns jumlah chunk yang diindeks."""
    print(f"\n{'='*60}")
    print(f"[Ingest] Memproses: {pdf_path.name}")
    print(f"{'='*60}")

    # Ekstrak halaman
    print("[Ingest] Mengekstrak teks dari PDF...")
    pages = extract_pages(pdf_path)
    print(f"[Ingest] Diekstrak: {len(pages)} halaman dengan teks")

    # Buat chunks
    print(f"[Ingest] Membuat chunks (size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP})...")
    # Buat prefix unik dari nama file
    safe_prefix = "".join(c for c in pdf_path.stem[:8] if c.isalnum()).lower() or "doc"
    chunks = create_chunks_from_pages(
        pages,
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        start_id=start_id,
        id_prefix=safe_prefix,
    )
    print(f"[Ingest] Dibuat: {len(chunks)} chunks")

    # Index ke ChromaDB
    print(f"[Ingest] Mengindex ke ChromaDB collection '{collection.name}'...")
    count = index_chunks(chunks, collection)

    print(f"[Ingest] Selesai: {count} chunks berhasil diindex untuk '{pdf_path.name}'")
    return count


def main():
    start_time = time.time()

    if len(sys.argv) > 1:
        # File spesifik
        pdf_paths = [Path(sys.argv[1])]
    else:
        # Semua PDF di data/
        pdf_paths = sorted(list(config.DATA_DIR.glob("*.pdf")))

    if not pdf_paths:
        print("[Ingest] ERROR: Tidak ada file PDF ditemukan.")
        print(f"[Ingest] Letakkan file PDF di folder: {config.DATA_DIR}")
        sys.exit(1)

    print(f"[Ingest] Ditemukan {len(pdf_paths)} file PDF:")
    for p in pdf_paths:
        print(f"  - {p.name}")
    print(f"[Ingest] Konfigurasi:")
    print(f"  - Chunk size: {config.CHUNK_SIZE}")
    print(f"  - Chunk overlap: {config.CHUNK_OVERLAP}")
    print(f"  - Embedding model: {config.EMBEDDING_MODEL}")
    print(f"  - ChromaDB dir: {config.CHROMA_DIR}")
    print(f"  - Collection: {config.CHROMA_COLLECTION}")

    # Reset collection satu kali di awal untuk rebuild bersih multi-dokumen
    client = get_chroma_client()
    try:
        client.delete_collection(config.CHROMA_COLLECTION)
        print("[Ingest] Collection lama dihapus untuk fresh multi-document build")
    except Exception:
        pass

    collection = get_or_create_collection(client)

    total_chunks = 0
    current_start_id = 0
    for pdf_path in pdf_paths:
        if not pdf_path.exists():
            print(f"[Ingest] SKIP: File tidak ditemukan — {pdf_path}")
            continue
        try:
            indexed = ingest_pdf(pdf_path, collection, start_id=current_start_id)
            total_chunks += indexed
            current_start_id += indexed
        except Exception as e:
            print(f"[Ingest] ERROR pada {pdf_path.name}: {e}")

    elapsed = time.time() - start_time
    print(f"\n[Ingest] TOTAL KESELURUHAN: {total_chunks} chunks dari {len(pdf_paths)} dokumen diindex dalam {elapsed:.1f} detik")


if __name__ == "__main__":
    main()

