import logging
from typing import Optional
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY as DEFAULT_REGISTRY,
)

logger = logging.getLogger("observability_metrics")


class MetricsService:
    """Decoupled metrics facade managing Prometheus counters, histograms, and gauges."""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or DEFAULT_REGISTRY

        # HTTP Requests & Performance
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests received",
            ["method", "endpoint", "status_code"],
            registry=self.registry,
        )
        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request handling latency in seconds",
            ["method", "endpoint"],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry,
        )

        # Multi-tenancy & Session Gauges
        self.active_sessions = Gauge(
            "active_sessions_count",
            "Number of currently active user sessions",
            registry=self.registry,
        )
        self.organization_count = Gauge(
            "organization_count",
            "Total provisioned organizations",
            registry=self.registry,
        )

        # Storage & Report Counters
        self.documents_uploaded_total = Counter(
            "documents_uploaded_total",
            "Total binary document uploads",
            ["provider"],
            registry=self.registry,
        )
        self.reports_generated_total = Counter(
            "reports_generated_total",
            "Total compliance reports compiled and exported",
            ["format"],
            registry=self.registry,
        )

        # Retrieval Engine Metrics
        self.retrieval_duration_seconds = Histogram(
            "retrieval_duration_seconds",
            "RAG vector retrieval & reranking latency in seconds",
            ["search_type"],
            buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
            registry=self.registry,
        )
        self.retrieval_cache_hits_total = Counter(
            "retrieval_cache_hits_total",
            "Total embedding/result cache hits",
            registry=self.registry,
        )
        self.retrieval_cache_misses_total = Counter(
            "retrieval_cache_misses_total",
            "Total embedding/result cache misses",
            registry=self.registry,
        )
        self.embedding_duration_seconds = Histogram(
            "embedding_duration_seconds",
            "SentenceTransformer embedding latency in seconds",
            registry=self.registry,
        )
        self.reranker_duration_seconds = Histogram(
            "reranker_duration_seconds",
            "Cross-encoder reranking latency in seconds",
            registry=self.registry,
        )
        self.vector_search_duration_seconds = Histogram(
            "vector_search_duration_seconds",
            "Qdrant vector query latency in seconds",
            registry=self.registry,
        )

        # Worker & Outbox Metrics
        self.outbox_queue_depth = Gauge(
            "outbox_queue_depth",
            "Number of pending outbox event deliveries",
            registry=self.registry,
        )
        self.worker_job_execution_seconds = Histogram(
            "worker_job_execution_seconds",
            "Background worker job processing duration in seconds",
            ["job_type"],
            registry=self.registry,
        )
        self.worker_failures_total = Counter(
            "worker_failures_total",
            "Total background worker job execution failures",
            ["job_type"],
            registry=self.registry,
        )

        # Integration Dispatch Metrics
        self.integration_dispatch_total = Counter(
            "integration_dispatch_total",
            "Total outbox integration event dispatches",
            ["provider"],
            registry=self.registry,
        )
        self.integration_dispatch_failures_total = Counter(
            "integration_dispatch_failures_total",
            "Total outbox integration dispatch failures",
            ["provider"],
            registry=self.registry,
        )

        # Database Pool Metrics
        self.database_pool_usage = Gauge(
            "database_pool_usage",
            "Active connections in database connection pool",
            registry=self.registry,
        )

        # AI & LLM Reasoning Metrics
        self.llm_requests_total = Counter(
            "llm_requests_total",
            "Total LLM inference calls",
            ["provider", "model"],
            registry=self.registry,
        )
        self.llm_duration_seconds = Histogram(
            "llm_duration_seconds",
            "LLM inference latency in seconds",
            ["provider", "model"],
            registry=self.registry,
        )
        self.llm_token_usage_total = Counter(
            "llm_token_usage_total",
            "Total tokens consumed by LLM inference calls",
            ["provider", "model", "token_type"],
            registry=self.registry,
        )

    # Business domain recording helper methods
    def record_request(
        self, method: str, endpoint: str, status_code: int, duration_s: float
    ):
        self.http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()
        self.http_request_duration_seconds.labels(
            method=method, endpoint=endpoint
        ).observe(duration_s)

    def record_retrieval(
        self, search_type: str, duration_s: float, cache_hit: bool = False
    ):
        self.retrieval_duration_seconds.labels(search_type=search_type).observe(
            duration_s
        )
        if cache_hit:
            self.retrieval_cache_hits_total.inc()
        else:
            self.retrieval_cache_misses_total.inc()

    def record_embedding(self, duration_s: float):
        self.embedding_duration_seconds.observe(duration_s)

    def record_reranker(self, duration_s: float):
        self.reranker_duration_seconds.observe(duration_s)

    def record_vector_search(self, duration_s: float):
        self.vector_search_duration_seconds.observe(duration_s)

    def record_document_upload(self, provider: str):
        self.documents_uploaded_total.labels(provider=provider).inc()

    def record_report_generated(self, fmt: str):
        self.reports_generated_total.labels(format=fmt).inc()

    def record_worker_job(self, job_type: str, duration_s: float, success: bool = True):
        self.worker_job_execution_seconds.labels(job_type=job_type).observe(duration_s)
        if not success:
            self.worker_failures_total.labels(job_type=job_type).inc()

    def record_integration_dispatch(self, provider: str, success: bool = True):
        self.integration_dispatch_total.labels(provider=provider).inc()
        if not success:
            self.integration_dispatch_failures_total.labels(provider=provider).inc()

    def record_llm_call(
        self,
        provider: str,
        model: str,
        duration_s: float,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ):
        self.llm_requests_total.labels(provider=provider, model=model).inc()
        self.llm_duration_seconds.labels(provider=provider, model=model).observe(
            duration_s
        )
        if prompt_tokens > 0:
            self.llm_token_usage_total.labels(
                provider=provider, model=model, token_type="prompt"
            ).inc(prompt_tokens)
        if completion_tokens > 0:
            self.llm_token_usage_total.labels(
                provider=provider, model=model, token_type="completion"
            ).inc(completion_tokens)

    def export_metrics(self) -> tuple[bytes, str]:
        """Returns generated Prometheus metrics and corresponding content-type header."""
        return generate_latest(self.registry), CONTENT_TYPE_LATEST


# Global singleton instance initialized with default registry
metrics_service = MetricsService()
