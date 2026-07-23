"""Report Drafting Agent (Sprint 2.6) executing ReportDraftingPipeline over state artifacts."""

import logging
from typing import Optional
from agents.base import Agent
from agent_runtime.state import AgentRuntimeState
from llm.base import BaseLLMProvider
from reporting_ai import (
    ReportDraftingPipeline,
    ReportContext,
    StructuredReport,
    ReportFormat,
)

logger = logging.getLogger("agents.report_drafting")


class ReportDraftingAgent(Agent):
    """Agent transforming requirements, verification findings, risk results, and policy decisions into structured audit reports."""

    name = "report_drafting"
    description = "Transforms structured requirements, verification findings, and risk scores into audit-ready compliance reports."

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        super().__init__(llm_provider)
        self.pipeline = ReportDraftingPipeline(llm_provider=self.llm_provider)

    async def invoke(self, state: AgentRuntimeState) -> AgentRuntimeState:
        """Executes report generation pipeline over state artifacts."""
        logger.info(f"ReportDraftingAgent compiling report for run {state.run_id}")

        context = ReportContext(
            requirements=state.requirements,
            verification_results=state.claims,
            risk_results=state.risk_assessment,
            policy_results=state.policy_results,
            organization_id=state.organization_id,
            format=ReportFormat.AUDIT,
        )

        report: StructuredReport = await self.pipeline.generate_report(context)

        # Attach structured report to state
        state.report = report.model_dump()
        state.report_sections = [s.model_dump() for s in report.sections]
        state.report_trace = report.trace.model_dump() if report.trace else {}
        state.current_step = "report_drafting_completed"

        logger.info(
            f"Report generated successfully with {len(report.sections)} section(s) for run {state.run_id}"
        )
        return state
