from dataclasses import dataclass

@dataclass(frozen=True)
class ReportGenerationReceipt:
    """Receipt record confirming compliance report generation details."""
    report_id: int
    request_id: int
    version: int
    snapshot_version: int
    created_by: str
    timestamp: str
