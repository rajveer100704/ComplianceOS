import logging
from typing import Dict, Any
from database.events import EventPublisher

logger = logging.getLogger("review_events")


class ReviewEventPublisher:
    """Publishes domain events related to the review and collaboration workflows."""

    @staticmethod
    async def publish_review_assigned(
        request_id: int, reviewer: str, assigned_by: str
    ) -> None:
        """Publishes ReviewAssigned domain event."""
        logger.info(f"Publishing ReviewAssigned event for request {request_id}")
        await EventPublisher.publish_event(
            "ReviewAssigned",
            {
                "request_id": request_id,
                "reviewer": reviewer,
                "assigned_by": assigned_by,
            },
        )

    @staticmethod
    async def publish_review_approved(request_id: int, approved_by: str) -> None:
        """Publishes ReviewApproved domain event."""
        logger.info(f"Publishing ReviewApproved event for request {request_id}")
        await EventPublisher.publish_event(
            "ReviewApproved", {"request_id": request_id, "approved_by": approved_by}
        )

    @staticmethod
    async def publish_evidence_pinned(
        claim_id: int, chunk_id: str, pinned_by: str, role: str
    ) -> None:
        """Publishes EvidencePinned domain event."""
        logger.info(f"Publishing EvidencePinned event for claim {claim_id}")
        await EventPublisher.publish_event(
            "EvidencePinned",
            {
                "claim_id": claim_id,
                "chunk_id": chunk_id,
                "pinned_by": pinned_by,
                "role": role,
            },
        )

    @staticmethod
    async def publish_snapshot_created(
        request_id: int, snapshot_id: int, version: int, creator: str
    ) -> None:
        """Publishes SnapshotCreated domain event."""
        logger.info(
            f"Publishing SnapshotCreated event for request {request_id} version {version}"
        )
        await EventPublisher.publish_event(
            "SnapshotCreated",
            {
                "request_id": request_id,
                "snapshot_id": snapshot_id,
                "version": version,
                "creator": creator,
            },
        )

    @staticmethod
    async def publish_comment_added(comment_id: int, claim_id: int, user: str) -> None:
        """Publishes CommentAdded domain event."""
        logger.info(
            f"Publishing CommentAdded event for comment {comment_id} on claim {claim_id}"
        )
        await EventPublisher.publish_event(
            "CommentAdded",
            {"comment_id": comment_id, "claim_id": claim_id, "user": user},
        )
