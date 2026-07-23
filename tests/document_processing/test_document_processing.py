"""Unit tests for Document Processing pipeline: layout, relationships, requirement extraction, and validation."""

import pytest
from document_processing import (
    SimpleTextParser,
    LayoutProcessor,
    RelationshipBuilder,
    RequirementExtractor,
    RequirementValidator,
    ElementType,
    RequirementType,
)


@pytest.mark.asyncio
async def test_simple_text_parser():
    parser = SimpleTextParser()
    sample_text = "Section 450.115 Flight Safety\nThe vehicle shall satisfy flight safety analysis requirements.\nNote: This is informative."
    elements = await parser.parse(file_path="", text_content=sample_text)

    assert len(elements) == 3
    assert elements[0].type == ElementType.HEADING
    assert elements[1].type == ElementType.PARAGRAPH


@pytest.mark.asyncio
async def test_layout_processor_hierarchy():
    parser = SimpleTextParser()
    sample_text = (
        "Section 450.115 Flight Safety\nThe vehicle shall satisfy requirements."
    )
    elements = await parser.parse(file_path="", text_content=sample_text)

    processor = LayoutProcessor()
    processed = processor.process_layout(elements)

    assert processed[1].parent_id == processed[0].id
    assert processed[0].children_ids == [processed[1].id]


@pytest.mark.asyncio
async def test_relationship_builder():
    parser = SimpleTextParser()
    sample_text = "Section 450.115 Flight Safety\nThe vehicle shall satisfy requirements.\nRefer to Section 450.115 for details."
    elements = await parser.parse(file_path="", text_content=sample_text)

    builder = RelationshipBuilder()
    rels = builder.build_relationships(elements)

    assert len(rels) > 0


@pytest.mark.asyncio
async def test_requirement_extractor_and_validator():
    parser = SimpleTextParser()
    sample_text = (
        "Section 450.115 Flight Safety Analysis\n"
        "The applicant shall perform a flight safety analysis for public risk.\n"
        "Spaceport means a launch or re-entry site.\n"
    )
    elements = await parser.parse(file_path="", text_content=sample_text)

    extractor = RequirementExtractor()
    reqs = extractor.extract_requirements(elements, default_regulator="FAA")

    assert len(reqs) == 2
    assert reqs[0].mandatory is True
    assert reqs[0].type == RequirementType.MANDATORY_CONSTRAINT
    assert reqs[1].type == RequirementType.DEFINITION

    validator = RequirementValidator()
    valid_reqs, warnings = validator.validate(reqs)
    assert len(valid_reqs) == 2
