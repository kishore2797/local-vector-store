from typing import Any, Optional

from app.vector_stores.base import BaseVectorStore
from app.search.vector_search import vector_search
from app.search.keyword_search import keyword_engine


def hybrid_search(
    collection_name: str,
    store: BaseVectorStore,
    query: str,
    top_k: int = 5,
    filters: Optional[dict[str, Any]] = None,
    min_score: Optional[float] = None,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3,
    fusion_method: str = "weighted_sum",
    highlight: bool = False,
    model_name: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Combine vector and keyword search results using configurable fusion."""

    # Run both searches
    vec_results = vector_search(
        store=store,
        query=query,
        top_k=top_k * 2,  # Get more for better fusion
        filters=filters,
        min_score=None,  # Apply min_score after fusion
        model_name=model_name,
    )

    kw_results = keyword_engine.search(
        collection_name=collection_name,
        store=store,
        query=query,
        top_k=top_k * 2,
        filters=filters,
        highlight=highlight,
    )

    if fusion_method == "rrf":
        merged = _reciprocal_rank_fusion(vec_results, kw_results, k=60)
    elif fusion_method == "relative_score":
        merged = _relative_score_fusion(vec_results, kw_results, vector_weight, keyword_weight)
    else:  # weighted_sum
        merged = _weighted_sum_fusion(vec_results, kw_results, vector_weight, keyword_weight)

    # Apply min_score filter
    if min_score is not None:
        merged = [r for r in merged if r["score"] >= min_score]

    # Trim to top_k
    merged = merged[:top_k]

    # Assign final ranks
    for i, result in enumerate(merged):
        result["combined_score"] = result["score"]

    return merged


def _weighted_sum_fusion(
    vec_results: list[dict],
    kw_results: list[dict],
    vector_weight: float,
    keyword_weight: float,
) -> list[dict]:
    """Combine scores using weighted sum."""
    all_docs: dict[str, dict] = {}

    for result in vec_results:
        doc_id = result["id"]
        all_docs[doc_id] = {
            **result,
            "vector_score": result.get("score", 0),
            "keyword_score": 0,
            "vector_rank": result.get("vector_rank"),
        }

    for result in kw_results:
        doc_id = result["id"]
        if doc_id in all_docs:
            all_docs[doc_id]["keyword_score"] = result.get("score", 0)
            all_docs[doc_id]["keyword_rank"] = result.get("keyword_rank")
            if result.get("highlighted_text"):
                all_docs[doc_id]["highlighted_text"] = result["highlighted_text"]
        else:
            all_docs[doc_id] = {
                **result,
                "vector_score": 0,
                "keyword_score": result.get("score", 0),
                "keyword_rank": result.get("keyword_rank"),
            }

    # Calculate combined score
    for doc in all_docs.values():
        vs = doc.get("vector_score", 0) or 0
        ks = doc.get("keyword_score", 0) or 0
        doc["score"] = round(vector_weight * vs + keyword_weight * ks, 4)

    merged = sorted(all_docs.values(), key=lambda x: x["score"], reverse=True)
    return merged


def _reciprocal_rank_fusion(
    vec_results: list[dict],
    kw_results: list[dict],
    k: int = 60,
) -> list[dict]:
    """Combine results using Reciprocal Rank Fusion (RRF)."""
    all_docs: dict[str, dict] = {}
    rrf_scores: dict[str, float] = {}

    for i, result in enumerate(vec_results):
        doc_id = result["id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + i + 1)
        all_docs[doc_id] = {
            **result,
            "vector_score": result.get("score", 0),
            "vector_rank": i + 1,
            "keyword_score": 0,
        }

    for i, result in enumerate(kw_results):
        doc_id = result["id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + 1.0 / (k + i + 1)
        if doc_id in all_docs:
            all_docs[doc_id]["keyword_score"] = result.get("score", 0)
            all_docs[doc_id]["keyword_rank"] = i + 1
            if result.get("highlighted_text"):
                all_docs[doc_id]["highlighted_text"] = result["highlighted_text"]
        else:
            all_docs[doc_id] = {
                **result,
                "vector_score": 0,
                "keyword_score": result.get("score", 0),
                "keyword_rank": i + 1,
            }

    # Normalize RRF scores to 0-1
    max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0
    for doc_id, doc in all_docs.items():
        doc["score"] = round(rrf_scores[doc_id] / max_rrf, 4) if max_rrf > 0 else 0

    merged = sorted(all_docs.values(), key=lambda x: x["score"], reverse=True)
    return merged


def _relative_score_fusion(
    vec_results: list[dict],
    kw_results: list[dict],
    vector_weight: float,
    keyword_weight: float,
) -> list[dict]:
    """Normalize score distributions independently, then combine."""
    def normalize_scores(results: list[dict]) -> list[dict]:
        if not results:
            return results
        scores = [r.get("score", 0) for r in results]
        min_s, max_s = min(scores), max(scores)
        range_s = max_s - min_s if max_s != min_s else 1.0
        for r in results:
            r["_normalized"] = (r.get("score", 0) - min_s) / range_s
        return results

    vec_results = normalize_scores(vec_results)
    kw_results = normalize_scores(kw_results)

    all_docs: dict[str, dict] = {}

    for result in vec_results:
        doc_id = result["id"]
        all_docs[doc_id] = {
            **result,
            "vector_score": result.get("score", 0),
            "_vec_norm": result.get("_normalized", 0),
            "keyword_score": 0,
            "_kw_norm": 0,
            "vector_rank": result.get("vector_rank"),
        }

    for result in kw_results:
        doc_id = result["id"]
        if doc_id in all_docs:
            all_docs[doc_id]["keyword_score"] = result.get("score", 0)
            all_docs[doc_id]["_kw_norm"] = result.get("_normalized", 0)
            all_docs[doc_id]["keyword_rank"] = result.get("keyword_rank")
            if result.get("highlighted_text"):
                all_docs[doc_id]["highlighted_text"] = result["highlighted_text"]
        else:
            all_docs[doc_id] = {
                **result,
                "vector_score": 0,
                "_vec_norm": 0,
                "keyword_score": result.get("score", 0),
                "_kw_norm": result.get("_normalized", 0),
                "keyword_rank": result.get("keyword_rank"),
            }

    for doc in all_docs.values():
        vn = doc.pop("_vec_norm", 0)
        kn = doc.pop("_kw_norm", 0)
        doc.pop("_normalized", None)
        doc["score"] = round(vector_weight * vn + keyword_weight * kn, 4)

    merged = sorted(all_docs.values(), key=lambda x: x["score"], reverse=True)
    return merged
