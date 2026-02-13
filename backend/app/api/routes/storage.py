import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException

from app.config import config
from app.vector_stores.factory import store_manager

router = APIRouter()


@router.get("/health")
async def storage_health():
    """Report storage health: disk usage, collection count, total vectors."""
    base_path = Path(config.storage.base_path)

    # Calculate disk usage
    total_size = 0
    if base_path.exists():
        for f in base_path.rglob("*"):
            if f.is_file():
                total_size += f.stat().st_size

    collections = store_manager.list_collections()
    total_docs = sum(c.get("document_count", 0) for c in collections)

    # Disk info
    disk_usage = shutil.disk_usage(str(base_path.parent))

    return {
        "status": "healthy",
        "storage_path": str(base_path.absolute()),
        "storage_size_bytes": total_size,
        "storage_size_mb": round(total_size / (1024 * 1024), 2),
        "collections_count": len(collections),
        "total_documents": total_docs,
        "disk_total_gb": round(disk_usage.total / (1024**3), 2),
        "disk_used_gb": round(disk_usage.used / (1024**3), 2),
        "disk_free_gb": round(disk_usage.free / (1024**3), 2),
        "disk_usage_percent": round(disk_usage.used / disk_usage.total * 100, 1),
        "backends": {
            "chroma": {
                "persist_directory": config.storage.chroma.persist_directory,
                "exists": Path(config.storage.chroma.persist_directory).exists(),
            },
            "faiss": {
                "persist_directory": config.storage.faiss.persist_directory,
                "index_type": config.storage.faiss.index_type,
                "exists": Path(config.storage.faiss.persist_directory).exists(),
            },
        },
    }


@router.post("/persist")
async def persist_all():
    """Force persist all collections to disk."""
    store_manager.persist_all()
    return {"message": "All collections persisted to disk"}


@router.get("/collections/{name}/size")
async def collection_size(name: str):
    """Get disk size for a specific collection."""
    if not store_manager.collection_exists(name):
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    meta = store_manager.get_meta(name)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    # Calculate size based on backend
    if meta.backend == "chroma":
        coll_path = Path(config.storage.chroma.persist_directory) / name
    else:
        coll_path = Path(config.storage.faiss.persist_directory) / name

    total_size = 0
    if coll_path.exists():
        for f in coll_path.rglob("*"):
            if f.is_file():
                total_size += f.stat().st_size

    store = store_manager.get_store(name)
    doc_count = store.count() if store else 0

    return {
        "collection": name,
        "backend": meta.backend,
        "document_count": doc_count,
        "disk_size_bytes": total_size,
        "disk_size_mb": round(total_size / (1024 * 1024), 2),
        "path": str(coll_path),
    }
