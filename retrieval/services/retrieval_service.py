import time
import uuid
import logging
from typing import Dict, Any, List, Tuple

from retrieval.base import (
    BaseEmbeddingProvider,
    BaseVectorStore,
    BaseRetriever,
    BaseReranker,
)
from retrieval.contracts.query import RetrievalQuery
from retrieval.contracts.response import RetrievalResponse
from retrieval.models.retrieval_session import RetrievalSession
from retrieval.models.retrieval_state import RetrievalState
from retrieval.models.evidence_bundle import EvidenceBundle
from retrieval.middleware.validation import RetrievalValidationMiddleware
from retrieval.middleware.timing import RetrievalTimingMiddleware
from retrieval.pipeline.retrieval_pipeline import RetrievalPipeline
from retrieval.pipeline.context_builder import ContextBuilder
from retrieval.fusion.rrf import ReciprocalRankFusion
from retrieval.retrievers.dense import DenseRetriever
from retrieval.retrievers.bm25 import BM25Retriever
from retrieval.selector import EvidenceSelector
from retrieval.config.loader import ConfigLoader
from retrieval.evaluation.query_classifier import QueryClassifier
from retrieval.observability.timing import measure_time

logger = logging.getLogger("retrieval_service")


class CachedEmbeddingProviderProxy:
    """Wraps an embedding provider to cache query embeddings and count hits/misses."""

    def __init__(self, provider: BaseEmbeddingProvider, cache):
        self.provider = provider
        self.cache = cache
        self.cache_hits = 0
        self.cache_misses = 0

    @property
    def version(self) -> str:
        return self.provider.version

    @property
    def capabilities(self):
        return self.provider.capabilities

    @property
    def model_name(self) -> str:
        return getattr(self.provider, "model_name", "unknown")

    def embed_query(self, query: str) -> List[float]:
        if not self.cache:
            return self.provider.embed_query(query)
        model_name = self.model_name
        model_version = self.version
        cached = self.cache.get(query, model_name, model_version)
        if cached is not None:
            self.cache_hits += 1
            return cached

        self.cache_misses += 1
        vec = self.provider.embed_query(query)
        self.cache.set(query, model_name, model_version, len(vec), vec)
        return vec

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        return self.provider.embed_documents(documents)


