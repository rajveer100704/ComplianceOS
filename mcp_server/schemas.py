"""Canonical DTOs and models for Model Context Protocol (MCP) Ecosystem (Sprint 8)."""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field


class JSONRPCRequest(BaseModel):
    """Standard JSON-RPC 2.0 request envelope."""

    model_config = ConfigDict(from_attributes=True)

    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[Union[str, int]] = 1


class JSONRPCError(BaseModel):
    """Standard JSON-RPC 2.0 error object."""

    model_config = ConfigDict(from_attributes=True)

    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCResponse(BaseModel):
    """Standard JSON-RPC 2.0 response envelope."""

    model_config = ConfigDict(from_attributes=True)

    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None
    id: Optional[Union[str, int]] = 1


class MCPTool(BaseModel):
    """Schema descriptor for exposed MCP tool."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str
    inputSchema: Dict[str, Any] = Field(default_factory=dict)


class MCPResource(BaseModel):
    """Descriptor for exposed MCP read-only resource."""

    model_config = ConfigDict(from_attributes=True)

    uri: str
    name: str
    description: str
    mimeType: str = "application/json"


class MCPPrompt(BaseModel):
    """Descriptor for exposed MCP prompt template."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str
    arguments: List[Dict[str, Any]] = Field(default_factory=list)
    template: str
