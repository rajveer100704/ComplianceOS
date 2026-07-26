"""Model Context Protocol (MCP) Ecosystem package for v2.0 AI Platform."""

from mcp_server.schemas import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    MCPTool,
    MCPResource,
    MCPPrompt,
)
from mcp_server.tools.registry import MCPToolsRegistry
from mcp_server.resources.provider import MCPResourcesProvider
from mcp_server.prompts.registry import MCPPromptsRegistry
from mcp_server.server import MCPServer

__all__ = [
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "MCPTool",
    "MCPResource",
    "MCPPrompt",
    "MCPToolsRegistry",
    "MCPResourcesProvider",
    "MCPPromptsRegistry",
    "MCPServer",
]
