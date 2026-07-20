from dataclasses import dataclass

@dataclass(frozen=True)
class ReportApprovalReceipt:
    """Receipt record confirming report verification and sign-off."""
    report_id: int
    approved_by: str
    timestamp: str
    version: int
