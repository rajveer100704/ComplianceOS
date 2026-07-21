class FeatureFlags:
    """Centralized toggles governing features availability in query flows."""

    def __init__(
        self,
        enable_rrf: bool = True,
        enable_reranker: bool = True,
        enable_cache: bool = True,
        enable_receipts: bool = True,
        enable_observability: bool = True,
    ):
        self.enable_rrf = enable_rrf
        self.enable_reranker = enable_reranker
        self.enable_cache = enable_cache
        self.enable_receipts = enable_receipts
        self.enable_observability = enable_observability

    def to_dict(self) -> dict:
        return {
            "enable_rrf": self.enable_rrf,
            "enable_reranker": self.enable_reranker,
            "enable_cache": self.enable_cache,
            "enable_receipts": self.enable_receipts,
            "enable_observability": self.enable_observability,
        }
