from fastapi import APIRouter
from datetime import datetime

from app.config import config
from app.vector_stores.factory import store_manager
from app.embeddings.manager import embedding_manager

router = APIRouter()


@router.get("/health")
async def health_check():
    """Backend health check with library versions and system info."""
    collections = store_manager.list_collections()
    total_docs = sum(c.get("document_count", 0) for c in collections)

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "default_backend": config.storage.default_backend,
        "default_embedding_model": config.embedding.default_model,
        "collections_count": len(collections),
        "total_documents": total_docs,
        "available_models": embedding_manager.available_models(),
        "supported_backends": ["chroma", "faiss"],
        "supported_formats": [".pdf", ".docx", ".txt", ".md"],
    }
