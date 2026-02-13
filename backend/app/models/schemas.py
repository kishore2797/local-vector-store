from pydantic import BaseModel, Field
from typing import Optional, Any


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=100)
    search_type: str = "vector"  # vector | keyword | hybrid
    filters: Optional[dict[str, Any]] = None
    min_score: Optional[float] = None
    highlight: bool = False
    hybrid_config: Optional["HybridConfig"] = None


class HybridConfig(BaseModel):
    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    keyword_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    fusion_method: str = "weighted_sum"  # weighted_sum | rrf | relative_score


class MultiSearchRequest(BaseModel):
    queries: list[str] = Field(..., min_items=2, max_items=5)
    top_k: int = Field(default=5, ge=1, le=100)
    filters: Optional[dict[str, Any]] = None
    fusion_method: str = "rrf"


class SearchResult(BaseModel):
    id: str
    text: str
    metadata: dict[str, Any] = {}
    score: float = 0.0
    vector_score: Optional[float] = None
    keyword_score: Optional[float] = None
    combined_score: Optional[float] = None
    vector_rank: Optional[int] = None
    keyword_rank: Optional[int] = None
    highlighted_text: Optional[str] = None


class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str
    search_type: str
    total_results: int
    processing_time_ms: float


class CompareSearchResponse(BaseModel):
    vector_results: SearchResponse
    keyword_results: SearchResponse
    hybrid_results: SearchResponse
    overlap_analysis: dict[str, Any] = {}


class AutoTuneRequest(BaseModel):
    queries: list[str] = Field(..., min_items=5, max_items=20)
    relevant_ids: list[list[str]] = Field(..., min_items=5, max_items=20)
    top_k: int = 5


class AutoTuneResponse(BaseModel):
    optimal_vector_weight: float
    optimal_keyword_weight: float
    optimal_fusion_method: str
    metrics: dict[str, Any] = {}
    weight_grid_results: list[dict[str, Any]] = []


SearchRequest.model_rebuild()
