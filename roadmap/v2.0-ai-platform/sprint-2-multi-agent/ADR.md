# Architecture Decision Record (ADR) — Sprint 2.2 Document Processing & Requirement Analysis

- **Status**: Approved
- **Date**: 2026-07-23
- **Deciders**: ComplianceOS Core Architecture Team

---

## 1. Context & Problem Statement

Standard regulatory compliance verification relies on converting dense, layout-heavy PDF standards (e.g. FAA Part 450, NRC 10 CFR, ASME BPVC) into structured requirements. Naive plain-text extraction or chunk-by-character slicing destroys section hierarchies, table-caption relationships, cross-references, and typed requirement definitions (e.g., distinguishing mandatory constraints from informational definitions).

## 2. Decision

We decide to build a dedicated **Layout-Aware Document Processing Pipeline** (`document_processing/`) decoupled from agent orchestration:

1. **Canonical Schema (`document_processing/schemas.py`)**: Canonical `DocumentElement` model (`id`, `type`, `page`, `bbox`, `text`, `parent_id`, `children`, `metadata`, `reading_order`) and `Requirement` model (`id`, `type`, `clause`, `section`, `title`, `text`, `mandatory`, `source_element_ids`).
2. **Layout-Aware Parsing (`document_processing/layout.py`)**: Typed element classification (`Title`, `Heading`, `Paragraph`, `Table`, `Figure`, `Caption`, `List`, `Footnote`).
3. **Relational Link Graph (`document_processing/relationships.py`)**: Preserves structural links (`contains`, `caption_of`, `references`, `parent_child`, `sequence`).
4. **Requirement Extractor & Validator (`document_processing/requirement_extractor.py` & `validator.py`)**: Identifies requirement candidates, classifies definition vs. constraint types, and validates clause completeness.
5. **Requirement Analysis Agent (`agents/requirement_analysis.py`)**: Orchestrates the pipeline and returns a structured `RequirementAnalysisResult` attached to `AgentRuntimeState.requirements`.

## 3. Consequences

### Positive
- Preserves document lineage and table/figure captions for explainable compliance review.
- Prevents vendor lock-in by normalizing parser output into `DocumentElement`.
- Prepares exact graph edges for Sprint 4 (Compliance Knowledge Graph).

### Negative
- Higher ingestion latency compared to un-structured plain-text splitters (mitigated by caching layout elements).
