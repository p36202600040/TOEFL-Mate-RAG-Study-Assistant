"""Regresi hermetik untuk error generasi dan validasi lokasi sitasi."""
from types import SimpleNamespace

import pytest

from src import generator
from src.evaluation import extract_citations, validate_citations_against_contexts, run_evaluation


def test_constructor_error_does_not_expose_details(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda **kwargs: None)
    monkeypatch.setenv("GROQ_API_KEY", "FAKE_TEST_SECRET")
    def fail(**kwargs):
        raise ValueError("FAKE_TEST_SECRET internal organization")
    monkeypatch.setattr(generator, "Groq", fail)
    result = generator.generate_answer("test", [])
    assert result["error"]
    assert "FAKE_TEST_SECRET" not in result["error"]
    assert "organization" not in result["error"]


def test_empty_provider_response_is_failure(monkeypatch):
    monkeypatch.setattr("dotenv.load_dotenv", lambda **kwargs: None)
    monkeypatch.setenv("GROQ_API_KEY", "fixture")
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=None))])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: response)))
    monkeypatch.setattr(generator, "Groq", lambda **kwargs: client)
    result = generator.generate_answer("test", [])
    assert result["error"] and result["answer"] == ""


def test_zero_width_and_wrong_source():
    citations = extract_citations("[\u200bofficial.pdf, Halaman 35] [other.pdf, Halaman 35]")
    validated = validate_citations_against_contexts(citations, [{"source": "official.pdf", "page": 35}])
    assert [c["in_retrieved_context"] for c in validated] == [True, False]
    assert validated[0]["source"].startswith("\u200b")


def test_empty_dataset_rejected():
    with pytest.raises(ValueError, match="kosong"):
        run_evaluation([])
