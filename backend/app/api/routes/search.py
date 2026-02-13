import time
import asyncio
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    CompareSearchResponse,
    MultiSearchRequest,
)
from app.vector_stores.factory import store_manager
from app.search.vector_search import vector_search
from app.search.keyword_search import keyword_engine
from app.search.hybrid_search import hybrid_search

router = APIRouter()


@router.post("/{name}/search")
async def search_collection(name: str, body: SearchRequest):
    """Search a collection using vector, keyword, or hybrid search."""
    store = store_manager.get_store(name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    meta = store_manager.get_meta(name)
    model_name = meta.embedding_model if meta else None

    start = time.time()

    if body.search_type == "vector":
        results = await asyncio.to_thread(
            vector_search,
            store=store,
            query=body.query,
            top_k=body.top_k,
            filters=body.filters,
            min_score=body.min_score,
            model_name=model_name,
        )
    elif body.search_type == "keyword":
        results = await asyncio.to_thread(
            keyword_engine.search,
            collection_name=name,
            store=store,
            query=body.query,
            top_k=body.top_k,
            filters=body.filters,
            highlight=body.highlight,
        )
    elif body.search_type == "hybrid":
        hc = body.hybrid_config
        results = await asyncio.to_thread(
            hybrid_search,
            collection_name=name,
            store=store,
            query=body.query,
            top_k=body.top_k,
            filters=body.filters,
            min_score=body.min_score,
            vector_weight=hc.vector_weight if hc else 0.7,
            keyword_weight=hc.keyword_weight if hc else 0.3,
            fusion_method=hc.fusion_method if hc else "weighted_sum",
            highlight=body.highlight,
            model_name=model_name,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown search_type: {body.search_type}")

    elapsed_ms = round((time.time() - start) * 1000, 2)

    return SearchResponse(
        results=[SearchResult(**r) for r in results],
        query=body.query,
        search_type=body.search_type,
        total_results=len(results),
        processing_time_ms=elapsed_ms,
    )


@router.post("/{name}/search/compare")
async def compare_search(name: str, body: SearchRequest):
    """Run the same query across vector, keyword, and hybrid search for comparison."""
    store = store_manager.get_store(name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    meta = store_manager.get_meta(name)
    model_name = meta.embedding_model if meta else None

    # Vector search
    start = time.time()
    vec_results = await asyncio.to_thread(
        vector_search,
        store=store, query=body.query, top_k=body.top_k,
        filters=body.filters, model_name=model_name,
    )
    vec_time = round((time.time() - start) * 1000, 2)

    # Keyword search
    start = time.time()
    kw_results = await asyncio.to_thread(
        keyword_engine.search,
        collection_name=name, store=store, query=body.query,
        top_k=body.top_k, filters=body.filters, highlight=True,
    )
    kw_time = round((time.time() - start) * 1000, 2)

    # Hybrid search
    hc = body.hybrid_config
    start = time.time()
    hyb_results = await asyncio.to_thread(
        hybrid_search,
        collection_name=name, store=store, query=body.query,
        top_k=body.top_k, filters=body.filters,
        vector_weight=hc.vector_weight if hc else 0.7,
        keyword_weight=hc.keyword_weight if hc else 0.3,
        fusion_method=hc.fusion_method if hc else "weighted_sum",
        highlight=True, model_name=model_name,
    )
    hyb_time = round((time.time() - start) * 1000, 2)

    # Overlap analysis
    vec_ids = {r["id"] for r in vec_results}
    kw_ids = {r["id"] for r in kw_results}
    hyb_ids = {r["id"] for r in hyb_results}

    overlap_analysis = {
        "vector_keyword_overlap": len(vec_ids & kw_ids),
        "vector_only": len(vec_ids - kw_ids),
        "keyword_only": len(kw_ids - vec_ids),
        "all_three_overlap": len(vec_ids & kw_ids & hyb_ids),
        "total_unique_documents": len(vec_ids | kw_ids | hyb_ids),
    }

    return CompareSearchResponse(
        vector_results=SearchResponse(
            results=[SearchResult(**r) for r in vec_results],
            query=body.query, search_type="vector",
            total_results=len(vec_results), processing_time_ms=vec_time,
        ),
        keyword_results=SearchResponse(
            results=[SearchResult(**r) for r in kw_results],
            query=body.query, search_type="keyword",
            total_results=len(kw_results), processing_time_ms=kw_time,
        ),
        hybrid_results=SearchResponse(
            results=[SearchResult(**r) for r in hyb_results],
            query=body.query, search_type="hybrid",
            total_results=len(hyb_results), processing_time_ms=hyb_time,
        ),
        overlap_analysis=overlap_analysis,
    )


@router.post("/{name}/search/multi")
async def multi_query_search(name: str, body: MultiSearchRequest):
    """Run multiple queries and merge results using fusion."""
    store = store_manager.get_store(name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    meta = store_manager.get_meta(name)
    model_name = meta.embedding_model if meta else None

    start = time.time()

    all_results: dict[str, dict] = {}
    per_query_results = []

    for qi, query in enumerate(body.queries):
        results = await asyncio.to_thread(
            vector_search,
            store=store, query=query, top_k=body.top_k,
            filters=body.filters, model_name=model_name,
        )
        per_query_results.append({
            "query": query,
            "results": [SearchResult(**r) for r in results],
        })

        # RRF fusion across queries
        for rank, result in enumerate(results):
            doc_id = result["id"]
            if doc_id not in all_results:
                all_results[doc_id] = {**result, "rrf_score": 0, "found_in_queries": []}
            all_results[doc_id]["rrf_score"] += 1.0 / (60 + rank + 1)
            all_results[doc_id]["found_in_queries"].append(qi)

    # Normalize and sort
    if all_results:
        max_rrf = max(r["rrf_score"] for r in all_results.values())
        for doc in all_results.values():
            doc["score"] = round(doc["rrf_score"] / max_rrf, 4) if max_rrf > 0 else 0
            del doc["rrf_score"]

    merged = sorted(all_results.values(), key=lambda x: x["score"], reverse=True)[:body.top_k]

    elapsed_ms = round((time.time() - start) * 1000, 2)

    return {
        "merged_results": [SearchResult(**r) for r in merged],
        "per_query_results": per_query_results,
        "total_results": len(merged),
        "processing_time_ms": elapsed_ms,
    }
