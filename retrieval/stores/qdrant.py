import uuid
import logging
from typing import List, Tuple
from retrieval.base import BaseVectorStore
from retrieval.capabilities import VectorStoreCapabilities
from retrieval.registry import register_vector_store
from retrieval.models.chunk import Chunk
from retrieval.stores.collection_manager import CollectionManager

logger = logging.getLogger("qdrant_vector_store")

try:
    import qdrant_client
    from qdrant_client.http import models as qmodels

    QDRANT_CLIENT_AVAILABLE = True
except ImportError:
    QDRANT_CLIENT_AVAILABLE = False
    qmodels = None


@register_vector_store("qdrant")
class QdrantVectorStore(BaseVectorStore):
    """Production Qdrant vector database engine supporting named vectors, schema checks, and fallback."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection: str = "compliance_chunks",
        vector_name: str = "dense",
        timeout: float = 5.0,
    ):
        if not QDRANT_CLIENT_AVAILABLE:
            raise ImportError(
                "Qdrant dependencies (qdrant-client) are not installed in the current environment."
            )

        self.url = url
        self.collection_name = collection
        self.vector_name = vector_name
        self.timeout = timeout

        try:
            # Initialize connection to Qdrant server
            self.client = qdrant_client.QdrantClient(url=url, timeout=timeout)
            # Instanciate CollectionManager
            self.collection_manager = CollectionManager(
                self.client, collection, vector_name
            )
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant at {url}: {e}")
            raise ConnectionError(f"Could not connect to Qdrant server at {url}: {e}")

    @property
    def capabilities(self) -> VectorStoreCapabilities:
        return VectorStoreCapabilities(filtering=True, hybrid=True)

    def upsert(self, chunks: List[Chunk], embeddings: List[List[float]]) -> None:
        """Converts chunks and dense vectors to Qdrant PointStruct items and uploads them."""
        if not chunks:
            return

        points = []
        for chunk, embedding in zip(chunks, embeddings):
            # Compute a deterministic UUID based on chunk text hash or ID
            para_idx = chunk.metadata.get("paragraph_index", 0)
            point_id = str(
                uuid.uuid5(uuid.NAMESPACE_DNS, f"{chunk.document_id}_{para_idx}")
            )

            # Map Chunk properties to payload
            payload = {
                "doc_id": chunk.document_id,
                "index": para_idx,
                "text": chunk.text,
                "metadata": chunk.metadata,
            }

            # Use named vector format
            vector_payload = {self.vector_name: embedding}

            points.append(
                qmodels.PointStruct(id=point_id, vector=vector_payload, payload=payload)
            )

        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(
            f"Upserted {len(chunks)} points to Qdrant collection '{self.collection_name}'."
        )

    def search(
        self, query_vector: List[float], limit: int, filters: dict = None
    ) -> List[Tuple[Chunk, float]]:
        """Executes point vector queries on Qdrant, supporting filter conditions."""
        # Convert dictionary filters to Qdrant Filter models if present
        query_filter = None
        if filters:
            conditions = []
            for key, val in filters.items():
                conditions.append(
                    qmodels.FieldCondition(key=key, match=qmodels.MatchValue(value=val))
                )
            if conditions:
                query_filter = qmodels.Filter(must=conditions)

        # Search with the named vector
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=(self.vector_name, query_vector),
            limit=limit,
            query_filter=query_filter,
        )

        results = []
        for hit in search_result:
            payload = hit.payload
            chunk = Chunk(
                chunk_id=payload.get(
                    "chunk_id", f"{payload['doc_id']}_{payload['index']}"
                ),
                document_id=payload["doc_id"],
                text=payload["text"],
                metadata=payload["metadata"],
            )
            # Qdrant scores can be cosine similarity (between -1.0 and 1.0 or 0.0 and 1.0)
            results.append((chunk, float(hit.score)))

        return results

    def delete(self, doc_id: int) -> None:
        """Deletes all vector points associated with the specified document ID."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qmodels.FilterSelector(
                filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="doc_id", match=qmodels.MatchValue(value=doc_id)
                        )
                    ]
                )
            ),
        )
        logger.info(
            f"Deleted points for doc_id {doc_id} from Qdrant collection '{self.collection_name}'."
        )

    def clear(self) -> None:
        """Flushes the collection."""
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        # Recreate schema (assuming a default dimension of 384 or matching prior config)
        # Note: Usually called in tests. In actual runs, CollectionManager recreates on schema verification.
        self.collection_manager.recreate_collection(384, qmodels.Distance.COSINE)
