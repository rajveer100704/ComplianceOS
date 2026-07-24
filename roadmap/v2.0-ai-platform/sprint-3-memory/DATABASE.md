# Shared Memory Engine — Database Schema & Data Models

## Memory Schema Definitions

### `memory_items` Table Schema

| Column | Type | Constraints / Description |
| :--- | :--- | :--- |
| `id` | UUID / String | Primary Key |
| `organization_id` | String | Indexed, Tenant Isolation |
| `memory_type` | Enum | `semantic`, `episodic`, `organizational`, `reviewer`, `workflow` |
| `content` | Text | Raw or compressed memory text content |
| `metadata` | JSONB | Additional key-value metadata filters |
| `importance_score` | Float | 0.0 (Trivial) to 1.0 (Critical) |
| `relevance_score` | Float | Computed dynamically during retrieval |
| `ttl_seconds` | Integer | Optional TTL duration |
| `version` | String | Default `v1.0.0`, Append-only versioning (e.g. `v1.0.1`) |
| `checksum` | String | SHA-256 content checksum computed automatically |
| `source_agent` | String | e.g. `RequirementAnalysisAgent`, `VerificationAgent` |
| `source_entity` | String | e.g. `REQ-001`, `CLM-002` |
| `linked_entity_ids` | JSONB / Array | Sprint 4 Knowledge Graph linked entity IDs |
| `embedding_id` | String | Vector embedding reference ID |
| `embedding_model` | String | Default `all-MiniLM-L6-v2` embedding model name |
| `graph_node_id` | String | Sprint 4 Knowledge Graph node pointer |
| `graph_edge_ids` | JSONB / Array | Sprint 4 Knowledge Graph edge pointers |
| `is_archived` | Boolean | Default `False`, Soft-deletion indicator |
| `is_pinned` | Boolean | Default `False`, Overrides TTL expiration |
| `created_at` | Timestamp UTC | Creation timestamp |
| `updated_at` | Timestamp UTC | Last modification timestamp |
