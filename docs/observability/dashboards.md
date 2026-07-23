# Grafana Dashboard Documentation — ComplianceOS

## Available Grafana Dashboards

1. **API Performance Dashboard (`grafana_api_performance.json`)**
   - HTTP Throughput (req/sec)
   - P50, P95, and P99 Latency distribution
   - HTTP Status Code breakdown (2xx, 4xx, 5xx)

2. **RAG Retrieval Pipeline Dashboard (`grafana_retrieval_pipeline.json`)**
   - Hybrid Vector Search Latency
   - Embedding & Cross-Encoder Reranker Duration
   - Embedding Cache Hit / Miss Ratio
   - Qdrant Vector Query Latency

3. **Background Worker & Outbox Health Dashboard (`grafana_worker_health.json`)**
   - Outbox Queue Depth
   - Worker Job Execution Duration by Type
   - Worker Failure Rates & Integration Dispatch Counts
