from typing import List
from retrieval.models.chunk import Chunk
from retrieval.base import BaseEmbeddingProvider, BaseVectorStore

from typing import List
import time
import logging
from retrieval.models.chunk import Chunk
from retrieval.base import BaseEmbeddingProvider, BaseVectorStore

logger = logging.getLogger("index_builder")


class IndexBuilder:
    """Performs batched caching, incremental updates, and document deletions in vector stores."""

    def __init__(
        self,
        embedding_provider: BaseEmbeddingProvider,
        vector_store: BaseVectorStore,
        cache=None,
    ):
        self.embedding_provider = embedding_provider
        self.vector_store = vector_store
        self.cache = cache

    def build_index(self, chunks: List[Chunk]) -> None:
        """Embeds and indexes document chunks with caching support and observability metrics."""
        if not chunks:
            return

        start_time = time.perf_counter()
        embeddings = [None] * len(chunks)
        uncached_indices = []
        uncached_texts = []

        model_name = getattr(self.embedding_provider, "model_name", "unknown")
        model_version = self.embedding_provider.version
        dimension = self.embedding_provider.capabilities.dimensions

        # 1. Resolve cached embeddings
        if self.cache:
            for idx, chunk in enumerate(chunks):
                cached_vec = self.cache.get(chunk.text, model_name, model_version)
                if cached_vec is not None:
                    embeddings[idx] = cached_vec
                else:
                    uncached_indices.append(idx)
                    uncached_texts.append(chunk.text)
        else:
            uncached_indices = list(range(len(chunks)))
            uncached_texts = [c.text for c in chunks]

        # 2. Run batched model inference for any cache misses
        if uncached_texts:
            logger.info(
                f"Computing embeddings for {len(uncached_texts)} chunks (cache misses)..."
            )
            embed_start = time.perf_counter()
            new_embeddings = self.embedding_provider.embed_documents(uncached_texts)
            embed_duration = time.perf_counter() - embed_start

            # Print observability statistics
            logger.info(
                f"Embedding batch inference completed in {embed_duration:.4f}s."
            )

            # Store in cache and populate full list
            for idx, local_idx in enumerate(uncached_indices):
                vec = new_embeddings[idx]
                embeddings[local_idx] = vec
                if self.cache:
                    self.cache.set(
                        chunk.text, model_name, model_version, dimension, vec
                    )

        # 3. Upsert to vector store
        logger.info(f"Upserting {len(chunks)} points to vector store...")
        upsert_start = time.perf_counter()
        self.vector_store.upsert(chunks, embeddings)
        upsert_duration = time.perf_counter() - upsert_start

        duration = time.perf_counter() - start_time
        hit_rate = 1.0 - (len(uncached_texts) / len(chunks)) if chunks else 0.0

        logger.info(
            f"Indexing complete in {duration:.4f}s. "
            f"Cache hits: {len(chunks) - len(uncached_texts)}/{len(chunks)} ({hit_rate*100:.1f}%). "
            f"Upsert latency: {upsert_duration:.4f}s."
        )

    def incremental_update(self, chunks: List[Chunk]) -> None:
        """Upserts new chunks into the vector store."""
        self.build_index(chunks)

    def delete_document(self, doc_id: int) -> None:
        """Deletes all vector store records matching document ID."""
        self.vector_store.delete(doc_id)
