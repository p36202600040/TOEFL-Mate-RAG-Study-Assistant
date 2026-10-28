"""
tests/test_ingestion.py — Unit tests untuk modul ingestion.
"""
import sys
import os
import tempfile
from pathlib import Path

import pytest

# Tambahkan project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion import extract_pages, clean_text, chunk_text, create_chunks_from_pages


class TestCleanText:
    """Test pembersihan teks."""

    def test_multiple_spaces(self):
        result = clean_text("hello    world")
        assert result == "hello world"

    def test_multiple_newlines(self):
        result = clean_text("hello\n\n\nworld")
        assert result == "hello world"

    def test_control_characters(self):
        result = clean_text("hello\x00world")
        assert result == "helloworld"

    def test_empty_string(self):
        result = clean_text("")
        assert result == ""

    def test_whitespace_only(self):
        result = clean_text("   \n\t  ")
        assert result == ""

    def test_preserves_normal_text(self):
        result = clean_text("The TOEFL test measures English proficiency.")
        assert result == "The TOEFL test measures English proficiency."


class TestChunkText:
    """Test chunking teks."""

    def test_basic_chunking(self):
        text = "a" * 1000
        chunks = chunk_text(text, chunk_size=500, chunk_overlap=100)
        assert len(chunks) >= 2

    def test_small_text(self):
        text = "hello world"
        chunks = chunk_text(text, chunk_size=500, chunk_overlap=100)
        assert len(chunks) == 1
        assert chunks[0] == "hello world"

    def test_empty_text(self):
        chunks = chunk_text("", chunk_size=500, chunk_overlap=100)
        assert chunks == []

    def test_overlap_works(self):
        text = "ABCDE" * 100  # 500 chars
        chunks = chunk_text(text, chunk_size=200, chunk_overlap=50)
        # With overlap, chunks should share some content
        assert len(chunks) >= 3

    def test_invalid_chunk_size(self):
        with pytest.raises(ValueError):
            chunk_text("hello", chunk_size=0, chunk_overlap=0)

    def test_overlap_too_large(self):
        with pytest.raises(ValueError):
            chunk_text("hello", chunk_size=100, chunk_overlap=100)

    def test_negative_overlap(self):
        with pytest.raises(ValueError):
            chunk_text("hello", chunk_size=100, chunk_overlap=-1)


class TestExtractPages:
    """Test ekstraksi PDF."""

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            extract_pages("/nonexistent/file.pdf")

    def test_real_pdf_if_available(self):
        """Test dengan PDF asli jika tersedia."""
        pdf_path = Path(__file__).resolve().parent.parent / "data" / "eBook_TOEFL_Official_Guide_4e.pdf"
        if not pdf_path.exists():
            pytest.skip("PDF not available in data/ directory")

        pages = extract_pages(pdf_path)
        assert len(pages) > 0
        assert all("page" in p for p in pages)
        assert all("text" in p for p in pages)
        assert all("source" in p for p in pages)
        assert all(p["page"] >= 1 for p in pages)  # 1-based


class TestCreateChunksFromPages:
    """Test pembuatan chunks dari pages."""

    def test_basic(self):
        pages = [
            {"page": 1, "text": "Hello world " * 100, "source": "test.pdf"},
            {"page": 2, "text": "Foo bar " * 100, "source": "test.pdf"},
        ]
        chunks = create_chunks_from_pages(pages, chunk_size=200, chunk_overlap=50)
        assert len(chunks) > 0
        assert all("chunk_id" in c for c in chunks)
        assert all("text" in c for c in chunks)
        assert all("page" in c for c in chunks)
        assert all("source" in c for c in chunks)

    def test_metadata_preserved(self):
        pages = [
            {"page": 42, "text": "Some text here", "source": "book.pdf"},
        ]
        chunks = create_chunks_from_pages(pages, chunk_size=500, chunk_overlap=100)
        assert len(chunks) == 1
        assert chunks[0]["page"] == 42
        assert chunks[0]["source"] == "book.pdf"

    def test_chunk_ids_unique(self):
        pages = [
            {"page": 1, "text": "A" * 1000, "source": "test.pdf"},
            {"page": 2, "text": "B" * 1000, "source": "test.pdf"},
        ]
        chunks = create_chunks_from_pages(pages, chunk_size=200, chunk_overlap=50)
        ids = [c["chunk_id"] for c in chunks]
        assert len(ids) == len(set(ids))  # All unique

    def test_empty_pages(self):
        chunks = create_chunks_from_pages([], chunk_size=500, chunk_overlap=100)
        assert chunks == []

