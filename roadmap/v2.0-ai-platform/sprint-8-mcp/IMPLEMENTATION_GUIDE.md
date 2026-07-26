# Model Context Protocol (MCP) Ecosystem — Implementation Guide

## Ordered Development Phases

1. **Phase A (Core Protocol Schemas)**:
   - `mcp_server/schemas.py` — `JSONRPCRequest`, `JSONRPCResponse`, `MCPTool`, `MCPResource`, `MCPPrompt`.
2. **Phase B (MCP Tools Registry & Handlers)**:
   - `mcp_server/tools/` — `verify_claim`, `search_knowledge_graph`, and `query_memory` tools.
3. **Phase C (MCP Resource Providers)**:
   - `mcp_server/resources/` — `compliance_rules`, `audit_ledger`, and `review_reports` providers.
4. **Phase D (MCP Prompt Templates)**:
   - `mcp_server/prompts/` — Regulatory audit prompt templates.
5. **Phase E (Centralized Facade & EventBus Emitter)**:
   - `mcp_server/server.py` — `MCPServer` handling JSON-RPC requests and publishing `PlatformEvent` (`category=SYSTEM`) to `EventBus`.
