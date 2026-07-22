import logging
from typing import List
from database.services.unit_of_work import UnitOfWork
from database.models.review import PinnedEvidenceModel, ReviewActivityLogModel
from review.events import ReviewEventPublisher

logger = logging.getLogger("evidence_service")


class EvidenceService:
    """Orchestrates evidence pinning, unpinning, and categorization roles."""

    @staticmethod
    async def pin_evidence(
        claim_id: int, chunk_id: str, document_id: int, user: str, role: str = "PRIMARY"
    ) -> PinnedEvidenceModel:
        """Pins a specific chunk as evidence with a role (PRIMARY, SUPPORTING, CONTRADICTING)."""
        if role not in ["PRIMARY", "SUPPORTING", "CONTRADICTING"]:
            raise ValueError(
                f"Invalid evidence role '{role}'. Must be PRIMARY, SUPPORTING, or CONTRADICTING."
            )

        async with UnitOfWork() as uow:
            claim = await uow.claims.get(claim_id)
            if not claim:
                raise ValueError(f"Claim with ID {claim_id} not found.")

            document = await uow.documents.get(document_id)
            if not document:
                raise ValueError(f"Document with ID {document_id} not found.")

            # Check if already pinned
            existing = await uow.evidences.get_by_claim_and_chunk(claim_id, chunk_id)
            if existing:
                # Update role
                evidence = existing[0]
                evidence.role = role
            else:
                # Create new pinning
                evidence = PinnedEvidenceModel(
                    claim_id=claim_id,
                    chunk_id=chunk_id,
                    document_id=document_id,
                    role=role,
                    pinned_by=user,
                )
                uow.session.add(evidence)

            # Log custom timeline log
            activity = ReviewActivityLogModel(
                request_id=claim.request_id,
                event_type="evidence",
                user=user,
                details=f"Pinned chunk '{chunk_id}' as {role} evidence for claim {claim_id}.",
            )
            uow.session.add(activity)
            await uow.commit()

            # Publish event
            await ReviewEventPublisher.publish_evidence_pinned(
                claim_id, chunk_id, user, role
            )

            return evidence

    @staticmethod
    async def unpin_evidence(claim_id: int, chunk_id: str, user: str) -> bool:
        """Removes a pinned evidence reference from a claim."""
        async with UnitOfWork() as uow:
            claim = await uow.claims.get(claim_id)
            if not claim:
                raise ValueError(f"Claim with ID {claim_id} not found.")

            existing = await uow.evidences.get_by_claim_and_chunk(claim_id, chunk_id)
            if not existing:
                return False

            for ev in existing:
                await uow.evidences.delete(ev)

            # Log timeline log
            activity = ReviewActivityLogModel(
                request_id=claim.request_id,
                event_type="evidence",
                user=user,
                details=f"Unpinned chunk '{chunk_id}' from claim {claim_id}.",
            )
            uow.session.add(activity)
            await uow.commit()
            return True

    @staticmethod
    async def get_claim_evidences(claim_id: int) -> List[PinnedEvidenceModel]:
        """Lists all active pinned evidence records for a specific claim."""
        async with UnitOfWork() as uow:
            return await uow.evidences.get_by_claim(claim_id)
