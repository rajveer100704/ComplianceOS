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
| `version` | String | Default `v1.0.0`, Append-only versioning |
| `checksum` | String | SHA-256 content checksum |
| `source_agent` | String | e.g. `RequirementAnalysisAgent`, `VerificationAgent` |
| `source_entity` | String | e.g. `REQ-001`, `CLM-002` |
| `linked_entities` | JSONB / Array | Sprint 4 Knowledge Graph linked entity IDs |
| `embedding_id` | String | Vector embedding reference ID |
| `graph_node_id` | String | Sprint 4 Knowledge Graph node pointer |
| `is_archived` | Boolean | Default `False`, Soft-deletion indicator |
| `is_pinned` | Boolean | Default `False`, Overrides TTL expiration |
| `created_at` | Timestamp UTC | Creation timestamp |
| `updated_at` | Timestamp UTC | Last modification timestamp |
