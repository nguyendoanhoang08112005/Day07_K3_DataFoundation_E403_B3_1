from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        # Store references to store and llm_fn
        self._store = store
        self._llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # Retrieve chunks, build prompt, call llm_fn
        results = self._store.search(question, top_k=top_k)

        if not results:
            return "I don't have enough information in my knowledge base to answer this question."

        # Build context from retrieved chunks
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[{i}] {result['content']}")

        context = "\n\n".join(context_parts)

        # Build prompt with context
        prompt = f"""Based on the following context from the knowledge base, answer the question.

Context:
{context}

Question: {question}

Answer:"""

        # Call the LLM
        answer = self._llm_fn(prompt)
        return answer
