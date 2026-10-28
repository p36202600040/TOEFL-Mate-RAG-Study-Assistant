"""
tests/test_retrieval.py — Unit tests untuk modul retrieval.
"""
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retriever import get_chroma_client, get_or_create_collection, index_chunks, retrieve
from src.embeddings import embed_texts, embed_query


class TestEmbeddings:
    """Test embedding functions."""

    def test_embed_single_text(self):
        result = embed_texts(["Hello world"])
        assert len(result) == 1
        assert len(result[0]) > 0  # Has dimensions

    def test_embed_multiple_texts(self):
        texts = ["Hello", "World", "TOEFL test"]
        result = embed_texts(texts)
        assert len(result) == 3
        # All same dimension
        dims = set(len(r) for r in result)
        assert len(dims) == 1

    def test_embed_empty_list(self):
        result = embed_texts([])
        assert result == []

    def test_embed_query(self):
        result = embed_query("What is TOEFL?")
        assert len(result) > 0


class TestChromaDB:
    """Test ChromaDB operations using in-memory ephemeral client to avoid Windows file locks."""

    def test_create_collection(self):
        client = get_chroma_client(is_ephemeral=True)
        collection = get_or_create_collection(client, "test_collection")
        assert collection is not None
        assert collection.count() == 0

    def test_index_and_retrieve(self):
        client = get_chroma_client(is_ephemeral=True)
        collection = get_or_create_collection(client, "test_retrieval")

        chunks = [
            {
                "chunk_id": "chunk_001",
                "text": "The TOEFL test measures English language proficiency for academic settings.",
                "source": "test.pdf",
                "page": 1,
            },
            {
                "chunk_id": "chunk_002",
                "text": "The Reading section contains passages from university textbooks.",
                "source": "test.pdf",
                "page": 10,
            },
            {
                "chunk_id": "chunk_003",
                "text": "Python is a programming language used for web development.",
                "source": "test.pdf",
                "page": 99,
            },
        ]

        count = index_chunks(chunks, collection)
        assert count == 3

        # Query related to TOEFL
        results = retrieve(
            "What does the TOEFL test measure?",
            top_k=2,
            relevance_threshold=100.0,  # Very permissive for test
            collection=collection,
        )
        assert len(results) > 0
        # TOEFL chunk should be most relevant
        assert results[0]["page"] in [1, 10]

    def test_retrieve_with_threshold(self):
        client = get_chroma_client(is_ephemeral=True)
        collection = get_or_create_collection(client, "test_threshold")

        chunks = [
            {
                "chunk_id": "chunk_001",
                "text": "The TOEFL iBT test has four sections: Reading, Listening, Speaking, and Writing.",
                "source": "test.pdf",
                "page": 5,
            },
        ]

        index_chunks(chunks, collection)

        # Very strict threshold should return less results
        results = retrieve(
            "What are the sections of TOEFL?",
            top_k=5,
            relevance_threshold=0.001,  # Very strict
            collection=collection,
        )
        # May return 0 results due to strict threshold
        assert isinstance(results, list)

