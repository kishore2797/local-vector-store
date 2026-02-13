from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class DocumentInput(BaseModel):
    text: str = Field(..., min_length=1)
    metadata: Optional[dict[str, Any]] = None
    id: Optional[str] = None


class DocumentIngestRequest(BaseModel):
    documents: list[DocumentInput] = Field(..., min_items=1, max_items=500)
    on_conflict: str = "error"  # skip | upsert | error


class DocumentUpdateRequest(BaseModel):
    text: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class DocumentInfo(BaseModel):
    id: str
    text: str
    metadata: dict[str, Any] = {}
    char_count: int = 0
    token_estimate: int = 0
    created_at: Optional[datetime] = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total: int
    page: int
    limit: int


class DocumentDeleteByFilter(BaseModel):
    filter: dict[str, Any]


class DocumentDeleteByIds(BaseModel):
    ids: list[str]


class IngestResponse(BaseModel):
    ingested: int = 0
    skipped: int = 0
    errors: list[dict[str, str]] = []
    collection: str = ""
