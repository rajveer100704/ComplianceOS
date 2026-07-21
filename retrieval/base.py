from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from retrieval.models.chunk import Chunk
from retrieval.capabilities import (
    RetrieverCapabilities,
    EmbeddingCapabilities,
    VectorStoreCapabilities,
)


class BaseChunker(ABC):
    """Abstract Base Class for all chunking engines."""

    @abstractmethod
    def chunk(self, doc_id: int, text: str, doc_metadata: dict) -> List[Chunk]:
        """Splits document text into a list of Chunk objects."""
        pass


class BaseEmbeddingProvider(ABC):
    """Abstract Base Class for all embedding models."""

    @property
    @abstractmethod
    def capabilities(self) -> EmbeddingCapabilities:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Computes dense vector representation for a query."""
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Computes dense vector representations for multiple texts."""
        pass


class BaseVectorStore(ABC):
    """Abstract Base Class for all vector database backends."""

    @property
    @abstractmethod
    def capabilities(self) -> VectorStoreCapabilities:
        pass

    @abstractmethod
    def upsert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        """Indexes chunks and their embeddings into the store."""
        pass

    @abstractmethod
    def search(
        self, query_vector: List[float], limit: int, filters: dict = None
    ) -> List[Tuple[Chunk, float]]:
        """Finds top-k nearest neighbor chunks based on distance."""
        pass

    @abstractmethod
    def delete(self, doc_id: int) -> None:
        """Deletes all chunks belonging to a document ID."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Flushes all documents and vectors from the store."""
        pass


class BaseRetriever(ABC):
    """Abstract Base Class for all document retrievers."""

    @property
    @abstractmethod
    def capabilities(self) -> RetrieverCapabilities:
        pass

    @abstractmethod
    def retrieve(
        self, query: str, limit: int, filters: dict = None
    ) -> List[Tuple[Chunk, float]]:
        """Retrieves matching document chunks for a query."""
        pass


class BaseReranker(ABC):
    """Abstract Base Class for all reranking algorithms."""

    @abstractmethod
    def rerank(
        self, query: str, candidates: List[Tuple[Chunk, float]]
    ) -> List[Tuple[Chunk, float]]:
        """Reranks candidate results with a secondary model score."""
        pass
