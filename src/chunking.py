from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
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
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Split text into sentences using regex for sentence boundaries
        # Sentences end with ". ", "! ", "? ", or ".\n"
        sentences = re.split(r'(?<=[.!?])\s*(?=[A-Z])|\.\n', text)

        # Filter out empty sentences and clean up whitespace
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return [text.strip()] if text.strip() else []

        # Group sentences into chunks
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk = " ".join(sentences[i:i + self.max_sentences_per_chunk])
            if chunk.strip():
                chunks.append(chunk.strip())

        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if text.strip() == "":
            return []
        return self._split(text.strip(), self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # If no more separators or text is small enough, return as single chunk
        if not remaining_separators:
            return [current_text] if current_text else []

        if len(current_text) <= self.chunk_size:
            return [current_text]

        separator = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Try to split with current separator
        if separator == "":
            # Final fallback: character-level split
            return [current_text] if current_text else []

        if separator not in current_text:
            # Separator not found, try next one
            return self._split(current_text, next_separators)

        # Split by separator
        parts = current_text.split(separator)
        result_chunks: list[str] = []
        current_chunk = ""

        for part in parts:
            # Check if adding this part would exceed chunk_size
            if current_chunk:
                candidate = current_chunk + separator + part
            else:
                candidate = part

            if len(candidate) <= self.chunk_size:
                current_chunk = candidate
            else:
                # Current chunk is full, save it and start new one
                if current_chunk:
                    result_chunks.append(current_chunk)
                # If single part exceeds chunk_size, recursively split with next separator
                if len(part) > self.chunk_size:
                    sub_chunks = self._split(part, next_separators)
                    result_chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = part

        # Don't forget the last chunk
        if current_chunk:
            result_chunks.append(current_chunk)

        # If we only got one chunk that's too big, try next separator
        if len(result_chunks) == 1 and len(result_chunks[0]) > self.chunk_size and next_separators:
            return self._split(current_text, next_separators)

        return result_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_product = _dot(vec_a, vec_b)
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(y * y for y in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        results = {}

        # Fixed size chunking
        fixed_chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=50)
        fixed_chunks = fixed_chunker.chunk(text)
        results['fixed_size'] = {
            'count': len(fixed_chunks),
            'avg_length': sum(len(c) for c in fixed_chunks) / len(fixed_chunks) if fixed_chunks else 0,
            'chunks': fixed_chunks
        }

        # Sentence-based chunking
        sentence_chunker = SentenceChunker(max_sentences_per_chunk=3)
        sentence_chunks = sentence_chunker.chunk(text)
        results['by_sentences'] = {
            'count': len(sentence_chunks),
            'avg_length': sum(len(c) for c in sentence_chunks) / len(sentence_chunks) if sentence_chunks else 0,
            'chunks': sentence_chunks
        }

        # Recursive chunking
        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)
        recursive_chunks = recursive_chunker.chunk(text)
        results['recursive'] = {
            'count': len(recursive_chunks),
            'avg_length': sum(len(c) for c in recursive_chunks) / len(recursive_chunks) if recursive_chunks else 0,
            'chunks': recursive_chunks
        }

        return results
