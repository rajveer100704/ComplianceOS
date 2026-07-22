import logging

logger = logging.getLogger("qdrant_collection_manager")

try:
    import qdrant_client
    from qdrant_client.http import models as qmodels
    from qdrant_client.http.exceptions import UnexpectedResponse

    QDRANT_CLIENT_AVAILABLE = True
except ImportError:
    QDRANT_CLIENT_AVAILABLE = False
    qdrant_client = None
    qmodels = None


class CollectionManager:
    """Manages creation, schema validation, named vectors, and migrations of Qdrant collections."""

    def __init__(self, client, collection_name: str, vector_name: str = "dense"):
        self.client = client
        self.collection_name = collection_name
        self.vector_name = vector_name

    def verify_or_create_collection(self, dimension: int, distance_str: str = "Cosine"):
        """Validates the schema of an existing collection or creates a new one with correct dimension."""
        if not QDRANT_CLIENT_AVAILABLE:
            raise ImportError("qdrant-client package is missing.")

        distance_map = {
            "Cosine": qmodels.Distance.COSINE,
            "Euclid": qmodels.Distance.EUCLID,
            "Dot": qmodels.Distance.DOT,
        }
        distance = distance_map.get(distance_str, qmodels.Distance.COSINE)

        try:
            collection_info = self.client.get_collection(self.collection_name)
            logger.info(
                f"Collection '{self.collection_name}' already exists. Validating schema..."
            )

            vectors_config = collection_info.config.params.vectors
            is_valid = False
            existing_dim = None
            existing_distance = None

            if isinstance(vectors_config, dict):
                if self.vector_name in vectors_config:
                    param = vectors_config[self.vector_name]
                    existing_dim = param.size
                    existing_distance = param.distance
                    if existing_dim == dimension and existing_distance == distance:
                        is_valid = True
            elif hasattr(vectors_config, "size"):
                existing_dim = vectors_config.size
                existing_distance = vectors_config.distance
                if existing_dim == dimension and existing_distance == distance:
                    is_valid = True

            if is_valid:
                logger.info(
                    f"Collection '{self.collection_name}' schema validated (dimension={dimension})."
                )
            else:
                logger.warning(
                    f"Collection '{self.collection_name}' schema mismatch! "
                    f"Expected dimension={dimension}, distance={distance}. "
                    f"Found existing dimension={existing_dim}, distance={existing_distance}. Recreating..."
                )
                self.recreate_collection(dimension, distance)

        except (UnexpectedResponse, Exception):
            logger.info(
                f"Collection '{self.collection_name}' does not exist. Creating new collection..."
            )
            self.recreate_collection(dimension, distance)

    def recreate_collection(self, dimension: int, distance):
        """Creates or recreates the collection with the correct named vector configuration."""
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                self.vector_name: qmodels.VectorParams(
                    size=dimension, distance=distance
                )
            },
        )
        logger.info(
            f"Collection '{self.collection_name}' created successfully with named vector '{self.vector_name}' (dimension={dimension})."
        )

    def get_health_status(self) -> dict:
        """Retrieves collection statistics and health metrics."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "status": "healthy",
                "points_count": info.points_count,
                "status_str": str(info.status),
                "vectors_count": info.vectors_count,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
