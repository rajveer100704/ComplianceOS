from retrieval.base import BaseEmbeddingProvider
from retrieval.capabilities import EmbeddingCapabilities
from retrieval.registry import register_embedding
from retrieval.models.manager import ModelManager
import logging

logger = logging.getLogger("bgem3_provider")


@register_embedding("bgem3")
class BGEM3EmbeddingProvider(BaseEmbeddingProvider):
    """Provides dense representations using a SentenceTransformers BGE model."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
        device: str = "auto",
        warmup: bool = True,
    ):
        self.model_name = model_name
        self.device = device

        self.model = ModelManager.load_embedding_model(
            model_name, device=device, warmup=warmup
        )
        self.dimension = self.model.get_sentence_embedding_dimension()

    @property
    def capabilities(self) -> EmbeddingCapabilities:
        return EmbeddingCapabilities(multivector=False, dimensions=self.dimension)

    @property
    def version(self) -> str:
        return f"{self.model_name}_{self.dimension}_v1"

    def embed_query(self, query: str) -> list[float]:
        vec = self.model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        return [float(v) for v in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vecs = self.model.encode(
            texts, batch_size=32, convert_to_numpy=True, normalize_embeddings=True
        )
        return [[float(v) for v in row] for row in vecs]
