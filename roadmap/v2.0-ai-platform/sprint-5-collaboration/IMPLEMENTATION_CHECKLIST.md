# Real-Time Collaboration — Implementation Checklist

- [x] Design Specification Package (PRD, ADR, ARCHITECTURE, DATABASE, API, DOMAIN_MODEL)
- [ ] Phase A Core Schemas (`collaboration/schemas.py`)
- [ ] Phase B Threaded Comments Engine (`collaboration/comments/store.py`)
- [ ] Phase C Concurrency Lock Manager & Presence Tracker (`collaboration/presence/lock_manager.py`, `tracker.py`)
- [ ] Phase D Activity Event Stream (`collaboration/webhooks/dispatcher.py`)
- [ ] Phase E Facade & Integration (`collaboration/manager.py`)
- [ ] Unit & Integration Tests (`tests/collaboration/`)
- [ ] Full Platform Regression Check (211+ tests passing)
