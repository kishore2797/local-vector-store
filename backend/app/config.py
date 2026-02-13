import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional


class ChromaConfig(BaseModel):
    persist_directory: str = "./vector_data/chroma"
    anonymized_telemetry: bool = False


class FAISSConfig(BaseModel):
    index_type: str = "Flat"  # Flat | IVFFlat | IVFPQ | HNSW
    nprobe: int = 10
    persist_directory: str = "./vector_data/faiss"


class StorageConfig(BaseModel):
    base_path: str = "./vector_data"
    default_backend: str = "chroma"  # chroma | faiss
    chroma: ChromaConfig = ChromaConfig()
    faiss: FAISSConfig = FAISSConfig()


class EmbeddingConfig(BaseModel):
    default_model: str = "all-MiniLM-L6-v2"
    device: str = "cpu"
    cache_dir: Optional[str] = None


class ChunkingConfig(BaseModel):
    default_strategy: str = "recursive"  # fixed | semantic | recursive
    default_chunk_size: int = 1000
    default_chunk_overlap: int = 200
    min_chunk_size: int = 50
    max_chunk_size: int = 5000


class APIConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    max_upload_size_mb: int = 50
    max_batch_size: int = 500
    max_collections: int = 50
    rate_limit_per_minute: int = 100


class AppConfig(BaseModel):
    storage: StorageConfig = StorageConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    chunking: ChunkingConfig = ChunkingConfig()
    api: APIConfig = APIConfig()


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from YAML file, falling back to defaults."""
    if config_path is None:
        config_path = os.environ.get(
            "CONFIG_PATH",
            str(Path(__file__).parent.parent.parent / "config.yaml")
        )

    config_path = Path(config_path)
    if config_path.exists():
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
        return AppConfig(**data)

    return AppConfig()


# Global config instance
config = load_config()
