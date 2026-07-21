class RetrieverCapabilities:
    """Feature support flag mapping for document retrievers."""

    def __init__(
        self,
        hybrid: bool = False,
        metadata: bool = True,
        filters: bool = True,
        multivector: bool = False,
    ):
        self.hybrid = hybrid
        self.metadata = metadata
        self.filters = filters
        self.multivector = multivector

    def to_dict(self) -> dict:
        return {
            "hybrid": self.hybrid,
            "metadata": self.metadata,
            "filters": self.filters,
            "multivector": self.multivector,
        }


class EmbeddingCapabilities:
    """Feature support flag mapping for embedding models."""

    def __init__(self, multivector: bool = False, dimensions: int = 512):
        self.multivector = multivector
        self.dimensions = dimensions

    def to_dict(self) -> dict:
        return {"multivector": self.multivector, "dimensions": self.dimensions}


class VectorStoreCapabilities:
    """Feature support flag mapping for vector databases."""

    def __init__(
        self,
        filtering: bool = True,
        hybrid: bool = False,
        distance_metrics: list = None,
    ):
        self.filtering = filtering
        self.hybrid = hybrid
        self.distance_metrics = distance_metrics or ["cosine"]

    def to_dict(self) -> dict:
        return {
            "filtering": self.filtering,
            "hybrid": self.hybrid,
            "distance_metrics": self.distance_metrics,
        }
