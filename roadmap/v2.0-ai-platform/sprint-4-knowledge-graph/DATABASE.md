# Regulatory Knowledge Graph Engine — Database Schema & Graph Models

## Graph Storage Schema

### `graph_nodes` Table / Model Schema

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `id` | String | Unique Node ID (e.g. `node-req-450.115`) |
| `logical_id` | String | Permanent entity identity |
| `organization_id` | String | Tenant isolation partition key |
| `node_type` | Enum | `REGULATION`, `REQUIREMENT`, `CLAIM`, `EVIDENCE`, `DECISION`, `MEMORY` |
| `label` | String | Human-readable node label / summary |
| `properties` | JSONB | Type-specific property dictionary |
| `checksum` | String | SHA-256 node content checksum |
| `source_agent` | String | Agent that created the node |
| `version` | String | Append-only revision string (e.g. `v1.0.0`) |
| `created_at` | Timestamp UTC | Node creation timestamp |

---

### `graph_edges` Table / Model Schema

| Attribute | Type | Description |
| :--- | :--- | :--- |
| `id` | String | Unique Edge ID (e.g. `edge-cites-101`) |
| `organization_id` | String | Tenant isolation partition key |
| `source_node_id` | String | Origin vertex ID |
| `target_node_id` | String | Destination vertex ID |
| `edge_type` | Enum | `CONTAINS`, `REQUIRES`, `SUPPORTS`, `CONTRADICTS`, `VERIFIES`, `CITES`, `GENERATED_BY`, `SUPERSEDES` |
| `weight` | Float | Edge weight / confidence score (0.0 to 1.0) |
| `properties` | JSONB | Edge metadata dictionary |
| `created_at` | Timestamp UTC | Edge creation timestamp |
