# AI Governance — Test Plan

## Test Strategy

1. **Unit Tests (`tests/governance/test_governance.py`)**: Validate cryptographic chain verification, compliance gate evaluation, and violation detection.
2. **EventBus Integration Tests**: Verify that publishing a `PlatformEvent` automatically triggers audit logging in `GovernanceManager`.
3. **Chain Tampering Tests**: Inject modified historical ledger entries and verify `verify_ledger()` correctly flags invalid hash chains.
