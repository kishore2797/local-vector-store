import chromadb
from chromadb.config import Settings
from typing import Any, Optional
from pathlib import Path

from app.vector_stores.base import BaseVectorStore


class ChromaVectorStore(BaseVectorStore):
    """ChromaDB-backed vector store with persistent storage and metadata filtering."""

    def __init__(self, collection_name: str, persist_directory: str):
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> int:
        # Sanitize metadata: Chroma doesn't support list values directly
        clean_metadatas = []
        for meta in metadatas:
            clean = {}
            for k, v in meta.items():
                if isinstance(v, list):
                    clean[k] = ",".join(str(item) for item in v)
                elif v is None:
                    continue
                else:
                    clean[k] = v
            clean_metadatas.append(clean)

        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=clean_metadatas,
        )
        return len(ids)

    def get_document(self, doc_id: str) -> Optional[dict[str, Any]]:
        result = self.collection.get(ids=[doc_id], include=["documents", "metadatas", "embeddings"])
        if not result["ids"]:
            return None
        return {
            "id": result["ids"][0],
            "text": result["documents"][0],
            "metadata": result["metadatas"][0] if result["metadatas"] else {},
            "embedding": result["embeddings"][0] if result["embeddings"] else None,
        }

    def get_documents(
        self,
        page: int = 1,
        limit: int = 20,
        filters: Optional[dict[str, Any]] = None,
    ) -> tuple[list[dict[str, Any]], int]:
        where = self._build_where_filter(filters) if filters else None
        total = self.collection.count()

        offset = (page - 1) * limit

        kwargs = {"include": ["documents", "metadatas"], "limit": limit, "offset": offset}
        if where:
            kwargs["where"] = where

        result = self.collection.get(**kwargs)

        docs = []
        for i, doc_id in enumerate(result["ids"]):
            docs.append({
                "id": doc_id,
                "text": result["documents"][i],
                "metadata": result["metadatas"][i] if result["metadatas"] else {},
            })

        return docs, total

    def update_document(
        self,
        doc_id: str,
        text: Optional[str] = None,
        embedding: Optional[list[float]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        existing = self.get_document(doc_id)
        if not existing:
            return False

        kwargs = {"ids": [doc_id]}
        if text is not None:
            kwargs["documents"] = [text]
        if embedding is not None:
            kwargs["embeddings"] = [embedding]
        if metadata is not None:
            clean = {}
            for k, v in metadata.items():
                if isinstance(v, list):
                    clean[k] = ",".join(str(item) for item in v)
                elif v is None:
                    continue
                else:
                    clean[k] = v
            kwargs["metadatas"] = [clean]

        self.collection.update(**kwargs)
        return True

    def delete_documents(self, ids: list[str]) -> int:
        existing_ids = []
        for doc_id in ids:
            if self.get_document(doc_id):
                existing_ids.append(doc_id)

        if existing_ids:
            self.collection.delete(ids=existing_ids)
        return len(existing_ids)

    def delete_by_filter(self, filters: dict[str, Any]) -> int:
        where = self._build_where_filter(filters)
        if not where:
            return 0

        result = self.collection.get(where=where, include=[])
        count = len(result["ids"])
        if count > 0:
            self.collection.delete(ids=result["ids"])
        return count

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: Optional[dict[str, Any]] = None,
        min_score: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        where = self._build_where_filter(filters) if filters else None

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        result = self.collection.query(**kwargs)

        results = []
        if result["ids"] and result["ids"][0]:
            for i, doc_id in enumerate(result["ids"][0]):
                # Chroma returns distances (lower = more similar for cosine)
                # Convert to similarity score: 1 - distance
                distance = result["distances"][0][i]
                score = 1.0 - distance

                if min_score is not None and score < min_score:
                    continue

                results.append({
                    "id": doc_id,
                    "text": result["documents"][0][i],
                    "metadata": result["metadatas"][0][i] if result["metadatas"] else {},
                    "score": round(score, 4),
                })

        return results

    def count(self) -> int:
        return self.collection.count()

    def persist(self) -> None:
        # PersistentClient auto-persists, but we call this for interface compliance
        pass

    def clear(self) -> None:
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def get_all_texts(self) -> list[tuple[str, str]]:
        result = self.collection.get(include=["documents"])
        pairs = []
        for i, doc_id in enumerate(result["ids"]):
            pairs.append((doc_id, result["documents"][i]))
        return pairs

    def _build_where_filter(self, filters: dict[str, Any]) -> Optional[dict]:
        """Convert our filter format to Chroma's where clause format."""
        if not filters:
            return None

        # If it's already in Chroma format ($and, $or, etc.), pass through
        if any(k.startswith("$") for k in filters):
            return self._convert_compound_filter(filters)

        # Simple key-value filters: {"category": "legal"} → {"category": {"$eq": "legal"}}
        if len(filters) == 1:
            key, value = next(iter(filters.items()))
            if isinstance(value, dict):
                return {key: value}
            return {key: {"$eq": value}}

        # Multiple simple filters → $and
        conditions = []
        for key, value in filters.items():
            if isinstance(value, dict):
                conditions.append({key: value})
            else:
                conditions.append({key: {"$eq": value}})
        return {"$and": conditions}

    def _convert_compound_filter(self, filters: dict) -> dict:
        """Recursively convert compound filters."""
        result = {}
        for key, value in filters.items():
            if key in ("$and", "$or"):
                result[key] = [
                    self._build_where_filter(cond) if isinstance(cond, dict) else cond
                    for cond in value
                ]
            elif key == "$not":
                result[key] = self._build_where_filter(value)
            else:
                result[key] = value
        return result
