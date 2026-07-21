from typing import Optional
from retrieval.base import (
    BaseChunker,
    BaseEmbeddingProvider,
    BaseVectorStore,
    BaseRetriever,
    BaseReranker,
)
from retrieval.registry import (
    CHUNKER_REGISTRY,
    EMBEDDING_REGISTRY,
    VECTOR_STORE_REGISTRY,
    RETRIEVER_REGISTRY,
    RERANKER_REGISTRY,
)


# Pre-import concrete classes dynamically or statically to execute registration decorators
def _import_registry_classes():
    try:
        from retrieval.chunkers.paragraph import ParagraphChunker
        from retrieval.chunkers.section import SectionChunker
        from retrieval.embeddings.tfidf import TFIDFEmbeddingProvider
        from retrieval.embeddings.bgem3 import BGEM3EmbeddingProvider
        from retrieval.stores.local import LocalVectorStore
        from retrieval.stores.qdrant import QdrantVectorStore
        from retrieval.retrievers.dense import DenseRetriever
        from retrieval.retrievers.bm25 import BM25Retriever
        from retrieval.retrievers.hybrid import HybridRetriever
        from retrieval.rerankers.cosine import CosineReranker
        from retrieval.rerankers.cross_encoder import CrossEncoderReranker
    except ImportError:
        pass


_import_registry_classes()


class RetrievalFactory:
    """Instantiates concrete retrieval components using config mapping registries."""

    @staticmethod
    def get_chunker(engine: str) -> BaseChunker:
        if engine not in CHUNKER_REGISTRY:
            raise ValueError(f"Unknown Chunker engine: {engine}")
        return CHUNKER_REGISTRY[engine]()

    @staticmethod
    def get_embedding(engine: str, **kwargs) -> BaseEmbeddingProvider:
        if engine not in EMBEDDING_REGISTRY:
            raise ValueError(f"Unknown Embedding engine: {engine}")
        return EMBEDDING_REGISTRY[engine](**kwargs)

    @staticmethod
    def get_vector_store(engine: str, **kwargs) -> BaseVectorStore:
        if engine not in VECTOR_STORE_REGISTRY:
            raise ValueError(f"Unknown Vector Store engine: {engine}")
        return VECTOR_STORE_REGISTRY[engine](**kwargs)

    @staticmethod
    def get_retriever(engine: str) -> BaseRetriever:
        if engine not in RETRIEVER_REGISTRY:
            raise ValueError(f"Unknown Retriever engine: {engine}")
        return RETRIEVER_REGISTRY[engine]()

    @staticmethod
    def get_reranker(engine: str, **kwargs) -> BaseReranker:
        if engine not in RERANKER_REGISTRY:
            raise ValueError(f"Unknown Reranker engine: {engine}")
        return RERANKER_REGISTRY[engine](**kwargs)
