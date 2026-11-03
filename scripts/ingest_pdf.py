"""
scripts/ingest_pdf.py — Skrip ingestion PDF ke ChromaDB.

Penggunaan:
    python scripts/ingest_pdf.py                    # Semua PDF di data/
    python scripts/ingest_pdf.py data/mybook.pdf    # Satu file spesifik

Nomor halaman mengikuti indeks PDF 1-based.
"""
import sys
import time
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Tambahkan project root ke path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from src.ingestion import extract_pages, create_chunks_from_pages, document_sha256
from src.retriever import get_chroma_client, get_or_create_collection, index_chunks
from src.embeddings import get_model


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


def write_manifest(collection_name: str, documents: list[dict], chunk_count: int) -> Path:
    """Simpan metadata build yang dapat diaudit tanpa menyimpan teks atau rahasia."""
    config.CHROMA_MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 2,
        "collection": collection_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "embedding_model": config.EMBEDDING_MODEL,
        "embedding_dimension": get_model().get_sentence_embedding_dimension(),
        "chunk_size": config.CHUNK_SIZE,
        "chunk_overlap": config.CHUNK_OVERLAP,
        "chunk_count": chunk_count,
        "documents": documents,
    }
    path = config.CHROMA_MANIFEST_DIR / f"{collection_name}.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_candidate(pdf_paths: list[Path], client, collection_name: str) -> tuple[int, list[dict]]:
    """Bangun koleksi kandidat; koleksi aktif tidak disentuh oleh fungsi ini."""
    collection = get_or_create_collection(client, collection_name)
    total_chunks = 0
    current_start_id = 0
    documents = []
    for pdf_path in pdf_paths:
        indexed = ingest_pdf(pdf_path, collection, start_id=current_start_id)
        total_chunks += indexed
        current_start_id += indexed
        documents.append({
            "source": pdf_path.name,
            "sha256": document_sha256(pdf_path),
        })
    if total_chunks <= 0 or collection.count() != total_chunks:
        raise RuntimeError("Verifikasi koleksi kandidat gagal: jumlah chunk tidak konsisten")
    return total_chunks, documents


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
        return 1

    missing_paths = [p for p in pdf_paths if not p.exists()]
    if missing_paths:
        for path in missing_paths:
            print(f"[Ingest] ERROR: File tidak ditemukan — {path}")
        print("[Ingest] Indeks aktif tidak diubah.")
        return 1

    try:
        config.validate_settings()
    except ValueError as error:
        print(f"[Ingest] ERROR konfigurasi: {error}")
        return 1

    print(f"[Ingest] Ditemukan {len(pdf_paths)} file PDF:")
    for p in pdf_paths:
        print(f"  - {p.name}")
    print(f"[Ingest] Konfigurasi:")
    print(f"  - Chunk size: {config.CHUNK_SIZE}")
    print(f"  - Chunk overlap: {config.CHUNK_OVERLAP}")
    print(f"  - Embedding model: {config.EMBEDDING_MODEL}")
    print(f"  - ChromaDB dir: {config.CHROMA_DIR}")
    print(f"  - Collection: {config.CHROMA_COLLECTION}")

    client = get_chroma_client()
    candidate_name = f"{config.CHROMA_COLLECTION}_candidate_{uuid.uuid4().hex[:8]}"
    print(f"[Ingest] Membangun koleksi kandidat: {candidate_name}")
    try:
        total_chunks, documents = build_candidate(pdf_paths, client, candidate_name)
        manifest_path = write_manifest(candidate_name, documents, total_chunks)
    except Exception as error:
        print(f"[Ingest] ERROR build kandidat: {error}")
        try:
            client.delete_collection(candidate_name)
        except Exception:
            pass
        print("[Ingest] Indeks aktif tidak diubah.")
        return 1

    elapsed = time.time() - start_time
    print(f"\n[Ingest] KANDIDAT BERHASIL: {total_chunks} chunks dari {len(pdf_paths)} dokumen dalam {elapsed:.1f} detik")
    print(f"[Ingest] Manifest: {manifest_path}")
    print(
        "[Ingest] Koleksi aktif tidak diubah otomatis. Untuk mengaktifkan kandidat, "
        f"atur CHROMA_COLLECTION={candidate_name} di .env setelah verifikasi."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
