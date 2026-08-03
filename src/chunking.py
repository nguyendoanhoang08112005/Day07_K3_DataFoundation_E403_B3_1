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
        
        # Split on ". ", "! ", "? " or ".\n", retaining the punctuation inside the split sentences.
        tokens = re.split(r'(\.\n|\. |! |\? )', text)
        sentences = []
        i = 0
        while i < len(tokens):
            s = tokens[i]
            if i + 1 < len(tokens):
                s += tokens[i + 1]
                i += 2
            else:
                i += 1
            s_stripped = s.strip()
            if s_stripped:
                sentences.append(s_stripped)
        
        chunks = []
        for j in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_group = sentences[j : j + self.max_sentences_per_chunk]
            chunks.append(" ".join(chunk_group))
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
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            # Fallback: slice into chunk_size pieces
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]

        if sep == "":
            splits = list(current_text)
        else:
            splits = current_text.split(sep)

        final_splits = []
        for split in splits:
            if len(split) > self.chunk_size:
                final_splits.extend(self._split(split, next_seps))
            else:
                final_splits.append(split)

        chunks = []
        current_chunk = []
        current_len = 0
        sep_len = len(sep) if sep != "" else 0

        for split in final_splits:
            split_len = len(split)
            added_len = split_len + (sep_len if current_chunk else 0)

            if current_len + added_len <= self.chunk_size:
                current_chunk.append(split)
                current_len += added_len
            else:
                if current_chunk:
                    chunks.append(sep.join(current_chunk))
                current_chunk = [split]
                current_len = split_len

        if current_chunk:
            chunks.append(sep.join(current_chunk))

        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_prod = _dot(vec_a, vec_b)
    mag_a = math.sqrt(_dot(vec_a, vec_a))
    mag_b = math.sqrt(_dot(vec_b, vec_b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot_prod / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_size_chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=max(0, chunk_size // 10))
        sentence_chunker = SentenceChunker(max_sentences_per_chunk=max(1, chunk_size // 100))
        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)

        fs_chunks = fixed_size_chunker.chunk(text)
        bs_chunks = sentence_chunker.chunk(text)
        rec_chunks = recursive_chunker.chunk(text)

        def _stats(chunks):
            count = len(chunks)
            avg_len = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            return {
                "count": count,
                "avg_length": avg_len,
                "chunks": chunks
            }

        return {
            "fixed_size": _stats(fs_chunks),
            "by_sentences": _stats(bs_chunks),
            "recursive": _stats(rec_chunks)
        }



class CustomChunker:
    """
    Custom Chunker for University Regulations that splits text by Markdown headings (#, ##, ###).
    It groups content under their respective headings to preserve section context.
    If a section's length exceeds chunk_size, it splits it by paragraphs or sentences.
    """

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        
        # Split text into sections based on headings
        lines = text.splitlines()
        sections = []
        current_header = ""
        current_section_lines = []
        
        for line in lines:
            if line.strip().startswith("#"):
                if current_section_lines:
                    sections.append((current_header, "\n".join(current_section_lines)))
                current_header = line.strip()
                current_section_lines = [line]
            else:
                current_section_lines.append(line)
        
        if current_section_lines:
            sections.append((current_header, "\n".join(current_section_lines)))
            
        chunks = []
        for header, content in sections:
            content = content.strip()
            if not content:
                continue
            
            if len(content) <= self.chunk_size:
                chunks.append(content)
            else:
                # Fallback: split by double newline (paragraphs)
                paragraphs = content.split("\n\n")
                current_chunk = []
                current_len = 0
                for para in paragraphs:
                    para = para.strip()
                    if not para:
                        continue
                    if len(para) > self.chunk_size:
                        # If a single paragraph is too large, just add it or split by characters
                        if current_chunk:
                            chunks.append("\n\n".join(current_chunk))
                            current_chunk = []
                            current_len = 0
                        chunks.append(para)
                    elif current_len + len(para) + 2 <= self.chunk_size:
                        current_chunk.append(para)
                        current_len += len(para) + 2
                    else:
                        if current_chunk:
                            chunks.append("\n\n".join(current_chunk))
                        current_chunk = [para]
                        current_len = len(para)
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    
        return chunks

