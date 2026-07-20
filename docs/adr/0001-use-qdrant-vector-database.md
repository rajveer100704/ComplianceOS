# ADR 0001: Selection of Qdrant as Primary Vector Database Engine

**Date:** 2026-07-20  
**Status:** Accepted  
**Deciders:** Core Engineering Team  

---

## Context & Problem Statement
ComplianceOS requires dense and sparse vector indexing for regulatory corpus chunks. Vector retrieval must support high similarity recall, metadata payload filtering (by document ID, regulatory chapter, and section), fast vector upserts, and low-latency hybrid search.

## Considered Options
1. **Qdrant Vector Engine**
2. **pgvector extension on PostgreSQL**
3. **Pinecone (SaaS)**
4. **Chroma DB**

## Decision Outcome
**Chosen Option:** **Qdrant Vector Engine**

### Positive Consequences
- **Hybrid Dense + Lexical Search**: Native payload filtering and payload indexing without PostgreSQL query overhead.
- **Self-Hosted & Cloud Compatibility**: Runs locally via Docker (`qdrant/qdrant:v1.7.4`) and scales seamlessly to Qdrant Cloud.
- **REST & gRPC Client Support**: Official Python client (`qdrant-client`) integrates directly into `retrieval/vector_store.py`.

## Alternatives Rejected

- **pgvector**: Rejected due to high index build times and query performance degradation on hybrid text-vector filters under large dataset sizes.
- **Pinecone**: Rejected to avoid mandatory third-party cloud lock-in for local development and offline testing.
- **Chroma DB**: Rejected due to limited production clustering and deployment options compared to Qdrant.
