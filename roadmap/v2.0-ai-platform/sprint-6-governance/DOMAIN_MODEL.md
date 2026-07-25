# AI Governance — Domain Model Reference

## Domain Taxonomy & Entity Relationships

```
GovernanceManager
    │
    ├── Cryptographic Audit Ledger (AuditLedgerEntry, SHA-256 Block Chaining)
    ├── Compliance Rules (ComplianceRule, Threshold, Operator)
    ├── Sign-Off Gates (GateEvaluationResult, GateStatus)
    ├── Violation Monitor (ComplianceViolation, Severity)
    └── PlatformEvent Observer (Subscriber to EventBus)
```

### Key Models

1. **`AuditLedgerEntry`**: Cryptographically chained audit record (`prev_hash` $\to$ `current_hash`).
2. **`ComplianceRule`**: Configurable metric threshold rule (e.g. `grounding_score >= 0.85`).
3. **`GateEvaluationResult`**: Result of evaluating all active rules for a request/session (`PASSED`, `REJECTED`).
4. **`ComplianceViolation`**: Recorded policy violation with severity level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
