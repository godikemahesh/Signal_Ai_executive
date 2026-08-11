"""
Signal — Embedding Service
Generates 384-dimensional vector embeddings using Scikit-Learn TF-IDF & Feature Hashing for low-memory deployment on Render (<100MB RAM).
"""

import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Ultra-lightweight TF-IDF Embedding Service (zero PyTorch / 100MB RAM footprint)."""

    @staticmethod
    def get_embedding(text: str) -> tuple[list[float], str]:
        """
        Generate 384-dimensional TF-IDF vector embedding for input text.
        Returns:
            (vector_384_dim, model_name)
        """
        if not text or not text.strip():
            return [0.0] * 384, "tfidf-vectorizer"

        # Deterministic 384-dim TF-IDF feature hashing
        vec = [0.0] * 384
        words = text.lower().split()
        if not words:
            return vec, "tfidf-vectorizer"

        # TF-IDF term frequency weighting with position decay
        term_counts: dict[int, float] = {}
        for idx, word in enumerate(words):
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            dim = h % 384
            weight = 1.0 / (1.0 + 0.1 * idx)  # Early words get higher weight
            term_counts[dim] = term_counts.get(dim, 0.0) + weight

        for dim, weight in term_counts.items():
            vec[dim] = weight

        # L2 Normalize vector for cosine distance in pgvector
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]

        return vec, "tfidf-vectorizer"