class RetrievalService:
    """Orchestrates query validations, timing checks, candidate DAG running, and receipt formatting."""

    def __init__(
        self,
        embedding_provider: BaseEmbeddingProvider,
        vector_store: BaseVectorStore,
        planner,
        reranker: BaseReranker = None,
        cache=None,
    ):
        self.raw_embedding_provider = embedding_provider
        if cache:
            self.embedding_provider = CachedEmbeddingProviderProxy(
                embedding_provider, cache
            )
        else:
            self.embedding_provider = embedding_provider

        self.vector_store = vector_store
        self.planner = planner
        self.reranker = reranker
        self.cache = cache

        # Assemble child retrievers
        self.dense_retriever = DenseRetriever(self.embedding_provider, vector_store)
        self.bm25_retriever = BM25Retriever(vector_store)
        self.rrf = ReciprocalRankFusion()
        self.pipeline = RetrievalPipeline(
            self.dense_retriever, self.bm25_retriever, self.rrf, reranker
        )

    def retrieve(
        self, query: str, limit: int = 5, filters: dict = None, profile: str = None
    ) -> EvidenceBundle:
        # 1. Validation
        RetrievalValidationMiddleware.validate_query(query, limit)

        # 2. Timing
        timer = RetrievalTimingMiddleware()
        timer.start()

        # 3. Session and State Setup
        session_id = str(uuid.uuid4())
        session = RetrievalSession(
            session_id=session_id, request_id=0, run_id=0, query_id=str(uuid.uuid4())
        )
        state = RetrievalState(query=query, session_id=session_id)

        # 4. Resolve Active Search Profile & Dynamic Overrides
        config = ConfigLoader.load()
        ret_conf = config.get("retrieval", {})
        active_prof = profile or ret_conf.get("active_profile", "balanced")

        profiles = ret_conf.get(
            "profiles",
            {
                "fast": {
                    "dense_top_k": 10,
                    "lexical_top_k": 10,
                    "rrf_k": 40,
                    "rerank_limit": 3,
                },
                "balanced": {
                    "dense_top_k": 20,
                    "lexical_top_k": 20,
                    "rrf_k": 60,
                    "rerank_limit": 5,
                },
                "quality": {
                    "dense_top_k": 50,
                    "lexical_top_k": 50,
                    "rrf_k": 60,
                    "rerank_limit": 10,
                },
            },
        )

        prof_params = profiles.get(active_prof, profiles["balanced"]).copy()

        # 5. Heuristic Query Classifier for Adaptive Top-K Routing
        difficulty = QueryClassifier.classify(query)

        adaptive_enabled = ret_conf.get("adaptive", {}).get("enabled", True)
        if adaptive_enabled:
            if difficulty == "easy":
                prof_params["dense_top_k"] = max(
                    10, int(prof_params["dense_top_k"] * 0.5)
                )
                prof_params["lexical_top_k"] = max(
                    10, int(prof_params["lexical_top_k"] * 0.5)
                )
                prof_params["rerank_limit"] = max(
                    2, int(prof_params["rerank_limit"] * 0.5)
                )
            elif difficulty == "hard":
                prof_params["dense_top_k"] = int(prof_params["dense_top_k"] * 1.5)
                prof_params["lexical_top_k"] = int(prof_params["lexical_top_k"] * 1.5)
                prof_params["rerank_limit"] = int(prof_params["rerank_limit"] * 1.5)

        # 6. Planning
        plan = self.planner.get_plan(query)

        # 7. Execute Retrieval Pipeline DAG with Detailed Observability timings
        embedding_lat = 0.0
        retrieval_lat = 0.0
        rerank_lat = 0.0

        # Measure Embedding Generation
        with measure_time() as t:
            query_vector = self.embedding_provider.embed_query(query)
        embedding_lat = t["elapsed_ms"]

        # Override embed_query on provider to yield fast cached vector
        original_embed = self.dense_retriever.embedding_provider.embed_query
        self.dense_retriever.embedding_provider.embed_query = lambda q: query_vector

        # Measure Vector Store Search + BM25 Candidate Generation
        with measure_time() as t:
            # Execute search
            candidates = self.pipeline.run(
                state, plan, limit, filters=filters, profile_params=prof_params
            )
        retrieval_lat = t["elapsed_ms"]

        # Restore original method
        self.dense_retriever.embedding_provider.embed_query = original_embed

        # 8. Context neighbor expansion
        expanded_chunks = ContextBuilder.expand_context(candidates)

        # 9. Evidence Selection
        selector = EvidenceSelector(plan["thresholds"])
        verdict_results = selector.select_evidence(expanded_chunks, state.scores)

        # Calculate cache hit ratio
        cache_hit_ratio = 0.0
        if isinstance(self.embedding_provider, CachedEmbeddingProviderProxy):
            total = (
                self.embedding_provider.cache_hits
                + self.embedding_provider.cache_misses
            )
            if total > 0:
                cache_hit_ratio = float(self.embedding_provider.cache_hits) / total

        # Compile Latency & Receipt
        latency_ms = timer.elapsed_ms()
        receipt = {
            "query": query,
            "chunker": "section-aware",
            "embedding_model": self.embedding_provider.version,
            "vector_store": "local",
            "retriever": plan["engine"],
            "strategy": plan["strategy"],
            "policy": plan["policy"],
            "dense_candidates": len(state.scores),
            "bm25_candidates": len(state.scores),
            "selected": len(expanded_chunks),
            "latency_ms": latency_ms,
            "explainability": state.scores,
            "profile": active_prof,
            "difficulty": difficulty,
            "cache_hit_ratio": cache_hit_ratio,
            "stage_latency": {
                "embedding_ms": round(embedding_lat, 2),
                "retrieval_ms": round(retrieval_lat, 2),
                "reranking_ms": round(latency_ms - embedding_lat - retrieval_lat, 2),
            },
        }

        # Build document provenance mapping
        doc_prov = {}
        for c in expanded_chunks:
            doc_prov[c.document_id] = c.metadata.get("filename", f"Doc-{c.document_id}")

        page_numbers = list(set(c.metadata.get("page", 1) for c in expanded_chunks))

        return EvidenceBundle(
            query=query,
            chunks=expanded_chunks,
            scores=state.scores,
            document_provenance=doc_prov,
            page_numbers=page_numbers,
            selection_reason=verdict_results.get("reason", ""),
            receipt=receipt,
        )
