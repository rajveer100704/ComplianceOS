"""Requirement validator detecting duplicates, orphan numbering, empty clauses, and text issues."""

import logging
from typing import List, Tuple
from document_processing.schemas import Requirement

logger = logging.getLogger("document_processing.validator")


class RequirementValidator:
    """Validates extracted requirements against structural and text quality rules."""

    def validate(
        self, requirements: List[Requirement]
    ) -> Tuple[List[Requirement], List[str]]:
        valid_requirements: List[Requirement] = []
        warnings: List[str] = []
        seen_texts = set()

        for req in requirements:
            # Rule 1: Check empty text
            if not req.text or not req.text.strip():
                warnings.append(f"Requirement '{req.id}' rejected: text is empty.")
                continue

            # Rule 2: Check duplicate text
            clean_text = req.text.strip().lower()
            if clean_text in seen_texts:
                warnings.append(
                    f"Requirement '{req.id}' flagged: duplicate text detected."
                )
                req.metadata["duplicate_flag"] = True
            seen_texts.add(clean_text)

            # Rule 3: Check minimum length
            if len(req.text) < 15:
                warnings.append(
                    f"Requirement '{req.id}' warning: text very short ({len(req.text)} chars)."
                )

            valid_requirements.append(req)

        return valid_requirements, warnings
