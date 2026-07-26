"""Metric evaluators calculating Recall@K, MRR, Grounding Score, and Latency Telemetry."""

import logging
from typing import List

logger = logging.getLogger("evaluation.metrics.evaluators")


class MetricEvaluator:
    """Calculates quantitative benchmark evaluation metrics."""

    @staticmethod
    def calculate_recall_at_k(
        retrieved_ids: List[str], expected_ids: List[str], k: int = 5
    ) -> float:
        if not expected_ids:
            return 1.0
        top_k = retrieved_ids[:k]
        hits = set(top_k).intersection(set(expected_ids))
        return round(len(hits) / len(expected_ids), 4)

    @staticmethod
    def calculate_mrr(retrieved_ids: List[str], expected_ids: List[str]) -> float:
        if not expected_ids:
            return 1.0
        expected_set = set(expected_ids)
        for rank, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in expected_set:
                return round(1.0 / rank, 4)
        return 0.0

    @staticmethod
    def calculate_mean_grounding(scores: List[float]) -> float:
        if not scores:
            return 1.0
        return round(sum(scores) / len(scores), 4)
