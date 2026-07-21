from typing import List, Tuple
from retrieval.base import BaseReranker
from retrieval.models.chunk import Chunk
from retrieval.registry import register_reranker
from retrieval.models.manager import ModelManager


@register_reranker("cross_encoder")
class CrossEncoderReranker(BaseReranker):
    """Reranks candidate chunks using a local CrossEncoder model."""

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: str = "auto",
        warmup: bool = True,
    ):
        self.model_name = model_name
        self.device = device
        self.model = ModelManager.load_reranker_model(
            model_name, device=device, warmup=warmup
        )

    def rerank(
        self, query: str, candidates: List[Tuple[Chunk, float]]
    ) -> List[Tuple[Chunk, float]]:
        if not candidates:
            return []

        # Construct pairs of (query, document) for cross-attention inference
        pairs = [(query, chunk.text) for chunk, _ in candidates]

        # Predict scores in batches
        scores = self.model.predict(pairs, batch_size=32)

        # Merge scores and sort candidates
        reranked = [
            (candidates[i][0], float(scores[i])) for i in range(len(candidates))
        ]
        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked
