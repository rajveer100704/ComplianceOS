# Model Context Protocol (MCP) Ecosystem — Key Design Decisions Log

## Summary of Decisions

1. **JSON-RPC 2.0 Compliance**: Standardized JSON-RPC 2.0 transport supporting Anthropic Claude Desktop and IDE integrations.
2. **EventBus Telemetry Emitter**: `MCPServer` publishes `PlatformEvent` (`category=SYSTEM`) to `EventBus` allowing Sprint 6 Governance to record tool audit logs automatically.
3. **Decoupled Tool Handlers**: Tools expose Pydantic JSON schemas and delegate directly to underlying platform subsystems.
