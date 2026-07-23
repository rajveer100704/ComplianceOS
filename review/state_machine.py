"""Generic StateMachine[T] managing formal state transitions across entities (Claim, Report, Evidence)."""

import enum
from typing import Generic, TypeVar, Dict, Set


class StandardState(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"


T = TypeVar("T")


class InvalidStateTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""

    pass


class StateMachine(Generic[T]):
    """Generic state machine validating allowable entity state transitions."""

    ALLOWED_TRANSITIONS: Dict[StandardState, Set[StandardState]] = {
        StandardState.DRAFT: {StandardState.PENDING_REVIEW, StandardState.REJECTED},
        StandardState.PENDING_REVIEW: {
            StandardState.PENDING_APPROVAL,
            StandardState.REJECTED,
            StandardState.DRAFT,
        },
        StandardState.PENDING_APPROVAL: {
            StandardState.APPROVED,
            StandardState.REJECTED,
            StandardState.PENDING_REVIEW,
        },
        StandardState.APPROVED: {StandardState.PUBLISHED, StandardState.PENDING_REVIEW},
        StandardState.PUBLISHED: set(),
        StandardState.REJECTED: {StandardState.DRAFT, StandardState.PENDING_REVIEW},
    }

    def transition(
        self, current_state: StandardState, target_state: StandardState
    ) -> StandardState:
        """Validates and executes state transition."""
        allowed = self.ALLOWED_TRANSITIONS.get(current_state, set())
        if target_state not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition entity state from '{current_state.value}' to '{target_state.value}'"
            )
        return target_state
