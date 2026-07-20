from typing import List, Set, Tuple

class RetrievalMetrics:
    """Computes standard information retrieval metrics (Recall, Precision, MRR, nDCG)."""

    @staticmethod
    def precision_at_k(retrieved: List[Tuple[int, int]], expected: Set[Tuple[int, int]], k: int) -> float:
        """Computes Precision@k: fraction of retrieved documents that are relevant."""
        if k <= 0:
            return 0.0
        retrieved_k = retrieved[:k]
        relevant_retrieved = sum(1 for item in retrieved_k if item in expected)
        return relevant_retrieved / k

    @staticmethod
    def recall_at_k(retrieved: List[Tuple[int, int]], expected: Set[Tuple[int, int]], k: int) -> float:
        """Computes Recall@k: fraction of relevant documents that are retrieved."""
        if not expected:
            return 0.0
        retrieved_k = retrieved[:k]
        relevant_retrieved = sum(1 for item in retrieved_k if item in expected)
        return relevant_retrieved / len(expected)

    @staticmethod
    def reciprocal_rank(retrieved: List[Tuple[int, int]], expected: Set[Tuple[int, int]]) -> float:
        """Computes Reciprocal Rank (RR): reciprocal of the rank of the first correct match."""
        for rank, item in enumerate(retrieved):
            if item in expected:
                return 1.0 / (rank + 1)
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved: List[Tuple[int, int]], expected: Set[Tuple[int, int]], k: int) -> float:
        """Computes Normalized Discounted Cumulative Gain (nDCG@k)."""
        import math
        if k <= 0 or not expected:
            return 0.0

        retrieved_k = retrieved[:k]
        dcg = 0.0
        for rank, item in enumerate(retrieved_k):
            if item in expected:
                dcg += 1.0 / math.log2(rank + 2)

        idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(expected), k)))

        if idcg == 0:
            return 0.0
        return dcg / idcg
