"""Test ringkasan evaluasi untuk kegagalan generation tanpa request API."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import evaluation


def test_evaluation_records_generation_failure(monkeypatch):
    monkeypatch.setattr(evaluation, "retrieve", lambda *args, **kwargs: [
        {"page": 1, "source": "book.pdf", "chunk_id": "c1", "text": "context", "distance": 0.1}
    ])
    monkeypatch.setattr(evaluation, "generate_answer", lambda *args, **kwargs: {
        "answer": "", "model": "test", "latency_seconds": 0.0, "error": "API unavailable"
    })
    summary = evaluation.run_evaluation([{
        "id": "q1", "category": "factual", "question": "question", "relevant_pages": [1]
    }])

    item = summary["results"][0]
    assert item["status"] == "GENERATION_FAILED"
    assert item["answer_correctness"] == "NOT_RATED"
    assert summary["run_status"] == "PARTIAL_OR_NOT_RUN"
    assert summary["metrics"]["citation_accuracy_micro"]["value"] == "NOT_RUN"
