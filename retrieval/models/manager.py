import logging
import torch

logger = logging.getLogger("model_manager")

try:
    from sentence_transformers import SentenceTransformer, CrossEncoder

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    CrossEncoder = None


class ModelManager:
    """Central manager handling lazy loading, device targeting, and warmup of local AI models."""

    _embedding_model = None
    _embedding_model_name = None
    _reranker_model = None
    _reranker_model_name = None

    @classmethod
    def get_device(cls, requested_device: str = "auto") -> str:
        """Determines the execution device: cuda, mps, or cpu."""
        if requested_device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
            return "cpu"
        return requested_device

    @classmethod
    def load_embedding_model(
        cls, model_name: str, device: str = "auto", warmup: bool = True
    ):
        """Loads and warms up the SentenceTransformer embedding model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers package is not installed. "
                "Please run: pip install sentence-transformers"
            )

        if cls._embedding_model is None or cls._embedding_model_name != model_name:
            target_device = cls.get_device(device)
            logger.info(
                f"Loading SentenceTransformer embedding model: {model_name} on {target_device}..."
            )
            cls._embedding_model = SentenceTransformer(model_name, device=target_device)
            cls._embedding_model_name = model_name

            if warmup:
                logger.info("Executing embedding model warmup...")
                cls._embedding_model.encode(
                    ["warmup task prompt"], convert_to_numpy=True
                )
                logger.info("Warmup complete.")

        return cls._embedding_model

    @classmethod
    def load_reranker_model(
        cls, model_name: str, device: str = "auto", warmup: bool = True
    ):
        """Loads and warms up the CrossEncoder reranker model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers package is not installed. "
                "Please run: pip install sentence-transformers"
            )

        if cls._reranker_model is None or cls._reranker_model_name != model_name:
            target_device = cls.get_device(device)
            logger.info(
                f"Loading CrossEncoder reranker model: {model_name} on {target_device}..."
            )
            cls._reranker_model = CrossEncoder(model_name, device=target_device)
            cls._reranker_model_name = model_name

            if warmup:
                logger.info("Executing reranker model warmup...")
                cls._reranker_model.predict([("warmup query", "warmup passage")])
                logger.info("Warmup complete.")

        return cls._reranker_model

    @classmethod
    def unload_models(cls):
        """Cleans up loaded models from memory/VRAM."""
        cls._embedding_model = None
        cls._embedding_model_name = None
        cls._reranker_model = None
        cls._reranker_model_name = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("All loaded model singletons unloaded.")
