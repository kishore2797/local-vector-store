"""Minimal test server to isolate the hang."""
import asyncio
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/test-embed")
async def test_embed():
    from app.embeddings.manager import embedding_manager
    print("Starting embed...")
    result = await asyncio.to_thread(
        embedding_manager.embed_texts,
        ["hello world", "test document"],
        None,
    )
    print(f"Embed done, got {len(result)} vectors")
    return {"count": len(result)}

@app.post("/test-store")
async def test_store():
    from app.vector_stores.factory import store_manager
    from app.embeddings.manager import embedding_manager
    import uuid

    print("Creating collection...")
    if not store_manager.collection_exists("debug-test"):
        store_manager.create_collection(
            name="debug-test", backend="chroma",
            embedding_model="all-MiniLM-L6-v2",
            dimension=384,
        )

    store = store_manager.get_store("debug-test")
    texts = ["hello world"]
    print("Embedding...")
    embeddings = await asyncio.to_thread(embedding_manager.embed_texts, texts, None)
    print("Adding to store...")
    count = await asyncio.to_thread(
        store.add_documents,
        ids=[str(uuid.uuid4())],
        texts=texts,
        embeddings=embeddings,
        metadatas=[{"test": "yes"}],
    )
    print(f"Added {count} docs")
    return {"added": count}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
