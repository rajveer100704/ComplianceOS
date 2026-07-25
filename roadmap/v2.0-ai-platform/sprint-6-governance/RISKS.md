# AI Governance — Risk Management Document

## Identified Risks & Mitigation Strategies

1. **Audit Ledger Hash Invalidation**: Schema mutation causing hash mismatch across ledger blocks.
   - *Mitigation*: Canonical SHA-256 serialization function enforcing deterministic key sorting.
2. **Blocking Pipeline Latency**: Synchronous governance rules slowing down live agent reasoning loops.
   - *Mitigation*: Non-blocking `EventBus` pub/sub observation for audit logging; fast-path numeric checks for gates.
