import re
from typing import Any, Optional
from rank_bm25 import BM25Okapi

from app.vector_stores.base import BaseVectorStore


class KeywordSearchEngine:
    """BM25-based keyword search engine."""

    def __init__(self):
        self._indices: dict[str, BM25Okapi] = {}
        self._doc_data: dict[str, list[tuple[str, str]]] = {}  # collection -> [(id, text)]

    def build_index(self, collection_name: str, store: BaseVectorStore) -> None:
        """Build or rebuild BM25 index for a collection."""
        doc_pairs = store.get_all_texts()
        if not doc_pairs:
            self._indices.pop(collection_name, None)
            self._doc_data.pop(collection_name, None)
            return

        self._doc_data[collection_name] = doc_pairs
        tokenized = [self._tokenize(text) for _, text in doc_pairs]
        self._indices[collection_name] = BM25Okapi(tokenized)

    def search(
        self,
        collection_name: str,
        store: BaseVectorStore,
        query: str,
        top_k: int = 5,
        filters: Optional[dict[str, Any]] = None,
        highlight: bool = False,
    ) -> list[dict[str, Any]]:
        """Run BM25 keyword search."""
        # Rebuild index if not present
        if collection_name not in self._indices:
            self.build_index(collection_name, store)

        if collection_name not in self._indices:
            return []

        bm25 = self._indices[collection_name]
        doc_pairs = self._doc_data[collection_name]

        tokenized_query = self._tokenize(query)
        scores = bm25.get_scores(tokenized_query)

        # Pair scores with doc data
        scored_docs = list(zip(scores, doc_pairs))
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # Normalize scores to 0-1 range
        max_score = max(scores) if max(scores) > 0 else 1.0

        results = []
        for score, (doc_id, text) in scored_docs[:top_k * 3]:  # Get extra for filtering
            if score <= 0:
                continue

            # Get full document with metadata from store
            doc = store.get_document(doc_id)
            if doc is None:
                continue

            metadata = doc.get("metadata", {})

            # Apply metadata filters
            if filters and not self._matches_filter(metadata, filters):
                continue

            normalized_score = round(score / max_score, 4)

            result = {
                "id": doc_id,
                "text": text,
                "metadata": metadata,
                "score": normalized_score,
                "keyword_score": normalized_score,
                "keyword_rank": len(results) + 1,
            }

            if highlight:
                result["highlighted_text"] = self._highlight_text(text, tokenized_query)

            results.append(result)

            if len(results) >= top_k:
                break

        return results

    def invalidate(self, collection_name: str) -> None:
        """Remove cached index for a collection (call after document changes)."""
        self._indices.pop(collection_name, None)
        self._doc_data.pop(collection_name, None)

    def _tokenize(self, text: str) -> list[str]:
        """Simple whitespace + punctuation tokenizer with lowercasing."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
            'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'and', 'but', 'or',
            'not', 'no', 'nor', 'so', 'yet', 'both', 'either', 'neither', 'each',
            'every', 'all', 'any', 'few', 'more', 'most', 'other', 'some', 'such',
            'than', 'too', 'very', 'just', 'also', 'this', 'that', 'these', 'those',
            'it', 'its', 'he', 'she', 'they', 'them', 'their', 'we', 'us', 'our',
        }
        return [t for t in tokens if t not in stop_words and len(t) > 1]

    def _highlight_text(self, text: str, query_tokens: list[str]) -> str:
        """Wrap matched terms in <mark> tags."""
        highlighted = text
        for token in set(query_tokens):
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            highlighted = pattern.sub(f"<mark>{token}</mark>", highlighted)
        return highlighted

    def _matches_filter(self, metadata: dict, filters: dict) -> bool:
        """Check if metadata matches filters (reuse FAISS logic)."""
        for key, condition in filters.items():
            if key.startswith("$"):
                if key == "$and":
                    return all(self._matches_filter(metadata, c) for c in condition)
                elif key == "$or":
                    return any(self._matches_filter(metadata, c) for c in condition)
                elif key == "$not":
                    return not self._matches_filter(metadata, condition)
                continue

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
            else:
                if value != condition:
                    return False

        return True


# Global keyword search engine instance
keyword_engine = KeywordSearchEngine()
