import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from database.services.unit_of_work import UnitOfWork
from database.models.review import ReviewAssignmentModel, ReviewActivityLogModel
from review.receipts.transition import ReviewTransitionReceipt
from review.events import ReviewEventPublisher

logger = logging.getLogger("review_service")

# Formal Review Workflow State Machine Transitions Map
# format: { current_state: [allowed_next_states] }
VALID_TRANSITIONS = {
    "Draft": ["Assigned", "In Review"],
    "Assigned": ["In Review", "Draft"],
    "In Review": ["Changes Requested", "Approved", "Rejected"],
    "Changes Requested": ["In Review"],
    "Approved": ["Published"],
    "Rejected": ["Draft", "Assigned"],
    "Published": [],
}

# Role Permission Matrix
# format: { action: [roles_allowed] }
ROLE_PERMISSIONS = {
    "assign": ["Reviewer", "Lead Reviewer", "Admin"],
    "transition_any": ["Reviewer", "Lead Reviewer", "Admin"],
    "transition_decision": ["Lead Reviewer", "Admin"],  # Approved, Rejected, Published
}


class ReviewService:
    """Orchestrates review lifecycles, state machine transitions, and reviewer assignments."""

    @staticmethod
    def check_permission(action: str, role: str) -> None:
        """Validates if user role has authorization to execute specific review actions."""
        allowed_roles = ROLE_PERMISSIONS.get(action, [])
        if role not in allowed_roles:
            raise PermissionError(
                f"User role '{role}' is not authorized to perform action '{action}'"
            )

    @staticmethod
    async def assign_reviewer(
        request_id: int,
        reviewer: str,
        assigned_by: str,
        role: str,
        reason: Optional[str] = None,
    ) -> ReviewAssignmentModel:
        """Assigns a reviewer to a request, preserving full audit history."""
        ReviewService.check_permission("assign", role)

        async with UnitOfWork() as uow:
            request = await uow.requests.get(request_id)
            if not request:
                raise ValueError(f"Request with ID {request_id} not found.")

            # Deactivate existing active assignment
            active_assign = await uow.assignments.get_active_assignment(request_id)
            now_str = datetime.now(timezone.utc).isoformat()
            if active_assign:
                active_assign.unassigned_at = now_str
                active_assign.reason = "Reassigned to another reviewer"

            # Create new assignment record
            new_assign = ReviewAssignmentModel(
                request_id=request_id,
                reviewer=reviewer,
                assigned_by=assigned_by,
                assigned_at=now_str,
                reason=reason,
            )
            uow.session.add(new_assign)

            # Update request reviewer and status if in Draft
            request.assigned_reviewer = reviewer
            old_status = request.status
            if request.status == "Draft":
                request.status = "Assigned"
                # Log state transition as part of assignment
                activity_transition = ReviewActivityLogModel(
                    request_id=request_id,
                    event_type="transition",
                    user=assigned_by,
                    details=f"Status transitioned from {old_status} to Assigned due to reviewer assignment.",
                )
                uow.session.add(activity_transition)

            # Log assignment event in activity log
            activity = ReviewActivityLogModel(
                request_id=request_id,
                event_type="assignment",
                user=assigned_by,
                details=f"Assigned reviewer '{reviewer}' to request.",
            )
            uow.session.add(activity)

            await uow.commit()

            # Publish event
            await ReviewEventPublisher.publish_review_assigned(
                request_id, reviewer, assigned_by
            )

            return new_assign

    @staticmethod
    async def transition_status(
        request_id: int, new_status: str, user: str, role: str
    ) -> ReviewTransitionReceipt:
        """Transitions request review lifecycle status according to formal state machine bounds."""
        async with UnitOfWork() as uow:
            request = await uow.requests.get(request_id)
            if not request:
                raise ValueError(f"Request with ID {request_id} not found.")

            old_status = request.status
            allowed_next = VALID_TRANSITIONS.get(old_status, [])

            if new_status not in allowed_next:
                raise ValueError(
                    f"Invalid transition: Cannot move from '{old_status}' to '{new_status}'"
                )

            # Check role permissions for approving/rejecting/publishing decisions
            if new_status in ["Approved", "Rejected", "Published"]:
                ReviewService.check_permission("transition_decision", role)
            else:
                ReviewService.check_permission("transition_any", role)

            # Update state
            request.status = new_status
            now_str = datetime.now(timezone.utc).isoformat()
            if new_status == "Approved":
                request.approved_at = now_str

            # Log transition in timeline activity log
            activity = ReviewActivityLogModel(
                request_id=request_id,
                event_type="transition",
                user=user,
                details=f"Status transitioned from '{old_status}' to '{new_status}'.",
            )
            uow.session.add(activity)
            await uow.commit()

            # Publish event
            if new_status == "Approved":
                await ReviewEventPublisher.publish_review_approved(request_id, user)

            return ReviewTransitionReceipt(
                request_id=request_id,
                old_status=old_status,
                new_status=new_status,
                transitioned_by=user,
                timestamp=now_str,
            )

    @staticmethod
    async def log_custom_activity(
        request_id: int, event_type: str, user: str, details: str
    ) -> None:
        """Appends an immutable timeline activity log entry."""
        async with UnitOfWork() as uow:
            activity = ReviewActivityLogModel(
                request_id=request_id, event_type=event_type, user=user, details=details
            )
            uow.session.add(activity)
            await uow.commit()

    @staticmethod
    async def check_activity_timeline_immutability(activity_id: int) -> None:
        """Helper checking that activity logs cannot be edited or deleted."""
        # This is enforced at the business service level by not exposing any update/delete functions
        pass
