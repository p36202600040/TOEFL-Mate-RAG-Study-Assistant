"""
src/embeddings.py — Embedding lokal menggunakan Sentence Transformers.

Model di-load sekali dan digunakan ulang. Tidak ada data yang dikirim ke
layanan eksternal untuk embedding.
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

import config


@lru_cache(maxsize=1)
def get_model(model_name: str | None = None) -> SentenceTransformer:
    """Load model embedding (cached)."""
    name = model_name or config.EMBEDDING_MODEL
    print(f"[Embeddings] Loading model: {name}")
    model = SentenceTransformer(name)
    dim = (
        model.get_embedding_dimension()
        if hasattr(model, "get_embedding_dimension")
        else model.get_sentence_embedding_dimension()
    )
    print(f"[Embeddings] Model loaded: {name}, dim={dim}")
    return model


def embed_texts(texts: list[str], model_name: str | None = None) -> list[list[float]]:
    """
    Embed daftar teks menggunakan sentence-transformers.

    Returns:
        List of embedding vectors (list of floats).
    """
    if not texts:
        return []
    model = get_model(model_name)
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings.tolist()


def embed_query(query: str, model_name: str | None = None) -> list[float]:
    """Embed satu query."""
    model = get_model(model_name)
    embedding = model.encode(query, convert_to_numpy=True)
    return embedding.tolist()
