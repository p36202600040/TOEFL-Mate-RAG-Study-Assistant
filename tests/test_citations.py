"""
tests/test_citations.py — Unit tests untuk modul prompts, sitasi, dan evaluasi.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.prompts import build_system_prompt, build_generation_prompt
from src.evaluation import (
    extract_cited_pages,
    extract_citations,
    validate_citations_against_contexts,
    compute_recall_at_k,
    compute_precision_at_k,
    compute_citation_accuracy,
    check_out_of_scope,
)
from src.generator import generate_answer


class TestBuildSystemPrompt:
    """Test system prompt generation."""

    def test_default_prompt(self):
        prompt = build_system_prompt()
        assert "TOEFL Mate" in prompt
        assert "Bahasa Indonesia" in prompt
        assert "konteks" in prompt.lower()

    def test_english_language(self):
        prompt = build_system_prompt(language="English")
        assert "English" in prompt

    def test_grounding_rules(self):
        prompt = build_system_prompt()
        # Must contain grounding rules
        assert "tidak ditemukan" in prompt.lower() or "konteks" in prompt.lower()
        assert "sitasi" in prompt.lower() or "Halaman" in prompt

    def test_ai_label_rule(self):
        prompt = build_system_prompt()
        assert "AI" in prompt
        assert "ETS" in prompt


class TestBuildGenerationPrompt:
    """Test generation prompt construction."""

    def test_with_contexts(self):
        contexts = [
            {"text": "TOEFL has four sections.", "page": 5, "source": "book.pdf"},
            {"text": "Reading section tests comprehension.", "page": 10, "source": "book.pdf"},
        ]
        messages = build_generation_prompt("What is TOEFL?", contexts)
        assert len(messages) > 0
        assert messages[-1]["role"] == "user"
        assert "TOEFL" in messages[-1]["content"]
        assert "Halaman 5" in messages[-1]["content"]
        assert "Halaman 10" in messages[-1]["content"]

    def test_no_contexts(self):
        messages = build_generation_prompt("What is TOEFL?", [])
        assert "Tidak ada konteks" in messages[-1]["content"]

    def test_with_chat_history(self):
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        messages = build_generation_prompt("Follow up", [], chat_history=history)
        assert len(messages) >= 3  # history + new message


class TestExtractCitedPages:
    """Test citation extraction."""

    def test_basic_citation(self):
        text = "TOEFL has four sections [Halaman 5]."
        pages = extract_cited_pages(text)
        assert pages == [5]

    def test_multiple_citations(self):
        text = "Reading [Halaman 10] and Listening [Halaman 20] sections."
        pages = extract_cited_pages(text)
        assert pages == [10, 20]

    def test_english_citation(self):
        text = "The test has four sections [Page 15]."
        pages = extract_cited_pages(text)
        assert pages == [15]

    def test_no_citations(self):
        text = "This is a plain text without citations."
        pages = extract_cited_pages(text)
        assert pages == []

    def test_canonical_source_page_citation(self):
        citations = extract_citations("Skor [book.pdf, Halaman 35].")
        assert citations == [{"source": "book.pdf", "page": 35}]

    def test_unicode_bracket_citation(self):
        citations = extract_citations("Skor 【book.pdf, Halaman 35】.")
        assert citations == [{"source": "book.pdf", "page": 35}]

    def test_citation_context_validation_multi_document(self):
        citations = extract_citations("[book.pdf, Halaman 35] [Halaman 70]")
        checked = validate_citations_against_contexts(citations, [
            {"source": "book.pdf", "page": 35},
            {"source": "other.pdf", "page": 70},
        ])
        assert checked[0]["in_retrieved_context"] is True
        assert checked[1]["in_retrieved_context"] is False


class TestMetrics:
    """Test evaluation metrics."""

    def test_recall_at_k_hit(self):
        assert compute_recall_at_k([1, 2, 3, 4, 5], [3], k=5) == 1.0

    def test_recall_at_k_miss(self):
        assert compute_recall_at_k([1, 2, 3, 4, 5], [99], k=5) == 0.0

    def test_recall_at_k_empty_relevant(self):
        assert compute_recall_at_k([1, 2, 3], [], k=5) == 0.0

    def test_precision_at_k(self):
        # 2 out of 5 are relevant
        assert compute_precision_at_k([1, 2, 3, 4, 5], [2, 4], k=5) == 0.4

    def test_precision_at_k_all_relevant(self):
        assert compute_precision_at_k([1, 2, 3], [1, 2, 3, 4, 5], k=3) == 1.0

    def test_citation_accuracy_all_correct(self):
        assert compute_citation_accuracy([5, 10], [5, 10, 15]) == 1.0

    def test_citation_accuracy_partial(self):
        assert compute_citation_accuracy([5, 99], [5, 10]) == 0.5

    def test_citation_accuracy_no_citations(self):
        assert compute_citation_accuracy([], [5, 10]) == 0.0


class TestOutOfScope:
    """Test out-of-scope detection."""

    def test_oos_indonesian(self):
        text = "Maaf, informasi ini tidak ditemukan dalam dokumen sumber."
        assert check_out_of_scope(text) is True

    def test_oos_english(self):
        text = "This information is not found in the source document."
        assert check_out_of_scope(text) is True

    def test_normal_answer(self):
        text = "The TOEFL test has four sections: Reading, Listening, Speaking, and Writing."
        assert check_out_of_scope(text) is False

    def test_partial_oos(self):
        text = "Dokumen tidak membahas topik ini secara spesifik."
        assert check_out_of_scope(text) is True


def test_generation_rate_limit_error_is_sanitized(monkeypatch):
    class FakeCompletions:
        def create(self, **kwargs):
            raise RuntimeError("rate_limit org_private_identifier")

    class FakeClient:
        class chat:
            completions = FakeCompletions()

    monkeypatch.setattr("src.generator.Groq", lambda api_key: FakeClient())
    monkeypatch.setattr("src.generator.os", None, raising=False)
    result = generate_answer("Q", [], model="test-model")
    assert "org_private_identifier" not in result["error"]
    assert "batas permintaan" in result["error"]
