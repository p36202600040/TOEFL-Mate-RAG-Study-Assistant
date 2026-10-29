"""
src/retriever.py — ChromaDB vector store dan retrieval.

Menggunakan L2 distance secara default. Semakin kecil distance,
semakin mirip vektor. Distance BUKAN probabilitas kebenaran.
"""
from pathlib import Path

import chromadb
from chromadb.config import Settings

import config
from src.embeddings import embed_texts, embed_query


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
        collection = get_or_create_collection()

    k = top_k or config.TOP_K
    threshold = relevance_threshold or config.RELEVANCE_THRESHOLD

    query_embedding = embed_query(query)

    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        # Fallback jika collection handle sudah stale (misal setelah re-ingestion)
        collection = get_or_create_collection()
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

