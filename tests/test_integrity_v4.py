"""Regresi integritas tanpa API atau indeks proyek."""
import json
from types import SimpleNamespace

import pytest

from src import evaluation, retriever


def test_source_aware_metrics_and_unknown_legacy(monkeypatch):
    monkeypatch.setattr(evaluation, "retrieve", lambda *args, **kwargs: [
        {"source": "other.pdf", "page": 35, "chunk_id": "c", "distance": 0.1}
    ])
    monkeypatch.setattr(evaluation, "generate_answer", lambda *args, **kwargs: {
        "answer": "[other.pdf, Halaman 35]", "model": "effective", "latency_seconds": 0.1, "error": None
    })
    summary = evaluation.run_evaluation([
        {"id": "explicit", "question": "a", "relevant_sources": [{"source": "official.pdf", "page": 35}]},
        {"id": "legacy", "question": "b", "relevant_pages": [35]},
    ])
    assert summary["results"][0]["recall_at_k"] == 0
    assert summary["results"][0]["citation_accuracy"] == 0
    assert summary["results"][1]["label_status"] == "SOURCE_UNKNOWN"
    assert summary["metrics"]["recall_at_k"]["n_samples"] == 1
    assert summary["metrics"]["citation_location_validity"]["value"] == 1
    assert summary["results"][0]["effective_model"] == "effective"


def test_manifest_model_and_dimension_mismatch(tmp_path, monkeypatch):
    monkeypatch.setattr(retriever.config, "CHROMA_MANIFEST_DIR", tmp_path)
    monkeypatch.setattr(retriever.config, "EMBEDDING_MODEL", "model-a")
    assert retriever.index_compatibility("fixture", 3) == "UNKNOWN"
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps({"collection": "fixture", "embedding_model": "model-b", "embedding_dimension": 3}))
    with pytest.raises(ValueError, match="Model"):
        retriever.index_compatibility("fixture", 3)
    path.write_text(json.dumps({"collection": "fixture", "embedding_model": "model-a", "embedding_dimension": 4}))
    with pytest.raises(ValueError, match="Dimensi"):
        retriever.index_compatibility("fixture", 3)
    assert retriever.index_compatibility("fixture", 4) == "VERIFIED"


def test_retrieval_does_not_fallback_after_query_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(retriever.config, "CHROMA_MANIFEST_DIR", tmp_path)
    monkeypatch.setattr(retriever, "embed_query", lambda query: [0.0, 0.0])
    def fail(**kwargs):
        raise RuntimeError("query failed")
    collection = SimpleNamespace(name="fixture", query=fail)
    with pytest.raises(RuntimeError, match="query failed"):
        retriever.retrieve("test", collection=collection)


def test_app_ambiguous_followup_requests_clarification(monkeypatch):
    from streamlit.testing.v1 import AppTest
    import config
    monkeypatch.setattr(config, "GROQ_API_KEY", "fixture")
    monkeypatch.setattr(retriever, "get_chroma_client", lambda: SimpleNamespace(
        get_collection=lambda name: SimpleNamespace(name=name, count=lambda: 1)))
    monkeypatch.setattr(retriever, "retrieve", lambda *args, **kwargs: pytest.fail("Retrieval tidak boleh dipanggil"))
    app = AppTest.from_file("app.py", default_timeout=30).run()
    # app memuat ulang config, sehingga status key disediakan melalui environment fixture.
    monkeypatch.setenv("GROQ_API_KEY", "fixture")
    monkeypatch.setattr("dotenv.load_dotenv", lambda **kwargs: None)
    app.run()
    app.chat_input[0].set_value("Jelaskan bagian kedua tadi.").run()
    assert not app.exception
    assert "Bagian yang mana?" in app.session_state["messages"][-1]["content"]
