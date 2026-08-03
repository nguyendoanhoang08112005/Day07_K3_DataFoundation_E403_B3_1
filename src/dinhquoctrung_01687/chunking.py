from __future__ import annotations

import math
import re
from collections.abc import Iterable


class FixedSizeChunker:
    """Split text into fixed-size chunks with optional character overlap."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap < 0:
            raise ValueError("overlap must be non-negative")
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            piece = text[start : start + self.chunk_size]
            if piece:
                chunks.append(piece)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """Group sentence-delimited text into chunks containing at most N sentences."""

    _SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])(?:[ \t]+|\n+)")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        # Keep sentence-ending punctuation by splitting *after* . ! or ?.
        sentences = [
            re.sub(r"\s+", " ", sentence).strip()
            for sentence in self._SENTENCE_BOUNDARY.split(text.strip())
            if sentence.strip()
        ]

        return [
            " ".join(sentences[index : index + self.max_sentences_per_chunk])
            for index in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """Recursively split text using separators ordered from coarse to fine."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self,
        separators: list[str] | None = None,
        chunk_size: int = 500,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        self.separators = (
            list(self.DEFAULT_SEPARATORS)
            if separators is None
            else list(separators)
        )
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return [chunk for chunk in self._split(text, self.separators) if chunk]

    def _split(
        self,
        current_text: str,
        remaining_separators: list[str],
    ) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return self._hard_split(current_text)

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]
        if separator == "":
            return self._hard_split(current_text)

        raw_parts = current_text.split(separator)
        if len(raw_parts) == 1:
            return self._split(current_text, next_separators)

        # Reattach separators so concatenating the chunks reproduces the input.
        units = [
            part + (separator if index < len(raw_parts) - 1 else "")
            for index, part in enumerate(raw_parts)
        ]
        return self._merge_or_recurse(units, next_separators)

    def _merge_or_recurse(
        self,
        units: Iterable[str],
        next_separators: list[str],
    ) -> list[str]:
        chunks: list[str] = []
        current = ""

        def flush() -> None:
            nonlocal current
            if current:
                chunks.append(current)
                current = ""

        for unit in units:
            if not unit:
                continue
            if len(unit) > self.chunk_size:
                flush()
                chunks.extend(self._split(unit, next_separators))
                continue

            if not current or len(current) + len(unit) <= self.chunk_size:
                current += unit
            else:
                flush()
                current = unit

        flush()
        return chunks

    def _hard_split(self, text: str) -> list[str]:
        return [
            text[start : start + self.chunk_size]
            for start in range(0, len(text), self.chunk_size)
            if text[start : start + self.chunk_size]
        ]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Return cosine similarity, or 0.0 when either vector has zero magnitude."""
    if len(vec_a) != len(vec_b):
        raise ValueError("vectors must have the same dimensionality")

    magnitude_a = math.sqrt(sum(value * value for value in vec_a))
    magnitude_b = math.sqrt(sum(value * value for value in vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and return comparable statistics."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")

        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict[str, dict] = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": (
                    sum(len(chunk) for chunk in chunks) / len(chunks)
                    if chunks
                    else 0.0
                ),
                "min_length": min((len(chunk) for chunk in chunks), default=0),
                "max_length": max((len(chunk) for chunk in chunks), default=0),
                "chunks": chunks,
            }
        return comparison
