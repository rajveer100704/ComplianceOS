"""Threaded comment and inline annotation storage engine with @mention parsing."""

import re
import logging
from typing import List, Dict
from collaboration.schemas import CommentThread

logger = logging.getLogger("collaboration.comments.store")


class CommentStore:
    """In-memory store for hierarchical comment threads and @mention extraction."""

    def __init__(self):
        self._threads: Dict[str, CommentThread] = {}

    def parse_mentions(self, content: str) -> List[str]:
        """Extracts @mention usernames from comment content string."""
        return re.findall(r"@([a-zA-Z0-9_\.\-]+)", content)

    async def add_comment(self, comment: CommentThread) -> CommentThread:
        extracted_mentions = self.parse_mentions(comment.content)
        if extracted_mentions:
            comment.mentions = list(set(comment.mentions + extracted_mentions))

        self._threads[comment.id] = comment
        logger.debug(
            f"Added comment '{comment.id}' by '{comment.author_id}' for section '{comment.section_id}'"
        )
        return comment

    async def get_threads_for_section(
        self, session_id: str, section_id: str, organization_id: str = "default"
    ) -> List[CommentThread]:
        threads = [
            c
            for c in self._threads.values()
            if c.session_id == session_id
            and c.section_id == section_id
            and c.organization_id == organization_id
        ]
        threads.sort(key=lambda x: x.created_at)
        return threads
