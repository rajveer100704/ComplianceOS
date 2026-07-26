"""Exposed MCP prompt templates and instruction builders."""

import logging
from typing import Dict, Any, List
from mcp_server.schemas import MCPPrompt

logger = logging.getLogger("mcp_server.prompts.registry")


class MCPPromptsRegistry:
    """Registry exposing pre-configured system prompts for regulatory auditing."""

    def __init__(self):
        self._prompts: Dict[str, MCPPrompt] = {}
        self._register_default_prompts()

    def _register_default_prompts(self):
        self._prompts["regulatory_audit_template"] = MCPPrompt(
            name="regulatory_audit_template",
            description="System prompt for performing regulatory compliance verification audits.",
            arguments=[
                {
                    "name": "standard",
                    "description": "Target regulation e.g. FAA Part 450, NRC 10 CFR",
                    "required": True,
                }
            ],
            template=(
                "You are an expert regulatory compliance auditor. "
                "Audit the following claim against standard '{standard}'. "
                "Verify evidence grounding and report any missing requirements."
            ),
        )

    def list_prompts(self) -> List[MCPPrompt]:
        return list(self._prompts.values())

    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> str:
        if name not in self._prompts:
            raise KeyError(f"Prompt '{name}' is not registered")

        prompt_def = self._prompts[name]
        standard = arguments.get("standard", "FAA Part 450")
        return prompt_def.template.format(standard=standard)
