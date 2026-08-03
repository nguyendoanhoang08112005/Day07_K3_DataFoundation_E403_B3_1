from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

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
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            # Initialize chromadb client + collection
            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # Build a normalized stored record for one document
        embedding = self._embedding_fn(doc.content)
        metadata = doc.metadata.copy()
        metadata['doc_id'] = doc.id  # Include doc_id in metadata for deletion
        return {
            'id': doc.id,
            'content': doc.content,
            'embedding': embedding,
            'metadata': metadata
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        # Run in-memory similarity search over provided records
        query_embedding = self._embedding_fn(query)

        # Compute similarity for each record
        scored_records = []
        for record in records:
            score = _dot(query_embedding, record['embedding'])
            scored_records.append({
                'content': record['content'],
                'metadata': record['metadata'],
                'score': score
            })

        # Sort by score descending and return top_k
        scored_records.sort(key=lambda x: x['score'], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if self._use_chroma and self._collection is not None:
            import chromadb
            ids = []
            documents = []
            embeddings = []

            for doc in docs:
                record = self._make_record(doc)
                ids.append(f"{doc.id}_{self._next_index}")
                documents.append(doc.content)
                embeddings.append(record['embedding'])
                self._next_index += 1

            self._collection.add(ids=ids, documents=documents, embeddings=embeddings)
        else:
            for doc in docs:
                record = self._make_record(doc)
                self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            output = []
            for i in range(len(results['documents'][0])):
                output.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                    'score': float(results['distances'][0][i]) if results.get('distances') else 0.0
                })
            return output
        else:
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if self._use_chroma and self._collection is not None:
            if metadata_filter:
                where_filter = metadata_filter
                query_embedding = self._embedding_fn(query)
                results = self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_filter
                )
                output = []
                for i in range(len(results['documents'][0])):
                    output.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results.get('metadatas') else {},
                        'score': float(results['distances'][0][i]) if results.get('distances') else 0.0
                    })
                return output
            else:
                return self.search(query, top_k)
        else:
            # In-memory: filter by metadata first
            if metadata_filter:
                filtered_records = [
                    record for record in self._store
                    if all(record['metadata'].get(k) == v for k, v in metadata_filter.items())
                ]
            else:
                filtered_records = self._store
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            # Get all chunks with this doc_id
            try:
                results = self._collection.get(where={"doc_id": doc_id})
                if results and results.get('ids'):
                    self._collection.delete(ids=results['ids'])
                    return True
                return False
            except Exception:
                return False
        else:
            # In-memory: filter out chunks with matching doc_id
            initial_size = len(self._store)
            self._store = [
                record for record in self._store
                if record['metadata'].get('doc_id') != doc_id
            ]
            return len(self._store) < initial_size
