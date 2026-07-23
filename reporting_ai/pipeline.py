"""ReportDraftingPipeline orchestrating section planning, section generation, quality validation, and trace logging."""

import time
import logging
from typing import List, Optional
from reporting_ai.schemas import (
    ReportContext,
    StructuredReport,
    ReportSection,
    ReportTrace,
)
from reporting_ai.planner import ReportPlanner
from reporting_ai.sections import SectionGenerators
from reporting_ai.validator import ReportValidator
from llm.registry import llm_registry
from llm.base import BaseLLMProvider

logger = logging.getLogger("reporting_ai.pipeline")


class ReportDraftingPipeline:
    """Pipeline orchestrating structured compliance report generation."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider or llm_registry.get()
        self.planner = ReportPlanner()
        self.generators = SectionGenerators()
        self.validator = ReportValidator()

    async def generate_report(self, context: ReportContext) -> StructuredReport:
        start_time = time.perf_counter()

        # 1. Section Planning
        blueprints = self.planner.plan_sections(context.format)

        sections: List[ReportSection] = []
        all_citations: List[str] = []

        # 2. Section Generation
        exec_sec = self.generators.generate_exec_summary(context)
        sections.append(exec_sec)

        ver_sec = self.generators.generate_verification_section(context)
        sections.append(ver_sec)
        all_citations.extend(ver_sec.citations)

        risk_sec = self.generators.generate_risk_section(context)
        sections.append(risk_sec)

        rec_sec = self.generators.generate_recommendations_section(context)
        sections.append(rec_sec)

        # 3. LLM Executive Summary Enrichment
        prompt_msgs = [
            {
                "role": "user",
                "content": f"Summarize regulatory compliance audit results for {len(context.requirements)} requirement(s).",
            }
        ]
        llm_res = await self.llm_provider.generate(prompt_msgs)
        summary_text = (
            llm_res.content
            or f"Audit report covering {len(context.requirements)} requirement(s)."
        )

        # 4. Build StructuredReport
        report = StructuredReport(
            title=f"Regulatory Compliance Audit Report - {context.organization_id}",
            summary=summary_text,
            sections=sections,
            recommendations=(
                context.risk_results.get("recommendations", [])
                if context.risk_results
                else []
            ),
            citations=list(set(all_citations)),
            format=context.format,
            metadata={"organization_id": context.organization_id},
        )

        # 5. Quality Validation
        val_errors = self.validator.validate(report)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        report.trace = ReportTrace(
            prompt_version="v1.0.0",
            generation_time_ms=latency_ms,
            tokens_used=llm_res.total_tokens,
            sections_generated=len(sections),
            validation_errors=val_errors,
            confidence=0.95 if not val_errors else 0.80,
        )

        return report
