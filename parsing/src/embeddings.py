import os
import logging
from typing import List, Optional
import numpy as np

logger = logging.getLogger(__name__)

class HuggingFaceEmbedder:
    """
    100% Free Hugging Face Embedder:
    - Generates 384-dimensional normalized vector embeddings for pgvector storage.
    - Automatically checks local './models/all-MiniLM-L6-v2' before fetching from HuggingFace Hub.
    - Supports both SentenceTransformers and FastEmbed backends with efficient batching.
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._st_model = None
        self._fastembed_model = None
        self._engine = None

    def _init_engine(self):
        """Initializes the embedding backend."""
        if self._engine is not None:
            return

        # Attempt 1: Try SentenceTransformer (local models folder or Hugging Face repository)
        try:
            from sentence_transformers import SentenceTransformer
            local_model_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "models", "all-MiniLM-L6-v2")
            )
            target_model = (
                local_model_path 
                if os.path.exists(os.path.join(local_model_path, "model.safetensors")) 
                else self.model_name
            )
            self._st_model = SentenceTransformer(target_model)
            self._engine = "sentence_transformers"
            logger.info(f"Initialized SentenceTransformer from '{target_model}' (384-dim).")
            return
        except Exception as e:
            logger.debug(f"SentenceTransformer initialization notice: {e}")

        # Attempt 2: Try FastEmbed (ONNX based)
        try:
            from fastembed import TextEmbedding
            self._fastembed_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
            self._engine = "fastembed"
            logger.info("Initialized FastEmbed (ONNX) with sentence-transformers/all-MiniLM-L6-v2 (384-dim).")
            return
        except Exception as e:
            logger.error(f"FastEmbed initialization failed: {e}")

        raise ImportError(
            "Neither 'sentence-transformers' nor 'fastembed' could be loaded. "
            "Please run: pip install sentence-transformers fastembed"
        )

    def embed_query(self, text: str) -> List[float]:
        """
        Generates a 384-dimensional normalized vector embedding for a single text query.
        Returns a list of native Python floats for direct pgvector insertion.
        """
        if not text or not text.strip():
            return [0.0] * 384

        try:
            self._init_engine()
            if self._engine == "sentence_transformers" and self._st_model:
                emb = self._st_model.encode(text, normalize_embeddings=True, show_progress_bar=False)
                return [float(x) for x in emb.tolist()]
            elif self._engine == "fastembed" and self._fastembed_model:
                embeddings = list(self._fastembed_model.embed([text]))
                return [float(x) for x in embeddings[0].tolist()]
        except Exception as e:
            logger.error(f"Error during embedding generation: {e}", exc_info=True)
            raise

        return [0.0] * 384

    def embed_documents(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generates 384-dimensional normalized vector embeddings for a list of documents.
        Uses optimized batch encoding for maximum throughput.
        """
        if not texts:
            return []

        # Filter and track non-empty texts
        valid_indices = [i for i, t in enumerate(texts) if t and t.strip()]
        valid_texts = [texts[i] for i in valid_indices]

        # Allocate placeholder results
        results: List[List[float]] = [[0.0] * 384 for _ in range(len(texts))]
        if not valid_texts:
            return results

        try:
            self._init_engine()
            if self._engine == "sentence_transformers" and self._st_model:
                batch_embeddings = self._st_model.encode(
                    valid_texts,
                    batch_size=batch_size,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                for orig_idx, emb in zip(valid_indices, batch_embeddings):
                    results[orig_idx] = [float(x) for x in emb.tolist()]
                return results

            elif self._engine == "fastembed" and self._fastembed_model:
                batch_embeddings = list(self._fastembed_model.embed(valid_texts, batch_size=batch_size))
                for orig_idx, emb in zip(valid_indices, batch_embeddings):
                    results[orig_idx] = [float(x) for x in emb.tolist()]
                return results

        except Exception as e:
            logger.error(f"Error during batch embedding generation: {e}", exc_info=True)
            raise

        return results
