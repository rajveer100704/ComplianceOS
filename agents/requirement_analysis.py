"""Requirement Analysis Agent (Sprint 2.2) executing layout parsing, relationship building, requirement extraction, and validation."""

import os
import logging
from typing import Optional
from agents.base import Agent
from agent_runtime.state import AgentRuntimeState
from llm.base import BaseLLMProvider
from document_processing import (
    parser_registry,
    LayoutProcessor,
    RelationshipBuilder,
    RequirementExtractor,
    RequirementValidator,
    RequirementAnalysisResult,
    ElementType,
)

logger = logging.getLogger("agents.requirement_analysis")


class RequirementAnalysisAgent(Agent):
    """Agent transforming regulatory documents into structured Requirement objects and relationship graphs."""

    name = "requirement_analysis"
    description = "Parses regulatory documents, extracts structured mandatory/definition requirements, and builds element link graph."

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        super().__init__(llm_provider)
        self.layout_processor = LayoutProcessor()
        self.relationship_builder = RelationshipBuilder()
        self.extractor = RequirementExtractor()
        self.validator = RequirementValidator()

    async def invoke(self, state: AgentRuntimeState) -> AgentRuntimeState:
        """Executes full document processing pipeline over state input."""
        file_path = state.metadata.get("file_path", "")
        text_content = state.metadata.get("text_content", "")
        regulator = state.metadata.get("regulator", "FAA")

        logger.info(
            f"RequirementAnalysisAgent processing document for run {state.run_id}"
        )

        parser = parser_registry.get()
        elements = await parser.parse(file_path=file_path, text_content=text_content)

        # Stage 1: Layout processing
        processed_elements = self.layout_processor.process_layout(elements)

        # Stage 2: Relationship building
        relationships = self.relationship_builder.build_relationships(
            processed_elements
        )

        # Stage 3: Requirement extraction
        extracted_reqs = self.extractor.extract_requirements(
            processed_elements, default_regulator=regulator
        )

        # Stage 4: Validation
        valid_reqs, warnings = self.validator.validate(extracted_reqs)

        # Compile statistics
        tables_count = sum(1 for e in processed_elements if e.type == ElementType.TABLE)
        figures_count = sum(
            1 for e in processed_elements if e.type == ElementType.FIGURE
        )

        result = RequirementAnalysisResult(
            document_id=state.run_id,
            filename=os.path.basename(file_path) if file_path else "document.txt",
            total_pages=max([e.page for e in processed_elements], default=1),
            requirements=valid_reqs,
            elements=processed_elements,
            relationships=relationships,
            statistics={
                "total_elements": len(processed_elements),
                "total_requirements": len(valid_reqs),
                "tables_count": tables_count,
                "figures_count": figures_count,
                "relationships_count": len(relationships),
            },
            warnings=warnings,
        )

        # Attach to shared AgentRuntimeState
        state.requirements = [r.model_dump() for r in valid_reqs]
        state.metadata["requirement_analysis_result"] = result.model_dump()
        state.current_step = "requirement_analysis_completed"

        logger.info(f"Extracted {len(valid_reqs)} valid requirements from document")
        return state
