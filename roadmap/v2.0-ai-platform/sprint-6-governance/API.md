# AI Governance — API Specification

## `GovernanceManager` Interface Methods

```python
async def record_event(event: PlatformEvent) -> AuditLedgerEntry:
    ...

async def verify_ledger(organization_id: str = "default") -> Tuple[bool, int]:
    ...

async def add_rule(rule: ComplianceRule) -> ComplianceRule:
    ...

async def evaluate_gate(
    session_id: str, context_metrics: Dict[str, float], organization_id: str = "default"
) -> GateEvaluationResult:
    ...

async def get_audit_trail(organization_id: str = "default") -> List[AuditLedgerEntry]:
    ...

async def get_violations(organization_id: str = "default") -> List[ComplianceViolation]:
    ...
```
