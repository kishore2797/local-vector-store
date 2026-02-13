from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import config
from app.api.routes import collections, documents, search, storage, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: ensure storage directories exist
    from pathlib import Path
    Path(config.storage.chroma.persist_directory).mkdir(parents=True, exist_ok=True)
    Path(config.storage.faiss.persist_directory).mkdir(parents=True, exist_ok=True)

    # Load existing collections
    from app.vector_stores.factory import store_manager
    store_manager.load_all()
    print(f"✅ Vector store ready | Backend: {config.storage.default_backend}")

    yield

    # Shutdown: persist all data
    store_manager.persist_all()
    print("💾 All collections persisted. Shutting down.")


app = FastAPI(
    title="Local Vector Store",
    description="Persistent vector storage with metadata filtering and hybrid search (Chroma/FAISS)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(collections.router, prefix="/api/collections", tags=["Collections"])
app.include_router(documents.router, prefix="/api/collections", tags=["Documents"])
app.include_router(search.router, prefix="/api/collections", tags=["Search"])
app.include_router(storage.router, prefix="/api/storage", tags=["Storage"])


@app.get("/")
async def root():
    return {
        "name": "Local Vector Store",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
