from typing import Optional
from datetime import datetime
from pathlib import Path
import json

from app.vector_stores.base import BaseVectorStore
from app.vector_stores.chroma_store import ChromaVectorStore
from app.vector_stores.faiss_store import FAISSVectorStore
from app.config import config


class CollectionMeta:
    """Metadata about a managed collection."""

    def __init__(
        self,
        name: str,
        backend: str,
        embedding_model: str,
        description: Optional[str] = None,
        metadata_schema: Optional[dict] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ):
        self.name = name
        self.backend = backend
        self.embedding_model = embedding_model
        self.description = description
        self.metadata_schema = metadata_schema
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.updated_at = updated_at or datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "backend": self.backend,
            "embedding_model": self.embedding_model,
            "description": self.description,
            "metadata_schema": self.metadata_schema,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class StoreManager:
    """Manages multiple vector store collections across backends."""

    def __init__(self):
        self._stores: dict[str, BaseVectorStore] = {}
        self._meta: dict[str, CollectionMeta] = {}
        self._registry_path = Path(config.storage.base_path) / "registry.json"

    def create_collection(
        self,
        name: str,
        backend: str = "chroma",
        embedding_model: str = "all-MiniLM-L6-v2",
        description: Optional[str] = None,
        metadata_schema: Optional[dict] = None,
        dimension: int = 384,
    ) -> BaseVectorStore:
        if name in self._stores:
            raise ValueError(f"Collection '{name}' already exists")

        if len(self._stores) >= config.api.max_collections:
            raise ValueError(f"Maximum collections ({config.api.max_collections}) reached")

        store = self._create_store(name, backend, dimension)
        meta = CollectionMeta(
            name=name,
            backend=backend,
            embedding_model=embedding_model,
            description=description,
            metadata_schema=metadata_schema,
        )

        self._stores[name] = store
        self._meta[name] = meta
        self._save_registry()

        return store

    def get_store(self, name: str) -> Optional[BaseVectorStore]:
        return self._stores.get(name)

    def get_meta(self, name: str) -> Optional[CollectionMeta]:
        return self._meta.get(name)

    def list_collections(self) -> list[dict]:
        collections = []
        for name, meta in self._meta.items():
            store = self._stores.get(name)
            info = meta.to_dict()
            info["document_count"] = store.count() if store else 0
            collections.append(info)
        return collections

    def update_collection(
        self,
        name: str,
        description: Optional[str] = None,
        metadata_schema: Optional[dict] = None,
    ) -> bool:
        meta = self._meta.get(name)
        if not meta:
            return False

        if description is not None:
            meta.description = description
        if metadata_schema is not None:
            meta.metadata_schema = metadata_schema
        meta.updated_at = datetime.utcnow().isoformat()

        self._save_registry()
        return True

    def delete_collection(self, name: str, permanent: bool = False) -> bool:
        if name not in self._stores:
            return False

        store = self._stores[name]
        store.clear()

        del self._stores[name]
        del self._meta[name]
        self._save_registry()
        return True

    def collection_exists(self, name: str) -> bool:
        return name in self._stores

    def persist_all(self) -> None:
        for store in self._stores.values():
            store.persist()
        self._save_registry()

    def load_all(self) -> None:
        """Load all collections from the registry on startup."""
        if not self._registry_path.exists():
            return

        try:
            with open(self._registry_path, "r") as f:
                registry = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return

        for entry in registry:
            name = entry["name"]
            backend = entry["backend"]
            try:
                dimension = self._get_dimension_for_model(entry.get("embedding_model", "all-MiniLM-L6-v2"))
                store = self._create_store(name, backend, dimension)
                self._stores[name] = store
                self._meta[name] = CollectionMeta(**entry)
            except Exception as e:
                print(f"⚠️ Failed to load collection '{name}': {e}")

    def _create_store(self, name: str, backend: str, dimension: int = 384) -> BaseVectorStore:
        if backend == "chroma":
            persist_dir = str(Path(config.storage.chroma.persist_directory) / name)
            return ChromaVectorStore(collection_name=name, persist_directory=persist_dir)
        elif backend == "faiss":
            return FAISSVectorStore(
                collection_name=name,
                persist_directory=config.storage.faiss.persist_directory,
                dimension=dimension,
                index_type=config.storage.faiss.index_type,
            )
        else:
            raise ValueError(f"Unknown backend: {backend}")

    def _save_registry(self) -> None:
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry = [meta.to_dict() for meta in self._meta.values()]
        with open(self._registry_path, "w") as f:
            json.dump(registry, f, indent=2)

    def _get_dimension_for_model(self, model_name: str) -> int:
        dimensions = {
            "all-MiniLM-L6-v2": 384,
            "all-MiniLM-L12-v2": 384,
            "all-mpnet-base-v2": 768,
            "paraphrase-MiniLM-L6-v2": 384,
            "multi-qa-MiniLM-L6-cos-v1": 384,
        }
        return dimensions.get(model_name, 384)


# Global store manager instance
store_manager = StoreManager()
