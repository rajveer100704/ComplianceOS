# Model Context Protocol (MCP) Ecosystem — Database Schema & Data Models

## Relational Schema Definitions

### `mcp_tool_definitions` Table
- `name` (String, Primary Key) — e.g. `verify_claim`, `search_knowledge_graph`
- `description` (Text)
- `input_schema` (JSONB) — Pydantic JSON schema for parameters
- `is_enabled` (Boolean)
- `created_at` (Timestamp UTC)

### `mcp_resources` Table
- `uri` (String, Primary Key) — e.g. `resource://compliance/rules`, `resource://audit/ledger`
- `name` (String)
- `description` (Text)
- `mime_type` (String) — e.g. `application/json`
- `created_at` (Timestamp UTC)

### `mcp_prompts` Table
- `name` (String, Primary Key) — e.g. `regulatory_audit_template`
- `description` (Text)
- `arguments` (JSONB)
- `template_text` (Text)
- `created_at` (Timestamp UTC)
