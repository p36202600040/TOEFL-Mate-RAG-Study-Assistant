"""Test build kandidat tidak menghapus koleksi aktif."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.retriever import get_chroma_client, get_or_create_collection
from scripts.ingest_pdf import build_candidate


def test_failed_candidate_build_preserves_active_collection(tmp_path):
    client = get_chroma_client(persist_dir=tmp_path)
    active = get_or_create_collection(client, "active_index")
    active.add(
        ids=["existing"],
        embeddings=[[0.0, 0.0]],
        documents=["existing data"],
        metadatas=[{"source": "existing.pdf", "page": 1, "chunk_id": "existing"}],
    )

    with pytest.raises(FileNotFoundError):
        build_candidate([tmp_path / "missing.pdf"], client, "candidate_index")

    assert client.get_collection("active_index").count() == 1
