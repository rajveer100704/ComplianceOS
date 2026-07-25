# AI Governance — Key Design Decisions Log

## Summary of Decisions

1. **SHA-256 Block Chaining**: Audit ledger entries link `prev_hash` to compute `current_hash` ensuring tamper-evident log integrity.
2. **PlatformEvent Pub/Sub Observation**: Governance subscribes to `EventBus` without coupling to specific subsystem internal APIs.
3. **Blocking vs Advisory Gates**: Compliance rules flag `is_blocking=True` for mandatory sign-off gates.
