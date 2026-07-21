from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SnapshotReceipt:
    """Receipt record confirming snapshot capture operations."""

    request_id: int
    snapshot_id: int
    version: int
    creator: str
    timestamp: str
    config_hash: Optional[str] = None
