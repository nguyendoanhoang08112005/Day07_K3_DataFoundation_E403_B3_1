from __future__ import annotations

import re
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """A deterministic vector-store wrapper with optional Chroma mirroring."""

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._client = None
        self._next_index = 0

        # Keep the in-memory representation as the source of truth so tests and
        # classroom runs are reproducible. Chroma is mirrored when available.
        try:
            import chromadb

            safe_name = self._safe_collection_name(collection_name)
            self._client = chromadb.EphemeralClient()
            self._collection = self._client.get_or_create_collection(
                name=safe_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None
            self._client = None

    @staticmethod
    def _safe_collection_name(name: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9._-]", "-", name).strip(".-")
        cleaned = cleaned or "documents"
        if len(cleaned) < 3:
            cleaned = f"lab-{cleaned}"
        return cleaned[:63]

    def _make_record(self, doc: Document) -> dict[str, Any]:
        if not isinstance(doc, Document):
            raise TypeError("docs must contain Document instances")
        if not isinstance(doc.content, str):
            raise TypeError("Document.content must be a string")

        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)
        storage_id = f"{doc.id}::record_{self._next_index}"
        self._next_index += 1
        return {
            "id": storage_id,
            "doc_id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": [float(value) for value in self._embedding_fn(doc.content)],
        }

    def _search_records(
        self,
        query: str,
        records: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []

        query_embedding = [float(value) for value in self._embedding_fn(query)]
        ranked: list[dict[str, Any]] = []
        for record in records:
            embedding = record["embedding"]
            if len(query_embedding) != len(embedding):
                raise ValueError("query and document embeddings have different dimensions")
            ranked.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    "metadata": dict(record["metadata"]),
                    "score": float(_dot(query_embedding, embedding)),
                }
            )

        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]
        self._store.extend(records)

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[record["id"] for record in records],
                    documents=[record["content"] for record in records],
                    embeddings=[record["embedding"] for record in records],
                    metadatas=[
                        self._chroma_metadata(record["metadata"])
                        for record in records
                    ],
                )
            except Exception:
                # The in-memory copy remains complete and searchable.
                self._use_chroma = False

    @staticmethod
    def _chroma_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
        allowed = (str, int, float, bool)
        return {
            str(key): value if isinstance(value, allowed) else str(value)
            for key, value in metadata.items()
            if value is not None
        }

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        return len(self._store)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> list[dict]:
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        filtered_records = [
            record
            for record in self._store
            if all(
                record["metadata"].get(key) == expected
                for key, expected in metadata_filter.items()
            )
        ]
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        matching_ids = [
            record["id"]
            for record in self._store
            if record["metadata"].get("doc_id") == doc_id
            or record["doc_id"] == doc_id
        ]
        if not matching_ids:
            return False

        matching_id_set = set(matching_ids)
        self._store = [
            record for record in self._store if record["id"] not in matching_id_set
        ]

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=matching_ids)
            except Exception:
                self._use_chroma = False
        return True
