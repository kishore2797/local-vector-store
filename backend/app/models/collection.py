from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_-]+$")
    description: Optional[str] = None
    embedding_model: str = "all-MiniLM-L6-v2"
    backend: str = "chroma"  # chroma | faiss
    metadata_schema: Optional[dict] = None


class CollectionUpdate(BaseModel):
    description: Optional[str] = None
    metadata_schema: Optional[dict] = None


class CollectionInfo(BaseModel):
    name: str
    description: Optional[str] = None
    embedding_model: str
    backend: str
    document_count: int = 0
    embedding_dimension: int = 0
    disk_size_bytes: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class CollectionListResponse(BaseModel):
    collections: list[CollectionInfo]
    total: int
