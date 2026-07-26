# Model Context Protocol (MCP) Ecosystem — Test Plan

## Test Strategy

1. **Unit Tests (`tests/mcp/test_mcp_server.py`)**: Validate JSON-RPC 2.0 request parsing, tool dispatching, resource reading, and prompt generation.
2. **EventBus Telemetry Tests**: Verify that tool execution publishes `MCP_TOOL_EXECUTED` `PlatformEvent` onto `EventBus`.
3. **Interoperability Tests**: Verify JSON-RPC error handling for unrecognized tool names or malformed JSON payloads.
