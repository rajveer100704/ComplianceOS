# Shared Memory Engine — Database Schema & Data Models

## Memory Schema Definitions

### `memory_items` Table
- `id` (UUID, Primary Key)
- `organization_id` (String, Indexed)
- `memory_type` (Enum: `semantic`, `episodic`, `organizational`, `reviewer`, `workflow`)
- `content` (Text / JSONB)
- `importance_score` (Float, 0.0 - 1.0)
- `relevance_score` (Float, 0.0 - 1.0)
- `ttl_seconds` (Integer, Optional)
- `created_at` (Timestamp UTC)
- `updated_at` (Timestamp UTC)
