"""Real-time policy violation monitoring engine."""

import logging
from typing import List, Dict
from governance.schemas import ComplianceViolation, ViolationSeverity

logger = logging.getLogger("governance.monitoring.monitor")


class ViolationMonitor:
    """Tracks and records compliance policy violations across platform operations."""

    def __init__(self):
        self._violations: Dict[str, List[ComplianceViolation]] = (
            {}
        )  # organization_id -> List[ComplianceViolation]

    async def record_violation(
        self, violation: ComplianceViolation
    ) -> ComplianceViolation:
        org_id = violation.organization_id
        if org_id not in self._violations:
            self._violations[org_id] = []
        self._violations[org_id].append(violation)
        logger.warning(
            f"Recorded ComplianceViolation '{violation.violation_id}' severity={violation.severity.value} rule='{violation.rule_id}'"
        )
        return violation

    async def get_violations(
        self,
        organization_id: str = "default",
        min_severity: Optional[ViolationSeverity] = None,
    ) -> List[ComplianceViolation]:
        return self._violations.get(organization_id, [])
