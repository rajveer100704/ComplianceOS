"""Unit & integration tests for Model Context Protocol (MCP) Ecosystem (Sprint 8)."""

import pytest
from events import EventBus
from governance import GovernanceManager
from mcp_server import MCPServer


@pytest.mark.asyncio
async def test_mcp_tools_list_and_call():
    bus = EventBus()
    gov = GovernanceManager(event_bus=bus)
    server = MCPServer(event_bus=bus)

    # 1. Test tools/list
    res_list = await server.handle_jsonrpc(
        {"jsonrpc": "2.0", "method": "tools/list", "id": 101}
    )
    assert res_list["error"] is None
    tools = res_list["result"]["tools"]
    assert len(tools) >= 3
    tool_names = [t["name"] for t in tools]
    assert "verify_claim" in tool_names
    assert "search_knowledge_graph" in tool_names

    # 2. Test tools/call -> publishes PlatformEvent (MCP_TOOL_EXECUTED) onto EventBus
    res_call = await server.handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "verify_claim",
                "arguments": {"claim_text": "Public risk casualty expectancy < 1e-4"},
            },
            "id": 102,
        },
        organization_id="org-acme",
    )
    assert res_call["error"] is None
    assert "SUPPORTED" in res_call["result"]["content"][0]["text"]

    # 3. Verify Sprint 6 GovernanceManager observed tool execution automatically
    audit_entries = await gov.get_audit_trail("org-acme")
    assert len(audit_entries) >= 1
    assert audit_entries[-1].event_type == "MCP_TOOL_EXECUTED"


@pytest.mark.asyncio
async def test_mcp_resources_list_and_read():
    server = MCPServer()

    # 1. Test resources/list
    res_list = await server.handle_jsonrpc(
        {"jsonrpc": "2.0", "method": "resources/list", "id": 201}
    )
    assert res_list["error"] is None
    resources = res_list["result"]["resources"]
    assert len(resources) >= 2

    # 2. Test resources/read
    res_read = await server.handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "method": "resources/read",
            "params": {"uri": "resource://compliance/rules"},
            "id": 202,
        }
    )
    assert res_read["error"] is None
    assert "rule-grounding" in res_read["result"]["contents"][0]["text"]


@pytest.mark.asyncio
async def test_mcp_prompts_list_and_get():
    server = MCPServer()

    # 1. Test prompts/list
    res_list = await server.handle_jsonrpc(
        {"jsonrpc": "2.0", "method": "prompts/list", "id": 301}
    )
    assert res_list["error"] is None
    prompts = res_list["result"]["prompts"]
    assert len(prompts) >= 1

    # 2. Test prompts/get
    res_get = await server.handle_jsonrpc(
        {
            "jsonrpc": "2.0",
            "method": "prompts/get",
            "params": {
                "name": "regulatory_audit_template",
                "arguments": {"standard": "FAA Part 450"},
            },
            "id": 302,
        }
    )
    assert res_get["error"] is None
    assert "FAA Part 450" in res_get["result"]["messages"][0]["content"]["text"]


@pytest.mark.asyncio
async def test_mcp_invalid_method_error():
    server = MCPServer()

    res_err = await server.handle_jsonrpc(
        {"jsonrpc": "2.0", "method": "invalid/method", "id": 401}
    )
    assert res_err["result"] is None
    assert res_err["error"]["code"] == -32601
