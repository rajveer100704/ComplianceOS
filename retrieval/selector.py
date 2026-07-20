from typing import List, Dict, Tuple, Any

class EvidenceSelector:
    """Selects top compliance evidence candidates matching thresholds to determine verdicts."""

    def __init__(self, thresholds: dict):
        self.thresholds = thresholds

    def select_evidence(self, candidates: list, scores: dict) -> dict:
        if not candidates:
            return {
                "status": "UNSUPPORTED",
                "citation": "—",
                "citation_title": "—",
                "snippet": "",
                "reason": "No regulation in the corpus sufficiently supports this claim."
            }

        # Select the best candidates based on scores (first candidate in list)
        best_chunk = candidates[0]
        # Get raw tf-idf / reranker score
        score_info = scores.get(best_chunk.chunk_id, {})
        
        # We can use 'rerank' score if present, else 'rrf' score, else 'dense' / 'bm25'
        best_score = score_info.get("rerank", score_info.get("dense", 0.0))

        support_thresh = self.thresholds.get("support", 0.35)
        partial_thresh = self.thresholds.get("partial", 0.15)

        if best_score >= support_thresh:
            status = "SUPPORTED"
            reason = "Claim terms strongly overlap with cited regulation."
        elif best_score >= partial_thresh:
            status = "PARTIAL"
            reason = "Some overlap found, but not enough specific terms match — needs engineer review."
        else:
            status = "UNSUPPORTED"
            reason = "No regulation in the corpus sufficiently supports this claim."

        return {
            "status": status,
            "score": best_score,
            "citation": best_chunk.metadata.get("id", "—") if status != "UNSUPPORTED" else "—",
            "citation_title": best_chunk.metadata.get("title", "—") if status != "UNSUPPORTED" else "—",
            "snippet": best_chunk.text if status != "UNSUPPORTED" else "",
            "reason": reason
        }
