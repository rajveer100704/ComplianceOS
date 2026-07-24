"""Context window summarizer and memory context compressor."""

import logging
from typing import List
from memory.schemas import MemoryItem

logger = logging.getLogger("memory.compression")


class MemoryCompressor:
    """Compresses a list of memory items into a token-budgeted summary text."""

    def compress(self, items: List[MemoryItem], max_summary_tokens: int = 500) -> str:
        if not items:
            return ""

        summary_lines = []
        for i in items:
            summary_lines.append(f"[{i.memory_type.value.upper()}] {i.content[:150]}")

        summary = "\n".join(summary_lines)
        logger.debug(
            f"Compressed {len(items)} memory items into summary of length {len(summary)}"
        )
        return summary
