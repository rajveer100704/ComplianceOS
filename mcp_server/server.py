"""Centralized MCPServer facade processing JSON-RPC 2.0 requests and emitting PlatformEvent streams."""

import logging
from typing import Dict, Any, Optional
from mcp_server.schemas import (
    JSONRPCResponse,
    JSONRPCError,
)
from mcp_server.tools.registry import MCPToolsRegistry
from mcp_server.resources.provider import MCPResourcesProvider
from mcp_server.prompts.registry import MCPPromptsRegistry
from events.bus import EventBus
from events.schemas import PlatformEvent, EventCategory

logger = logging.getLogger("mcp_server.server")


class MCPServer:
    """Centralized Model Context Protocol (MCP) server handling JSON-RPC 2.0 messages."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.tools_registry = MCPToolsRegistry()
        self.resources_provider = MCPResourcesProvider()
        self.prompts_registry = MCPPromptsRegistry()
        self.event_bus = event_bus

    async def handle_jsonrpc(
        self, request_payload: Dict[str, Any], organization_id: str = "default"
    ) -> Dict[str, Any]:
        req_id = request_payload.get("id", 1)
        method = request_payload.get("method", "")
        params = request_payload.get("params", {})

        logger.info(f"MCPServer handling JSON-RPC method='{method}' req_id={req_id}")

        try:
            if method == "tools/list":
                tools = self.tools_registry.list_tools()
                return JSONRPCResponse(
                    id=req_id, result={"tools": [t.model_dump() for t in tools]}
                ).model_dump()

            elif method == "tools/call":
                name = params.get("name", "")
                arguments = params.get("arguments", {})
                res = await self.tools_registry.execute_tool(
                    name, arguments, organization_id=organization_id
                )

                # Emit MCP_TOOL_EXECUTED PlatformEvent onto EventBus for Governance observation
                if self.event_bus:
                    evt = PlatformEvent(
                        event_id=f"mcp-tool-{req_id}",
                        event_type="MCP_TOOL_EXECUTED",
                        category=EventCategory.SYSTEM,
                        organization_id=organization_id,
                        actor_id="MCPServer",
                        target_id=name,
                        payload={"arguments": arguments, "result": res},
                    )
                    await self.event_bus.publish(evt)

                return JSONRPCResponse(
                    id=req_id, result={"content": [{"type": "text", "text": str(res)}]}
                ).model_dump()

            elif method == "resources/list":
                resources = self.resources_provider.list_resources()
                return JSONRPCResponse(
                    id=req_id, result={"resources": [r.model_dump() for r in resources]}
                ).model_dump()

            elif method == "resources/read":
                uri = params.get("uri", "")
                content = await self.resources_provider.read_resource(
                    uri, organization_id=organization_id
                )
                return JSONRPCResponse(
                    id=req_id,
                    result={
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "application/json",
                                "text": content,
                            }
                        ]
                    },
                ).model_dump()

            elif method == "prompts/list":
                prompts = self.prompts_registry.list_prompts()
                return JSONRPCResponse(
                    id=req_id, result={"prompts": [p.model_dump() for p in prompts]}
                ).model_dump()

            elif method == "prompts/get":
                name = params.get("name", "")
                arguments = params.get("arguments", {})
                prompt_text = await self.prompts_registry.get_prompt(name, arguments)
                return JSONRPCResponse(
                    id=req_id,
                    result={
                        "messages": [
                            {
                                "role": "user",
                                "content": {"type": "text", "text": prompt_text},
                            }
                        ]
                    },
                ).model_dump()

            else:
                err = JSONRPCError(code=-32601, message=f"Method '{method}' not found")
                return JSONRPCResponse(id=req_id, error=err).model_dump()

        except Exception as exc:
            logger.error(f"Error handling MCP JSON-RPC method='{method}': {exc}")
            err = JSONRPCError(code=-32603, message=str(exc))
            return JSONRPCResponse(id=req_id, error=err).model_dump()
