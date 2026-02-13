from sentence_transformers import SentenceTransformer
from typing import Optional

from app.config import config


class EmbeddingManager:
    """Manages embedding model loading and inference with caching."""

    def __init__(self):
        self._models: dict[str, SentenceTransformer] = {}

    def get_model(self, model_name: Optional[str] = None) -> SentenceTransformer:
        model_name = model_name or config.embedding.default_model
        if model_name not in self._models:
            self._models[model_name] = SentenceTransformer(
                model_name,
                device=config.embedding.device,
                cache_folder=config.embedding.cache_dir,
            )
        return self._models[model_name]

    def embed_texts(self, texts: list[str], model_name: Optional[str] = None) -> list[list[float]]:
        model = self.get_model(model_name)
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str, model_name: Optional[str] = None) -> list[float]:
        model = self.get_model(model_name)
        embedding = model.encode(query, show_progress_bar=False, normalize_embeddings=True)
        return embedding.tolist()

    def get_dimension(self, model_name: Optional[str] = None) -> int:
        model = self.get_model(model_name)
        return model.get_sentence_embedding_dimension()

    def available_models(self) -> list[dict]:
        return [
            {"name": "all-MiniLM-L6-v2", "dimension": 384, "description": "Fast, good quality (default)"},
            {"name": "all-MiniLM-L12-v2", "dimension": 384, "description": "Better quality, slightly slower"},
            {"name": "all-mpnet-base-v2", "dimension": 768, "description": "Best quality, slower"},
            {"name": "paraphrase-MiniLM-L6-v2", "dimension": 384, "description": "Optimized for paraphrase detection"},
            {"name": "multi-qa-MiniLM-L6-cos-v1", "dimension": 384, "description": "Optimized for Q&A retrieval"},
        ]


# Global embedding manager instance
embedding_manager = EmbeddingManager()
