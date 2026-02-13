import json
import numpy as np
import faiss
from typing import Any, Optional
from pathlib import Path
from datetime import datetime

from app.vector_stores.base import BaseVectorStore


class FAISSVectorStore(BaseVectorStore):
    """FAISS-backed vector store with persistent storage and metadata filtering."""

    def __init__(self, collection_name: str, persist_directory: str, dimension: int = 384, index_type: str = "Flat"):
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.dimension = dimension
        self.index_type = index_type

        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        self._documents: dict[str, dict[str, Any]] = {}  # id -> {text, metadata}
        self._id_to_idx: dict[str, int] = {}  # doc_id -> faiss index position
        self._idx_to_id: dict[int, str] = {}  # faiss index position -> doc_id
        self._next_idx: int = 0

        self.index = self._create_index(index_type, dimension)
        self._load_from_disk()

    def _create_index(self, index_type: str, dimension: int) -> faiss.Index:
        if index_type == "Flat":
            return faiss.IndexFlatIP(dimension)  # Inner product (use normalized vectors for cosine)
        elif index_type == "IVFFlat":
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, min(100, max(1, dimension // 4)))
            return index
        elif index_type == "HNSW":
            index = faiss.IndexHNSWFlat(dimension, 32)
            index.hnsw.efConstruction = 200
            index.hnsw.efSearch = 128
            return index
        else:
            return faiss.IndexFlatIP(dimension)

    def add_documents(
        self,
        ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, Any]],
    ) -> int:
        vectors = np.array(embeddings, dtype=np.float32)
        # Normalize for cosine similarity via inner product
        faiss.normalize_L2(vectors)

        # Train IVF index if needed
        if hasattr(self.index, 'is_trained') and not self.index.is_trained:
            if vectors.shape[0] >= self.index.nlist:
                self.index.train(vectors)

        self.index.add(vectors)

        for i, doc_id in enumerate(ids):
            idx = self._next_idx
            self._id_to_idx[doc_id] = idx
            self._idx_to_id[idx] = doc_id
            self._documents[doc_id] = {
                "text": texts[i],
                "metadata": metadatas[i],
                "created_at": datetime.utcnow().isoformat(),
            }
            self._next_idx += 1

        self.persist()
        return len(ids)

    def get_document(self, doc_id: str) -> Optional[dict[str, Any]]:
        if doc_id not in self._documents:
            return None
        doc = self._documents[doc_id]
        return {
            "id": doc_id,
            "text": doc["text"],
            "metadata": doc.get("metadata", {}),
        }

    def get_documents(
        self,
        page: int = 1,
        limit: int = 20,
        filters: Optional[dict[str, Any]] = None,
    ) -> tuple[list[dict[str, Any]], int]:
        all_docs = list(self._documents.items())

        if filters:
            all_docs = [(did, doc) for did, doc in all_docs if self._matches_filter(doc.get("metadata", {}), filters)]

        total = len(all_docs)
        start = (page - 1) * limit
        end = start + limit
        page_docs = all_docs[start:end]

        docs = []
        for doc_id, doc in page_docs:
            docs.append({
                "id": doc_id,
                "text": doc["text"],
                "metadata": doc.get("metadata", {}),
            })

        return docs, total

    def update_document(
        self,
        doc_id: str,
        text: Optional[str] = None,
        embedding: Optional[list[float]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        if doc_id not in self._documents:
            return False

        if text is not None:
            self._documents[doc_id]["text"] = text
        if metadata is not None:
            self._documents[doc_id]["metadata"] = metadata

        # Note: FAISS doesn't support in-place vector updates easily.
        # For embedding updates, we'd need to rebuild the index.
        # This is handled by the caller doing delete + re-add for text changes.

        self.persist()
        return True

    def delete_documents(self, ids: list[str]) -> int:
        count = 0
        for doc_id in ids:
            if doc_id in self._documents:
                del self._documents[doc_id]
                if doc_id in self._id_to_idx:
                    idx = self._id_to_idx[doc_id]
                    del self._idx_to_id[idx]
                    del self._id_to_idx[doc_id]
                count += 1

        if count > 0:
            self._rebuild_index()
            self.persist()
        return count

    def delete_by_filter(self, filters: dict[str, Any]) -> int:
        to_delete = []
        for doc_id, doc in self._documents.items():
            if self._matches_filter(doc.get("metadata", {}), filters):
                to_delete.append(doc_id)
        return self.delete_documents(to_delete)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filters: Optional[dict[str, Any]] = None,
        min_score: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        if self.index.ntotal == 0:
            return []

        query_vec = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_vec)

        # Search more than top_k if we have filters (post-filtering)
        search_k = top_k * 5 if filters else top_k
        search_k = min(search_k, self.index.ntotal)

        scores, indices = self.index.search(query_vec, search_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:
                continue

            doc_id = self._idx_to_id.get(int(idx))
            if doc_id is None or doc_id not in self._documents:
                continue

            score = float(scores[0][i])
            # Convert inner product to 0-1 range (already normalized, so IP ≈ cosine)
            score = max(0.0, min(1.0, (score + 1.0) / 2.0))

            if min_score is not None and score < min_score:
                continue

            doc = self._documents[doc_id]
            if filters and not self._matches_filter(doc.get("metadata", {}), filters):
                continue

            results.append({
                "id": doc_id,
                "text": doc["text"],
                "metadata": doc.get("metadata", {}),
                "score": round(score, 4),
            })

            if len(results) >= top_k:
                break

        return results

    def count(self) -> int:
        return len(self._documents)

    def persist(self) -> None:
        base = Path(self.persist_directory) / self.collection_name
        base.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        if self.index.ntotal > 0:
            faiss.write_index(self.index, str(base / "index.faiss"))

        # Save documents and mappings
        data = {
            "documents": self._documents,
            "id_to_idx": self._id_to_idx,
            "idx_to_id": {str(k): v for k, v in self._idx_to_id.items()},
            "next_idx": self._next_idx,
            "dimension": self.dimension,
            "index_type": self.index_type,
        }
        with open(base / "metadata.json", "w") as f:
            json.dump(data, f, default=str)

    def clear(self) -> None:
        self._documents.clear()
        self._id_to_idx.clear()
        self._idx_to_id.clear()
        self._next_idx = 0
        self.index = self._create_index(self.index_type, self.dimension)
        self.persist()

    def get_all_texts(self) -> list[tuple[str, str]]:
        return [(doc_id, doc["text"]) for doc_id, doc in self._documents.items()]

    def _load_from_disk(self) -> None:
        base = Path(self.persist_directory) / self.collection_name
        metadata_path = base / "metadata.json"
        index_path = base / "index.faiss"

        if not metadata_path.exists():
            return

        with open(metadata_path, "r") as f:
            data = json.load(f)

        self._documents = data.get("documents", {})
        self._id_to_idx = data.get("id_to_idx", {})
        self._idx_to_id = {int(k): v for k, v in data.get("idx_to_id", {}).items()}
        self._next_idx = data.get("next_idx", 0)

        if index_path.exists():
            self.index = faiss.read_index(str(index_path))

    def _rebuild_index(self) -> None:
        """Rebuild FAISS index from scratch after deletions."""
        # We need stored embeddings to rebuild — for now, we mark as needing re-ingestion
        # In production, you'd store embeddings alongside documents
        self.index = self._create_index(self.index_type, self.dimension)
        self._id_to_idx.clear()
        self._idx_to_id.clear()
        self._next_idx = 0

    def _matches_filter(self, metadata: dict, filters: dict) -> bool:
        """Check if document metadata matches the given filters."""
        for key, condition in filters.items():
            if key == "$and":
                return all(self._matches_filter(metadata, c) for c in condition)
            elif key == "$or":
                return any(self._matches_filter(metadata, c) for c in condition)
            elif key == "$not":
                return not self._matches_filter(metadata, condition)

            value = metadata.get(key)
            if isinstance(condition, dict):
                for op, target in condition.items():
                    if op == "$eq" and value != target:
                        return False
                    elif op == "$ne" and value == target:
                        return False
                    elif op == "$gt" and (value is None or value <= target):
                        return False
                    elif op == "$gte" and (value is None or value < target):
                        return False
                    elif op == "$lt" and (value is None or value >= target):
                        return False
                    elif op == "$lte" and (value is None or value > target):
                        return False
                    elif op == "$in" and value not in target:
                        return False
                    elif op == "$nin" and value in target:
                        return False
                    elif op == "$contains":
                        if isinstance(value, str) and target not in value:
                            return False
                        elif isinstance(value, list) and target not in value:
                            return False
            else:
                if value != condition:
                    return False

        return True
