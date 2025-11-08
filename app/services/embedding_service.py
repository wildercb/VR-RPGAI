"""Embedding generation service for semantic memory retrieval."""
from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from loguru import logger


class EmbeddingService:
    """
    Singleton service for generating text embeddings.

    Uses sentence-transformers for fast, local embedding generation.
    Model: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
    """

    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._model is None:
            logger.info("Loading embedding model: all-MiniLM-L6-v2")
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded")

    def encode(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            384-dimensional embedding vector
        """
        return self._model.encode(text, convert_to_numpy=True)

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            Array of embedding vectors
        """
        return self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0 to 1)
        """
        return float(np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))


# Global singleton instance
embedding_service = EmbeddingService()
