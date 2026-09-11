import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

class HuggingFaceEmbedder:
    """
    Hugging Face Embedder for generating 384-dimensional normalized vector embeddings
    for Supabase pgvector semantic search (using all-MiniLM-L6-v2).
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._st_model = None
        self._fastembed_model = None
        self._engine = None

    def _init_engine(self):
        if self._engine is not None:
            return

        # Attempt 1: SentenceTransformer
        try:
            from sentence_transformers import SentenceTransformer
            # Check local models folder if available
            local_model_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "parsing", "models", "all-MiniLM-L6-v2")
            )
            target_model = (
                local_model_path
                if os.path.exists(os.path.join(local_model_path, "model.safetensors"))
                else self.model_name
            )
            self._st_model = SentenceTransformer(target_model)
            self._engine = "sentence_transformers"
            logger.info(f"Initialized SentenceTransformer with '{target_model}' (384-dim).")
            return
        except Exception as e:
            logger.debug(f"SentenceTransformer init notice: {e}")

        # Attempt 2: FastEmbed
        try:
            from fastembed import TextEmbedding
            self._fastembed_model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
            self._engine = "fastembed"
            logger.info("Initialized FastEmbed (ONNX) with sentence-transformers/all-MiniLM-L6-v2 (384-dim).")
            return
        except Exception as e:
            logger.debug(f"FastEmbed init notice: {e}")

        logger.warning("No embedding engine could be loaded. Embeddings will default to zero vectors.")
        self._engine = "none"

    def embed_query(self, text: str) -> List[float]:
        """
        Generates a 384-dimensional normalized vector embedding for a single text query.
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

        return [0.0] * 384

embedder = HuggingFaceEmbedder()
