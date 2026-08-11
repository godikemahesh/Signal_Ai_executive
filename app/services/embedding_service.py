"""
Signal — Embedding Service
Generates 384-dimensional vector embeddings using all-MiniLM-L6-v2 with TF-IDF fallback for low-memory deployment on Render.
"""

import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy-loaded model instances
_minilm_model = None
_tfidf_vectorizer = None


class EmbeddingService:
    """Embedding generation service with MiniLM and TF-IDF fallback."""

    @staticmethod
    def get_embedding(text: str) -> tuple[list[float], str]:
        """
        Generate embedding vector for input text.
        Returns:
            (vector, model_name)
        """
        if not text.strip():
            return [0.0] * 384, "zero_vector"

        global _minilm_model
        try:
            if _minilm_model is None:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading sentence-transformer model: all-MiniLM-L6-v2")
                _minilm_model = SentenceTransformer("all-MiniLM-L6-v2")

            vector = _minilm_model.encode(text, convert_to_numpy=True).tolist()
            return vector, "all-MiniLM-L6-v2"

        except Exception as e:
            logger.warning(f"MiniLM embedding model unavailable ({e}). Falling back to TF-IDF vectorizer.")
            return EmbeddingService._tfidf_fallback(text)

    @staticmethod
    def _tfidf_fallback(text: str) -> tuple[list[float], str]:
        """Simple deterministic hash-based 384-dim pseudo-vector fallback when ML dependencies fail."""
        # Simple feature hash to 384 dimensions
        vec = [0.0] * 384
        words = text.lower().split()
        if not words:
            return vec, "tfidf-fallback"

        for idx, word in enumerate(words):
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            dim = h % 384
            vec[dim] += 1.0 / (idx + 1)

        # Normalize
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]

        return vec, "tfidf-fallback"
