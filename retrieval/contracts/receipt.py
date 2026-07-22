from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ParserReceiptContract:
    """Explicit parser operations receipt schema mapping for enterprise audit checks."""

    engine: str
    engine_version: str
    ocr_used: bool
    tables_found: int
    layout: str
    duration_ms: int
    warnings: List[str] = field(default_factory=list)
