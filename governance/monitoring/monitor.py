"""Real-time policy violation monitoring engine."""

import logging
from typing import List, Dict, Optional
from governance.schemas import ComplianceViolation, ViolationSeverity

logger = logging.getLogger("governance.monitoring.monitor")

SEVERITY_ORDER: Dict[ViolationSeverity, int] = {
    ViolationSeverity.LOW: 1,
    ViolationSeverity.MEDIUM: 2,
    ViolationSeverity.HIGH: 3,
    ViolationSeverity.CRITICAL: 4,
}


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
        violations = self._violations.get(organization_id, [])
        if min_severity is None:
            return violations

        target_rank = SEVERITY_ORDER.get(min_severity, 1)
        return [
            v for v in violations if SEVERITY_ORDER.get(v.severity, 1) >= target_rank
        ]
