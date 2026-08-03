from __future__ import annotations

import re

from .chunking import RecursiveChunker


class HeadingSectionChunker:
    """Split Markdown by headings and recursively split oversized sections.

    This strategy is designed for university policies, handbooks and FAQs where
    headings often encode the semantic unit users search for.
    """

    HEADING_PATTERN = re.compile(r"^#{1,6}\s+\S", re.MULTILINE)

    def __init__(self, max_chars: int = 900) -> None:
        if max_chars <= 0:
            raise ValueError("max_chars must be greater than 0")
        self.max_chars = max_chars
        self._fallback = RecursiveChunker(chunk_size=max_chars)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        starts = [match.start() for match in self.HEADING_PATTERN.finditer(text)]
        if not starts:
            return self._fallback.chunk(text)

        sections: list[str] = []
        if starts[0] > 0 and text[: starts[0]].strip():
            sections.append(text[: starts[0]])

        for index, start in enumerate(starts):
            end = starts[index + 1] if index + 1 < len(starts) else len(text)
            section = text[start:end]
            if section.strip():
                sections.append(section)

        chunks: list[str] = []
        for section in sections:
            if len(section) <= self.max_chars:
                chunks.append(section.strip())
            else:
                chunks.extend(
                    piece.strip()
                    for piece in self._fallback.chunk(section)
                    if piece.strip()
                )
        return chunks
