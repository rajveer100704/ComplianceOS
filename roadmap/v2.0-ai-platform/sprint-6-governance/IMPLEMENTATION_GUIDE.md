# AI Governance — Implementation Guide

## Ordered Development Phases

1. **Phase A (Core Domain Models & Schemas)**:
   - `governance/schemas.py` — `AuditLedgerEntry`, `ComplianceRule`, `GateEvaluationResult`, `ComplianceViolation`.
2. **Phase B (Cryptographic Audit Ledger)**:
   - `governance/audit/ledger.py` — SHA-256 block-chained audit ledger with `verify_chain()`.
3. **Phase C (Compliance Sign-off Gates)**:
   - `governance/compliance_gates/evaluator.py` — Policy evaluator enforcing threshold guardrails.
4. **Phase D (Real-Time Violation Monitor)**:
   - `governance/monitoring/monitor.py` — Real-time violation monitor.
5. **Phase E (Centralized Facade & EventBus Subscriber)**:
   - `governance/manager.py` — `GovernanceManager` subscribing to `EventBus` (`PlatformEvent`).
