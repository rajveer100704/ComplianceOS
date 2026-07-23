"""Requirement extractor identifying clauses, mandatory constraints, and definition types from DocumentElements."""

import re
import logging
from typing import List
from document_processing.schemas import (
    DocumentElement,
    Requirement,
    RequirementType,
    ElementType,
)

logger = logging.getLogger("document_processing.requirement_extractor")

# Keyword indicators for mandatory vs definition requirements
MANDATORY_KEYWORDS = [
    "shall",
    "must",
    "required",
    "shall not",
    "mandatory",
    "enforce",
    "prohibited",
]
DEFINITION_KEYWORDS = ["means", "is defined as", "refers to", "shall mean", "denotes"]
EXCEPTION_KEYWORDS = ["except", "exempt", "unless", "provided that", "notwithstanding"]
FORMULA_KEYWORDS = ["calculated by", "formula", "equation", "ratio", "percentage"]


class RequirementExtractor:
    """Consumes DocumentElement objects and extracts structured Requirement records."""

    def extract_requirements(
        self, elements: List[DocumentElement], default_regulator: str = "FAA"
    ) -> List[Requirement]:
        requirements: List[Requirement] = []
        current_section = ""
        current_clause = ""
        req_counter = 1

        for elem in elements:
            if elem.type == ElementType.HEADING:
                current_section = elem.text
                # Extract clause pattern e.g. "450.115" or "10 CFR 50"
                match = re.search(r"(\d+(?:\.\d+)+)", elem.text)
                if match:
                    current_clause = match.group(1)
                continue

            if elem.type in (ElementType.PARAGRAPH, ElementType.LIST):
                text_lower = elem.text.lower()
                is_mandatory = any(kw in text_lower for kw in MANDATORY_KEYWORDS)

                # Determine requirement type
                if any(kw in text_lower for kw in DEFINITION_KEYWORDS):
                    req_type = RequirementType.DEFINITION
                elif any(kw in text_lower for kw in EXCEPTION_KEYWORDS):
                    req_type = RequirementType.EXCEPTION
                elif any(kw in text_lower for kw in FORMULA_KEYWORDS):
                    req_type = RequirementType.FORMULA
                elif is_mandatory:
                    req_type = RequirementType.MANDATORY_CONSTRAINT
                else:
                    req_type = RequirementType.INFORMATIVE

                # If mandatory or explicit requirement text, construct Requirement record
                if is_mandatory or req_type in (
                    RequirementType.MANDATORY_CONSTRAINT,
                    RequirementType.DEFINITION,
                    RequirementType.FORMULA,
                ):
                    req_id = f"REQ-{req_counter:03d}"
                    clause_str = current_clause or f"{default_regulator}-{req_counter}"

                    requirements.append(
                        Requirement(
                            id=req_id,
                            regulator=default_regulator,
                            section=current_section,
                            clause=clause_str,
                            title=current_section or f"Requirement {req_counter}",
                            text=elem.text,
                            type=req_type,
                            mandatory=is_mandatory,
                            confidence=0.95 if is_mandatory else 0.80,
                            source_element_ids=[elem.id],
                            page_numbers=[elem.page],
                        )
                    )
                    req_counter += 1

        return requirements
