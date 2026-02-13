from typing import Any, Optional

from app.vector_stores.base import BaseVectorStore
from app.embeddings.manager import embedding_manager


def vector_search(
    store: BaseVectorStore,
    query: str,
    top_k: int = 5,
    filters: Optional[dict[str, Any]] = None,
    min_score: Optional[float] = None,
    model_name: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Run semantic similarity search against a vector store."""
    query_embedding = embedding_manager.embed_query(query, model_name)
    results = store.search(
        query_embedding=query_embedding,
        top_k=top_k,
        filters=filters,
        min_score=min_score,
    )

    for i, result in enumerate(results):
        result["vector_score"] = result["score"]
        result["vector_rank"] = i + 1

    return results
