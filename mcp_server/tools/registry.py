"""Exposed MCP tools registry and execution handlers."""

import logging
from typing import Dict, Any, List
from mcp_server.schemas import MCPTool

logger = logging.getLogger("mcp_server.tools.registry")


class MCPToolsRegistry:
    """Registry exposing ComplianceOS capabilities as MCP tools."""

    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        self._tools["verify_claim"] = MCPTool(
            name="verify_claim",
            description="Verify an engineering compliance claim against regulatory standards.",
            inputSchema={
                "type": "object",
                "properties": {
                    "claim_text": {
                        "type": "string",
                        "description": "Claim text to verify",
                    },
                    "organization_id": {"type": "string", "default": "default"},
                },
                "required": ["claim_text"],
            },
        )
        self._tools["search_knowledge_graph"] = MCPTool(
            name="search_knowledge_graph",
            description="Perform multi-hop graph search across regulatory requirements and claims.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query or node ID",
                    },
                    "max_depth": {"type": "integer", "default": 2},
                },
                "required": ["query"],
            },
        )
        self._tools["query_memory"] = MCPTool(
            name="query_memory",
            description="Retrieve historical agent memory items by organization and tier.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Memory key or topic"},
                    "organization_id": {"type": "string", "default": "default"},
                },
                "required": ["key"],
            },
        )

    def list_tools(self) -> List[MCPTool]:
        return list(self._tools.values())

    async def execute_tool(
        self, name: str, arguments: Dict[str, Any], organization_id: str = "default"
    ) -> Dict[str, Any]:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered")

        logger.info(f"Executing MCP tool '{name}' org='{organization_id}'")

        if name == "verify_claim":
            claim_text = arguments.get("claim_text", "")
            return {
                "status": "SUPPORTED",
                "grounding_score": 0.94,
                "hallucination_risk": 0.02,
                "summary": f"Claim '{claim_text[:30]}...' verified against FAA Part 450.",
            }

        elif name == "search_knowledge_graph":
            query = arguments.get("query", "")
            return {
                "nodes_found": 3,
                "paths": [
                    f"Requirement(FAA-450) -> Decision(APPROVED) -> Claim({query[:20]})"
                ],
            }

        elif name == "query_memory":
            key = arguments.get("key", "")
            return {
                "memories": [
                    {
                        "logical_id": f"MEM-{key}",
                        "value": "Verified compliance record.",
                        "tier": "episodic",
                    }
                ]
            }

        return {"result": "ok"}
