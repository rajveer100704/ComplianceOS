# ComplianceOS — Production Deployment Guide

This guide outlines the production deployment architecture, managed cloud infrastructure stack, environmental configuration, CI/CD pipeline, and smoke-testing workflow for deploying ComplianceOS to production environments.

---

## 1. System Architecture & Topology

```
                                     Internet
                                        │
                                Cloudflare (SSL / CDN)
                                        │
                            ┌───────────┴───────────┐
                            │   Nginx / Caddy Proxy │
                            └───────────┬───────────┘
                                        │
                              FastAPI Web Server
                        (Containerized Uvicorn Service)
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           │                            │                            │
    PostgreSQL 15/17              Qdrant Vector DB            Worker Queue
   (Neon / Supabase)              (Qdrant Cloud)            (Upstash Redis)
           │                            │                            │
           └────────────────────────────┼────────────────────────────┘
                                        │
                             Cloudflare R2 / AWS S3
                            (Document Export Storage)
                                        │
                                  OpenTelemetry
                                        │
                           Prometheus + Grafana Cloud
                             (Metrics & Log Tracing)
```

---

## 2. Recommended Production Cloud Stack

| Component | Provider Recommendation | Purpose |
| :--- | :--- | :--- |
| **Frontend UI** | **Vercel** / **Netlify** | Edge hosting for static Review Workstation UI (`index.html`). |
| **Backend API** | **Railway** / **Render** | Containerized FastAPI application deployment. |
| **Relational Database** | **Neon** / **Supabase** | Serverless PostgreSQL database with automated Alembic migrations. |
| **Vector Engine** | **Qdrant Cloud** | Cloud-managed dense & sparse vector index storage. |
| **Background Queue** | **Upstash Redis** | Serverless Redis instance backing async task execution. |
| **Object Storage** | **Cloudflare R2** / **AWS S3** | Durable storage for PDF document uploads and compiled export files. |
| **Telemetry & Monitoring** | **Grafana Cloud** | Prometheus metrics scraping, OpenTelemetry tracing, and log aggregation. |

---

## 3. System Prerequisites

Before deploying ComplianceOS, ensure the following software dependencies and cloud accounts are configured:

- **Python**: 3.11+ (Python 3.11 slim runtime container)
- **Docker**: Docker Engine 25+ & Docker Compose v2+
- **Database**: PostgreSQL 15+ (Local or Neon/Supabase instance)
- **Vector Database**: Qdrant v1.7+ (Local or Qdrant Cloud cluster)
- **Background Queue**: Redis 7+ (Local or Upstash Redis instance)
- **Object Storage**: S3-compatible bucket (Cloudflare R2 or AWS S3)
- **Version Control**: Git & GitHub CLI

---

## 4. Production Environment Configuration

Copy `.env.example` and set production environment variables:

```ini
# Application Core
APP_NAME=ComplianceOS
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Security & Authentication
AUTH_SECRET=your-secure-random-32-byte-secret-key
API_KEY=your-production-api-key
AUTH_PROVIDER=jwt
JWT_SECRET=your-jwt-secret-key-32-bytes
JWT_ALGORITHM=HS256
CORS_ORIGINS=["https://complianceos.yourdomain.com"]
RATE_LIMIT_PER_MINUTE=120

# Databases & Vector Store
DATABASE_URL=postgresql+asyncpg://user:pass@ep-cool-db.neon.tech/compliancedb
QDRANT_URL=https://your-cluster-url.qdrant.tech:6333
QDRANT_API_KEY=your-qdrant-cloud-api-key
QDRANT_COLLECTION=compliance_regulations

# Workers & Redis
REDIS_URL=rediss://default:pass@upstash-redis.upstash.io:6379
WORKER_POLL_INTERVAL_SEC=1.0

# AI & Embedding Providers
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_PROVIDER=gemini
LLM_API_KEY=your-gemini-api-key

# Storage & Telemetry
STORAGE_PROVIDER=r2
R2_BUCKET=complianceos-exports
R2_ACCESS_KEY=your-r2-access-key
R2_SECRET_KEY=your-r2-secret-key
PROMETHEUS_ENABLED=true
```

---

## 5. Continuous Integration & Continuous Deployment (CI/CD)

The GitHub Actions pipeline (`.github/workflows/ci.yml`) enforces code quality, type checks, unit testing, container security scanning, and deployment:

```yaml
name: ComplianceOS Production Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  quality-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt ruff black mypy pytest pytest-cov
      - name: Lint Code (Ruff)
        run: ruff check .
      - name: Code Formatting (Black)
        run: black --check .
      - name: Type Check (Mypy)
        run: mypy --ignore-missing-imports .
      - name: Execute Automated Test Suite
        run: python -m pytest test_main.py --cov=.

  security-and-deploy:
    needs: quality-and-test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker Image
        run: docker build -t complianceos-web:latest .
      - name: Trivy Container Vulnerability Scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'complianceos-web:latest'
          format: 'table'
          exit-code: '0'
          severity: 'CRITICAL,HIGH'
```

---

## 6. Post-Deployment Smoke Testing Checklist

After deploying to production, execute the following smoke tests:

1. **Liveness Probe**: `curl -f https://api.complianceos.yourdomain.com/healthz`
2. **Readiness Probe**: `curl -f https://api.complianceos.yourdomain.com/readyz`
3. **Metrics Check**: `curl -f https://api.complianceos.yourdomain.com/metrics`
4. **API OpenDocs**: Verify `https://api.complianceos.yourdomain.com/docs` loads OpenAPI interactive interface.
5. **Create Compliance Request**: `POST /api/requests`
6. **Upload & Ingest Document**: `POST /api/requests/{id}/documents`
7. **Execute Verification Pipeline**: `POST /api/requests/{id}/run`
8. **Capture Snapshot**: `POST /api/requests/{id}/snapshots`
9. **Generate & Transition Report**: `POST /api/requests/{id}/reports` & `POST /api/reports/{id}/transition`
10. **Export Document**: `POST /api/reports/{id}/export`
