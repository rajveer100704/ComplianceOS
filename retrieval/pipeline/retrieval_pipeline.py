from typing import List, Tuple
from retrieval.models.chunk import Chunk
from retrieval.models.retrieval_state import RetrievalState


class RetrievalPipeline:
    """DAG organizing CandidateGeneration, RRF Fusion, and Reranking pipeline nodes."""

    def __init__(self, dense_retriever, bm25_retriever, rrf, reranker):
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.rrf = rrf
        self.reranker = reranker

    def run(
        self,
        state: RetrievalState,
        planner_plan: dict,
        limit: int,
        filters: dict = None,
        profile_params: dict = None,
    ) -> List[Tuple[Chunk, float]]:
        # Retrieve candidate limits
        params = profile_params or {}
        dense_top_k = params.get("dense_top_k", 20)
        lexical_top_k = params.get("lexical_top_k", 20)
        rrf_k = params.get("rrf_k", 60)
        rerank_limit = params.get("rerank_limit", 5)

        # Candidate Generation
        dense_candidates = []
        if self.dense_retriever:
            dense_candidates = self.dense_retriever.retrieve(
                state.query, limit=dense_top_k, filters=filters
            )

        bm25_candidates = []
        if self.bm25_retriever:
            bm25_candidates = self.bm25_retriever.retrieve(
                state.query, limit=lexical_top_k, filters=filters
            )

        # Map candidate raw scores for explainability
        for chunk, score in dense_candidates:
            state.scores.setdefault(chunk.chunk_id, {})["dense"] = score
        for chunk, score in bm25_candidates:
            state.scores.setdefault(chunk.chunk_id, {})["bm25"] = score

        # RRF rank fusion
        fused = self.rrf.fuse(dense_candidates, bm25_candidates, limit=rrf_k)
        for chunk, score in fused:
            state.scores.setdefault(chunk.chunk_id, {})["rrf"] = score

        # Rerank candidates
        reranked = fused
        if self.reranker:
            to_rerank = fused[:rerank_limit]
            reranked = self.reranker.rerank(state.query, to_rerank)
            for chunk, score in reranked:
                state.scores.setdefault(chunk.chunk_id, {})["rerank"] = score

        state.candidates = reranked[:limit]
        return state.candidates
