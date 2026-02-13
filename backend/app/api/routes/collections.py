import asyncio
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.collection import (
    CollectionCreate,
    CollectionUpdate,
    CollectionInfo,
    CollectionListResponse,
)
from app.vector_stores.factory import store_manager
from app.embeddings.manager import embedding_manager
from datetime import datetime

router = APIRouter()


@router.post("", status_code=201)
async def create_collection(body: CollectionCreate):
    """Create a new vector collection."""
    if store_manager.collection_exists(body.name):
        raise HTTPException(status_code=409, detail=f"Collection '{body.name}' already exists")

    try:
        dimension = await asyncio.to_thread(embedding_manager.get_dimension, body.embedding_model)
    except Exception:
        dimension = 384

    try:
        store_manager.create_collection(
            name=body.name,
            backend=body.backend,
            embedding_model=body.embedding_model,
            description=body.description,
            metadata_schema=body.metadata_schema,
            dimension=dimension,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    meta = store_manager.get_meta(body.name)
    return {
        "message": f"Collection '{body.name}' created successfully",
        "collection": {
            "name": body.name,
            "backend": body.backend,
            "embedding_model": body.embedding_model,
            "description": body.description,
            "document_count": 0,
            "embedding_dimension": dimension,
            "created_at": meta.created_at if meta else datetime.utcnow().isoformat(),
        },
    }


@router.get("")
async def list_collections(
    sort_by: str = Query("name", enum=["name", "document_count", "created_at"]),
    search: Optional[str] = None,
):
    """List all collections with stats."""
    collections = store_manager.list_collections()

    if search:
        collections = [c for c in collections if search.lower() in c["name"].lower()]

    if sort_by == "document_count":
        collections.sort(key=lambda c: c.get("document_count", 0), reverse=True)
    elif sort_by == "created_at":
        collections.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    else:
        collections.sort(key=lambda c: c["name"])

    return {"collections": collections, "total": len(collections)}


@router.get("/{name}")
async def get_collection(name: str):
    """Get detailed info about a collection."""
    meta = store_manager.get_meta(name)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    store = store_manager.get_store(name)
    doc_count = (await asyncio.to_thread(store.count)) if store else 0

    return {
        **meta.to_dict(),
        "document_count": doc_count,
    }


@router.patch("/{name}")
async def update_collection(name: str, body: CollectionUpdate):
    """Update collection description or metadata schema."""
    if not store_manager.collection_exists(name):
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    store_manager.update_collection(
        name=name,
        description=body.description,
        metadata_schema=body.metadata_schema,
    )

    return {"message": f"Collection '{name}' updated successfully"}


@router.delete("/{name}")
async def delete_collection(
    name: str,
    confirm: bool = Query(False),
    permanent: bool = Query(False),
):
    """Delete a collection. Requires confirm=true."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Delete requires confirm=true query parameter",
        )

    if not store_manager.collection_exists(name):
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    store_manager.delete_collection(name, permanent=permanent)
    return {"message": f"Collection '{name}' deleted successfully"}
