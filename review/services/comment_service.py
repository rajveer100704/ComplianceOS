import re
import logging
from typing import List, Dict, Any, Optional
from database.services.unit_of_work import UnitOfWork
from database.models.review import (
    ClaimCommentModel,
    CommentMentionModel,
    ReviewActivityLogModel,
)
from review.events import ReviewEventPublisher

logger = logging.getLogger("comment_service")


class CommentService:
    """Orchestrates threaded comments, discussions, and reviewer mention tags."""

    @staticmethod
    async def add_comment(
        claim_id: int, user: str, text: str, parent_id: Optional[int] = None
    ) -> ClaimCommentModel:
        """Appends a new threaded comment, parses mentions, and logs request activity."""
        async with UnitOfWork() as uow:
            claim = await uow.claims.get(claim_id)
            if not claim:
                raise ValueError(f"Claim with ID {claim_id} not found.")

            # Create comment
            comment = ClaimCommentModel(
                claim_id=claim_id, parent_id=parent_id, user=user, text=text
            )
            uow.session.add(comment)
            await uow.session.flush()  # Populate comment.id

            # Parse mentions matching @Username
            mentions = re.findall(r"@(\w+)", text)
            for m in mentions:
                mention = CommentMentionModel(comment_id=comment.id, user=m)
                uow.session.add(mention)

            # Log custom request timeline activity
            activity = ReviewActivityLogModel(
                request_id=claim.request_id,
                event_type="comment",
                user=user,
                details=f"User '{user}' added comment to claim {claim_id}: '{text[:50]}...'",
            )
            uow.session.add(activity)
            await uow.commit()

            # Publish event
            await ReviewEventPublisher.publish_comment_added(comment.id, claim_id, user)

            return comment

    @staticmethod
    async def get_comments_tree(claim_id: int) -> List[Dict[str, Any]]:
        """Fetches threaded comments tree for a specific claim ordered by hierarchy."""
        async with UnitOfWork() as uow:
            comments = await uow.comments.get_by_claim(claim_id)

            # Map comments to dictionary structure
            nodes = {}
            roots = []
            for c in comments:
                node = {
                    "id": c.id,
                    "claim_id": c.claim_id,
                    "parent_id": c.parent_id,
                    "user": c.user,
                    "text": c.text,
                    "created_at": c.created_at.isoformat(),
                    "replies": [],
                }
                nodes[c.id] = node
                if c.parent_id is None:
                    roots.append(node)
                else:
                    parent = nodes.get(c.parent_id)
                    if parent:
                        parent["replies"].append(node)
                    else:
                        # Fallback if parent not parsed yet (roots fallback)
                        roots.append(node)
            return roots
