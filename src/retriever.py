"""
src/retriever.py — ChromaDB vector store dan retrieval.

Menggunakan L2 distance secara default. Semakin kecil distance,
semakin mirip vektor. Distance BUKAN probabilitas kebenaran.
"""
from pathlib import Path
import json

import chromadb
from chromadb.config import Settings

import config
from src.embeddings import embed_texts, embed_query


# Glosarium kecil untuk memperkaya query Indonesia terhadap dokumen sumber yang
# mayoritas berbahasa Inggris. Ini bukan jawaban/hardcode halaman; istilah umum
# dipetakan ke padanan yang memang dicari pada seluruh indeks.
INDONESIAN_RETRIEVAL_TERMS = {
    "bagian": "section sections",
    "rentang skor": "score range score scale total score",
    "skor": "score scoring scale",
    "jumlah": "number total",
    "pertanyaan": "question questions",
    "waktu persiapan": "preparation time",
    "waktu berbicara": "response time speaking",
    "berbicara": "speaking",
    "mendengarkan": "listening",
    "membaca": "reading",
    "menulis": "writing",
    "tugas": "task tasks",
    "penilaian": "scoring rating rubric",
    "catatan": "note taking notes",
    "biaya": "registration fee cost",
}


def enrich_query_for_retrieval(query: str) -> str:
    """Tambahkan padanan istilah Inggris bila query tampak berbahasa Indonesia."""
    query_lower = query.lower()
    terms = []
    for indonesian, english in INDONESIAN_RETRIEVAL_TERMS.items():
        if indonesian in query_lower:
            terms.append(english)
    if not terms:
        return query
    return f"{query}\nEnglish retrieval terms: {' '.join(dict.fromkeys(terms))}"


def get_chroma_client(
    persist_dir: str | Path | None = None,
    is_ephemeral: bool = False,
) -> chromadb.ClientAPI:
    """Buat atau buka ChromaDB client (persistent atau in-memory ephemeral)."""
    if is_ephemeral or (persist_dir and str(persist_dir) == ":memory:"):
        return chromadb.EphemeralClient()
    path = str(persist_dir or config.CHROMA_DIR)
    client = chromadb.PersistentClient(path=path)
    return client


def get_or_create_collection(
    client: chromadb.ClientAPI | None = None,
    collection_name: str | None = None,
) -> chromadb.Collection:
    """Get or create ChromaDB collection."""
    if client is None:
        client = get_chroma_client()
    name = collection_name or config.CHROMA_COLLECTION
    collection = client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "l2"},  # L2 distance
    )
    return collection


def collection_exists(client: chromadb.ClientAPI, collection_name: str) -> bool:
    """Cek koleksi tanpa membuat koleksi baru sebagai efek samping."""
    try:
        client.get_collection(collection_name)
        return True
    except Exception:
        return False


def index_compatibility(collection_name: str, dimension: int | None = None) -> str:
    """Periksa manifest bila tersedia; metadata lama yang tidak lengkap tetap UNKNOWN."""
    path = config.CHROMA_MANIFEST_DIR / f"{collection_name}.json"
    if not path.exists():
        return "UNKNOWN"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Manifest indeks tidak dapat dibaca.") from exc
    if manifest.get("collection") != collection_name:
        raise ValueError("Identitas koleksi pada manifest tidak cocok.")
    model = manifest.get("embedding_model")
    if model and model != config.EMBEDDING_MODEL:
        raise ValueError("Model embedding tidak cocok dengan manifest indeks.")
    stored_dimension = manifest.get("embedding_dimension")
    if dimension is not None and stored_dimension is not None and stored_dimension != dimension:
        raise ValueError("Dimensi embedding tidak cocok dengan manifest indeks.")
    return "VERIFIED" if model and stored_dimension is not None and dimension is not None else "UNKNOWN"


def index_chunks(
    chunks: list[dict],
    collection: chromadb.Collection | None = None,
    batch_size: int = 100,
) -> int:
    """
    Index chunks ke ChromaDB.

    Args:
        chunks: List of dicts dengan keys: chunk_id, text, source, page
        collection: ChromaDB collection (opsional, dibuat otomatis)
        batch_size: Jumlah chunk per batch untuk embedding

    Returns:
        Jumlah chunk yang diindeks
    """
    if collection is None:
        collection = get_or_create_collection()

    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["text"] for c in batch]
        ids = [c["chunk_id"] for c in batch]
        metadatas = [
            {"source": c["source"], "page": c["page"], "chunk_id": c["chunk_id"]}
            for c in batch
        ]

        embeddings = embed_texts(texts)

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        total += len(batch)
        print(f"[Retriever] Indexed {total}/{len(chunks)} chunks")

    return total


def retrieve(
    query: str,
    top_k: int | None = None,
    relevance_threshold: float | None = None,
    collection: chromadb.Collection | None = None,
) -> list[dict]:
    """
    Ambil top-k chunk yang relevan untuk query.

    Returns:
        List of dicts:
        - chunk_id: str
        - text: str
        - source: str
        - page: int
        - distance: float  (L2 distance; semakin kecil = semakin mirip)
    """
    if collection is None:
        collection = get_chroma_client().get_collection(config.CHROMA_COLLECTION)

    k = config.TOP_K if top_k is None else top_k
    threshold = config.RELEVANCE_THRESHOLD if relevance_threshold is None else relevance_threshold
    if k <= 0:
        raise ValueError("top_k harus lebih besar dari 0")
    if threshold < 0:
        raise ValueError("relevance_threshold harus >= 0")

    # Pemeriksaan model dilakukan sebelum embedding, dimensi setelahnya.
    index_compatibility(collection.name)
    query_embedding = embed_query(enrich_query_for_retrieval(query))
    index_compatibility(collection.name, len(query_embedding))

    results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

    retrieved = []
    if results and results["ids"] and results["ids"][0]:
        for idx in range(len(results["ids"][0])):
            distance = results["distances"][0][idx]
            # Filter berdasarkan threshold jika diatur
            if distance <= threshold:
                retrieved.append({
                    "chunk_id": results["ids"][0][idx],
                    "text": results["documents"][0][idx],
                    "source": results["metadatas"][0][idx].get("source", ""),
                    "page": results["metadatas"][0][idx].get("page", 0),
                    "distance": distance,
                })

    return retrieved
