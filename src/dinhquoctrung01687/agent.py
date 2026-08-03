from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """Answer questions using retrieved evidence from an EmbeddingStore."""

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        if not callable(llm_fn):
            raise TypeError("llm_fn must be callable")
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        retrieved = self.store.search(question.strip(), top_k=top_k)
        context_blocks = []
        for index, result in enumerate(retrieved, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("source") or "unknown"
            context_blocks.append(
                f"[{index}] source={source} score={result['score']:.4f}\n"
                f"{result['content']}"
            )

        context = (
            "\n\n".join(context_blocks)
            if context_blocks
            else "Không tìm thấy đoạn tài liệu liên quan trong knowledge base."
        )
        prompt = f"""Bạn là trợ lý tra cứu dùng Retrieval-Augmented Generation (RAG).
Chỉ trả lời dựa trên CONTEXT bên dưới. Không tự bổ sung quy định hoặc dữ kiện không có trong context.
Nếu context không đủ, hãy nói rõ rằng chưa đủ thông tin và đề nghị kiểm tra nguồn chính thức.
Khi có thể, hãy tham chiếu số đoạn [1], [2], ... hỗ trợ câu trả lời.

CONTEXT:
{context}

QUESTION:
{question.strip()}

ANSWER:
"""
        answer = self.llm_fn(prompt)
        if not isinstance(answer, str):
            raise TypeError("llm_fn must return a string")
        return answer
