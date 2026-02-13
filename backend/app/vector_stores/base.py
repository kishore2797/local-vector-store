from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseVectorStore(ABC):
    """Abstract base class for vector store backends."""

    @abstractmethod
    def add_documents(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> int:
        """Add documents with embeddings and metadata. Returns count added."""
        pass

    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[dict[str, Any]]:
        """Get a single document by ID."""
        pass

    @abstractmethod
    def get_documents(
        self,
        page: int = 1,
        limit: int = 20,
        filters: Optional[dict[str, Any]] = None,
    ) -> tuple[list[dict[str, Any]], int]:
        """Get paginated documents. Returns (documents, total_count)."""
        pass

    @abstractmethod
    def update_document(
        self,
        doc_id: str,
        text: Optional[str] = None,
        embedding: Optional[list[float]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Update a document. Returns True if found and updated."""
        pass

    @abstractmethod
    def delete_documents(self, ids: list[str]) -> int:
        """Delete documents by IDs. Returns count deleted."""
        pass

    @abstractmethod
    def delete_by_filter(self, filters: dict[str, Any]) -> int:
        """Delete documents matching filter. Returns count deleted."""
        pass

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: Optional[dict[str, Any]] = None,
        min_score: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Vector similarity search. Returns list of results with scores."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total document count."""
        pass

    @abstractmethod
    def persist(self) -> None:
        """Persist data to disk."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Remove all documents."""
        pass

    @abstractmethod
    def get_all_texts(self) -> list[tuple[str, str]]:
        """Return all (id, text) pairs for keyword indexing."""
        pass
