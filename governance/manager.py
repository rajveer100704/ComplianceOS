"""Centralized GovernanceManager facade observing PlatformEvents via EventBus."""

import logging
from typing import Dict, List, Optional, Tuple
from events.bus import EventBus
from events.schemas import PlatformEvent
from governance.schemas import (
    AuditLedgerEntry,
    ComplianceRule,
    GateEvaluationResult,
    ComplianceViolation,
)
from governance.audit.ledger import AuditLedger
from governance.compliance_gates.evaluator import ComplianceGateEvaluator
from governance.monitoring.monitor import ViolationMonitor

logger = logging.getLogger("governance.manager")


class GovernanceManager:
    """Centralized facade for AI Governance, Audit Ledger, Compliance Gates, and EventBus observation."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.ledger = AuditLedger()
        self.evaluator = ComplianceGateEvaluator()
        self.monitor = ViolationMonitor()
        self.event_bus = event_bus

        if self.event_bus:
            # Subscribe to all PlatformEvent categories (category=None wildcard)
            self.event_bus.subscribe(self.handle_platform_event, category=None)
            logger.info(
                "GovernanceManager subscribed to EventBus wildcard PlatformEvents"
            )

    async def handle_platform_event(self, event: PlatformEvent) -> None:
        """Callback invoked whenever any subsystem emits a PlatformEvent."""
        entry = AuditLedgerEntry(
            organization_id=event.organization_id,
            event_id=event.event_id,
            event_type=event.event_type,
            actor_id=event.actor_id,
            target_id=event.target_id,
            timestamp=event.timestamp,
        )
        await self.ledger.append_entry(entry)

    async def record_event(self, event: PlatformEvent) -> AuditLedgerEntry:
        entry = AuditLedgerEntry(
            organization_id=event.organization_id,
            event_id=event.event_id,
            event_type=event.event_type,
            actor_id=event.actor_id,
            target_id=event.target_id,
            timestamp=event.timestamp,
        )
        return await self.ledger.append_entry(entry)

    async def verify_ledger(self, organization_id: str = "default") -> Tuple[bool, int]:
        return await self.ledger.verify_chain(organization_id)

    async def add_rule(self, rule: ComplianceRule) -> ComplianceRule:
        return await self.evaluator.add_rule(rule)

    async def evaluate_gate(
        self,
        session_id: str,
        context_metrics: Dict[str, float],
        organization_id: str = "default",
    ) -> GateEvaluationResult:
        return await self.evaluator.evaluate_gate(
            session_id, context_metrics, organization_id
        )

    async def get_audit_trail(
        self, organization_id: str = "default"
    ) -> List[AuditLedgerEntry]:
        return await self.ledger.get_entries(organization_id)

    async def get_violations(
        self, organization_id: str = "default"
    ) -> List[ComplianceViolation]:
        return await self.monitor.get_violations(organization_id)
