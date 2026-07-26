# Model Context Protocol (MCP) Ecosystem — Domain Model Reference

## Domain Taxonomy & Entity Relationships

```
MCPServer
    │
    ├── JSON-RPC Protocol Handler (JSONRPCRequest, JSONRPCResponse, JSONRPCError)
    ├── Tools Registry (MCPTool: verify_claim, search_knowledge_graph, query_memory)
    ├── Resources Provider (MCPResource: compliance_rules, audit_ledger, reports)
    ├── Prompts Registry (MCPPrompt: regulatory_audit_template, claim_verification_prompt)
    └── PlatformEvent Emitter (Publishes MCP_TOOL_EXECUTED to EventBus)
```

### Key Models

1. **`JSONRPCRequest` / `JSONRPCResponse`**: Standard JSON-RPC 2.0 message envelope wrappers.
2. **`MCPTool`**: Tool definition schema exposing tool name, description, and parameter JSON schema.
3. **`MCPResource`**: Read-only resource descriptor with URI, name, description, and MIME type.
4. **`MCPPrompt`**: Structured prompt template with arguments and templated instruction text.
