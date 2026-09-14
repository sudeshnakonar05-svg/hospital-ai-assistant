"""Unit tests for text chunking."""

import pytest

from app.services.chunking import chunk_text


def test_empty_text_returns_no_chunks() -> None:
    """Whitespace-only input produces no chunks."""
    assert chunk_text("   \n  ") == []


def test_short_text_is_one_chunk() -> None:
    """Text smaller than chunk_size stays in a single chunk."""
    chunks = chunk_text("Visiting hours are 10 AM to 8 PM.", chunk_size=800, chunk_overlap=50)
    assert len(chunks) == 1
    assert chunks[0].index == 0
    assert "Visiting hours" in chunks[0].content


def test_long_text_is_split_with_overlap() -> None:
    """Long input is split into overlapping pieces."""
    paragraph = "Cardiology clinic. " * 80
    chunks = chunk_text(paragraph, chunk_size=120, chunk_overlap=20)
    assert len(chunks) > 1
    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))
    assert all(len(chunk.content) <= 140 for chunk in chunks)


def test_overlap_must_be_smaller_than_size() -> None:
    """Invalid overlap is rejected."""
    with pytest.raises(ValueError):
        chunk_text("hello world", chunk_size=10, chunk_overlap=10)
