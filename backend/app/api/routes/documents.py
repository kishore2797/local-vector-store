import uuid
import asyncio
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from typing import Optional

from app.models.document import (
    DocumentIngestRequest,
    DocumentUpdateRequest,
    DocumentDeleteByIds,
    IngestResponse,
)
from app.vector_stores.factory import store_manager
from app.embeddings.manager import embedding_manager
from app.ingestion.metadata import validate_metadata, enrich_metadata
from app.ingestion.file_parser import parse_file
from app.ingestion.chunker import chunk_text
from app.search.keyword_search import keyword_engine

router = APIRouter()


@router.post("/{name}/documents")
async def ingest_documents(name: str, body: DocumentIngestRequest):
    """Add documents with metadata to a collection."""
    store = store_manager.get_store(name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    meta = store_manager.get_meta(name)
    model_name = meta.embedding_model if meta else None

    ids = []
    texts = []
    metadatas = []
    errors = []
    skipped = 0

    for i, doc in enumerate(body.documents):
        doc_id = doc.id or str(uuid.uuid4())

        # Check for duplicates
        existing = store.get_document(doc_id)
        if existing:
            if body.on_conflict == "skip":
                skipped += 1
                continue
            elif body.on_conflict == "error":
                errors.append({"id": doc_id, "error": "Document already exists"})
                continue
            # upsert: will overwrite below

        raw_meta = doc.metadata or {}
        cleaned = validate_metadata(raw_meta)
        enriched = enrich_metadata(cleaned, doc.text, source="api")

        ids.append(doc_id)
        texts.append(doc.text)
        metadatas.append(enriched)

    if not ids:
        return IngestResponse(
            ingested=0,
            skipped=skipped,
            errors=errors,
            collection=name,
        )

    # Generate embeddings (run in thread to avoid blocking event loop)
    try:
        embeddings = await asyncio.to_thread(embedding_manager.embed_texts, texts, model_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

    # Add to store
    count = await asyncio.to_thread(store.add_documents, ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)

    # Invalidate keyword index
    keyword_engine.invalidate(name)

    return IngestResponse(
        ingested=count,
        skipped=skipped,
        errors=errors,
        collection=name,
    )


@router.post("/{name}/upload")
async def upload_file(
    name: str,
    file: UploadFile = File(...),
    chunk_strategy: str = Form("recursive"),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(200),
    custom_metadata: Optional[str] = Form(None),
):
    """Upload a file, auto-chunk, embed, and store."""
    store = store_manager.get_store(name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    meta = store_manager.get_meta(name)
    model_name = meta.embedding_model if meta else None

    # Read file
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=413, detail="File too large. Maximum 50MB.")

    # Parse file
    try:
        parsed = parse_file(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ImportError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Chunk text
    chunks = chunk_text(
        parsed["text"],
        strategy=chunk_strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    if not chunks:
        raise HTTPException(status_code=400, detail="No text extracted from file")

    # Parse custom metadata
    import json
    extra_meta = {}
    if custom_metadata:
        try:
            extra_meta = json.loads(custom_metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid custom_metadata JSON")

    # Prepare documents
    ids = []
    texts = []
    metadatas = []

    for chunk in chunks:
        doc_id = str(uuid.uuid4())
        chunk_meta = {
            **parsed["metadata"],
            **extra_meta,
            "_chunk_index": chunk["chunk_index"],
            "_start_char": chunk["start_char"],
            "_end_char": chunk["end_char"],
        }
        cleaned = validate_metadata(chunk_meta)
        enriched = enrich_metadata(cleaned, chunk["text"], source="file_upload")

        ids.append(doc_id)
        texts.append(chunk["text"])
        metadatas.append(enriched)

    # Embed and store (run in thread to avoid blocking event loop)
    try:
        embeddings = await asyncio.to_thread(embedding_manager.embed_texts, texts, model_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

    count = await asyncio.to_thread(store.add_documents, ids=ids, texts=texts, embeddings=embeddings, metadatas=metadatas)
    keyword_engine.invalidate(name)

    return {
        "message": f"File '{file.filename}' processed successfully",
        "chunks_created": count,
        "filename": file.filename,
        "format": parsed["metadata"].get("format", "unknown"),
        "total_characters": parsed["metadata"].get("char_count", 0),
        "collection": name,
    }


@router.get("/{name}/documents")
async def list_documents(
    name: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    filter: Optional[str] = None,
):
    """Browse documents in a collection with pagination and filtering."""
    store = store_manager.get_store(name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    import json
    filters = None
    if filter:
        try:
            filters = json.loads(filter)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid filter JSON")

    docs, total = await asyncio.to_thread(store.get_documents, page=page, limit=limit, filters=filters)

    # Enrich with computed fields
    for doc in docs:
        doc["char_count"] = len(doc.get("text", ""))
        doc["token_estimate"] = doc["char_count"] // 4

    return {
        "documents": docs,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{name}/documents/{doc_id}")
async def get_document(name: str, doc_id: str):
    """Get a single document by ID."""
    store = store_manager.get_store(name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    doc = await asyncio.to_thread(store.get_document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")

    doc["char_count"] = len(doc.get("text", ""))
    doc["token_estimate"] = doc["char_count"] // 4
    return doc


@router.patch("/{name}/documents/{doc_id}")
async def update_document(name: str, doc_id: str, body: DocumentUpdateRequest):
    """Update a document's text and/or metadata."""
    store = store_manager.get_store(name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    meta = store_manager.get_meta(name)
    model_name = meta.embedding_model if meta else None

    embedding = None
    if body.text is not None:
        # Re-embed if text changed
        embedding = await asyncio.to_thread(embedding_manager.embed_query, body.text, model_name)

    cleaned_meta = None
    if body.metadata is not None:
        cleaned_meta = validate_metadata(body.metadata)

    updated = await asyncio.to_thread(store.update_document, doc_id=doc_id, text=body.text, embedding=embedding, metadata=cleaned_meta)

    if not updated:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")

    keyword_engine.invalidate(name)
    return {"message": f"Document '{doc_id}' updated successfully"}


@router.delete("/{name}/documents/{doc_id}")
async def delete_document(name: str, doc_id: str):
    """Delete a single document by ID."""
    store = store_manager.get_store(name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    count = await asyncio.to_thread(store.delete_documents, [doc_id])
    if count == 0:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")

    keyword_engine.invalidate(name)
    return {"message": f"Document '{doc_id}' deleted successfully", "deleted": count}


@router.post("/{name}/documents/delete")
async def bulk_delete_documents(name: str, body: DocumentDeleteByIds):
    """Delete multiple documents by ID list."""
    store = store_manager.get_store(name)
    if not store:
        raise HTTPException(status_code=404, detail=f"Collection '{name}' not found")

    count = await asyncio.to_thread(store.delete_documents, body.ids)
    keyword_engine.invalidate(name)
    return {"message": f"{count} documents deleted", "deleted": count}
