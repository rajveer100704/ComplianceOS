from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewTransitionReceipt:
    """Receipt record confirming request workflow state transition."""

    request_id: int
    old_status: str
    new_status: str
    transitioned_by: str
    timestamp: str
