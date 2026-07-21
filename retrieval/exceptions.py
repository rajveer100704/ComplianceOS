class RetrievalError(Exception):
    """Base exception for all retrieval subsystem errors."""

    pass


class ChunkingError(RetrievalError):
    """Raised when document segmentation fails."""

    pass


class EmbeddingError(RetrievalError):
    """Raised when generating vector embeddings fails."""

    pass


class VectorStoreError(RetrievalError):
    """Raised when interacting with the vector database fails."""

    pass


class RerankerError(RetrievalError):
    """Raised when cross-encoder or vector scoring fails."""

    pass
