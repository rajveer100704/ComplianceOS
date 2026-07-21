from typing import List, Tuple
from retrieval.base import BaseRetriever, BaseEmbeddingProvider, BaseVectorStore
from retrieval.capabilities import RetrieverCapabilities
from retrieval.models.chunk import Chunk
from retrieval.registry import register_retriever


@register_retriever("dense")
class DenseRetriever(BaseRetriever):
    """Executes dense vector search operations over the configured vector database."""

    def __init__(
        self, embedding_provider: BaseEmbeddingProvider, vector_store: BaseVectorStore
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store

    @property
    def capabilities(self) -> RetrieverCapabilities:
        return RetrieverCapabilities(hybrid=False, metadata=True, filters=True)

    def retrieve(
        self, query: str, limit: int, filters: dict = None
    ) -> List[Tuple[Chunk, float]]:
        query_vector = self.embedding_provider.embed_query(query)
        return self.vector_store.search(query_vector, limit, filters)
