# Shared Memory Engine — Implementation Guide

## Ordered Development Phases

1. **Phase A (Foundation)**: `memory/interfaces.py`, `memory/schemas.py`, `memory/base.py`, `memory/manager.py`
2. **Phase B (Storage Engines)**: `memory/semantic/`, `memory/episodic/`, `memory/organizational/`, `memory/reviewer/`, `memory/workflow/`
3. **Phase C (Intelligence Pipeline)**: `ranking.py`, `importance.py`, `compression.py`, `expiration.py`
4. **Phase D (Context Builder)**: `builder.py`, `retrieval.py`
5. **Phase E (Agent Integration)**: Inject `MemoryContext` into `AgentRuntimeState` and `Agent` base class.
