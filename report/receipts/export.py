from dataclasses import dataclass


@dataclass(frozen=True)
class ReportExportReceipt:
    """Receipt record confirming format compilation and document export details."""

    report_id: int
    format: str
    exported_by: str
    timestamp: str
    file_path: str
