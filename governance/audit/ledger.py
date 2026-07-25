"""Cryptographically chained SHA-256 audit ledger ensuring tamper-evident log integrity."""

import logging
from typing import List, Dict, Tuple
from governance.schemas import AuditLedgerEntry

logger = logging.getLogger("governance.audit.ledger")


class AuditLedger:
    """Immutable audit trail maintaining a SHA-256 parent block hash chain."""

    def __init__(self):
        self._chain: Dict[str, List[AuditLedgerEntry]] = (
            {}
        )  # organization_id -> List[AuditLedgerEntry]

    async def append_entry(self, entry: AuditLedgerEntry) -> AuditLedgerEntry:
        org_id = entry.organization_id
        if org_id not in self._chain:
            self._chain[org_id] = []

        history = self._chain[org_id]
        if history:
            prev_entry = history[-1]
            entry.sequence_number = prev_entry.sequence_number + 1
            entry.prev_hash = prev_entry.current_hash
        else:
            entry.sequence_number = 1
            entry.prev_hash = "0" * 64

        entry.current_hash = entry.compute_hash()
        history.append(entry)

        logger.info(
            f"Appended AuditLedgerEntry seq={entry.sequence_number} ({entry.event_type}) current_hash={entry.current_hash[:8]}..."
        )
        return entry

    async def verify_chain(self, organization_id: str = "default") -> Tuple[bool, int]:
        """Validates 100% of historical ledger entries against SHA-256 parent block hashes."""
        history = self._chain.get(organization_id, [])
        if not history:
            return True, 0

        expected_prev_hash = "0" * 64
        for idx, entry in enumerate(history):
            if entry.prev_hash != expected_prev_hash:
                logger.error(
                    f"Audit ledger hash mismatch at sequence {entry.sequence_number}: prev_hash={entry.prev_hash} != expected={expected_prev_hash}"
                )
                return False, idx

            recalculated_hash = entry.compute_hash()
            if entry.current_hash != recalculated_hash:
                logger.error(
                    f"Audit ledger content tampered at sequence {entry.sequence_number}: stored_hash={entry.current_hash} != recalculated={recalculated_hash}"
                )
                return False, idx

            expected_prev_hash = entry.current_hash

        logger.info(
            f"Verified audit ledger integrity across {len(history)} entries for org '{organization_id}'"
        )
        return True, len(history)

    async def get_entries(
        self, organization_id: str = "default"
    ) -> List[AuditLedgerEntry]:
        return self._chain.get(organization_id, [])
