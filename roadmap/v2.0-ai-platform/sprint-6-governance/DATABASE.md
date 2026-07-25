# AI Governance — Database Schema & Data Models

## Relational Schema Definitions

### `audit_ledger_entries` Table
- `entry_id` (UUID, Primary Key)
- `sequence_number` (BigInt, Indexed)
- `organization_id` (String, Indexed)
- `event_id` (String)
- `event_type` (String)
- `actor_id` (String)
- `target_id` (String)
- `prev_hash` (String)
- `current_hash` (String, SHA-256)
- `timestamp` (Timestamp UTC)

### `compliance_rules` Table
- `rule_id` (String, Primary Key)
- `organization_id` (String, Indexed)
- `name` (String)
- `metric_name` (String) — e.g. `grounding_score`, `hallucination_risk`
- `operator` (Enum: `GREATER_THAN_EQUAL`, `LESS_THAN_EQUAL`, `EQUALS`)
- `threshold_value` (Float)
- `is_blocking` (Boolean)

### `compliance_violations` Table
- `violation_id` (UUID, Primary Key)
- `organization_id` (String, Indexed)
- `rule_id` (String, Foreign Key)
- `event_id` (String)
- `severity` (Enum: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- `details` (JSONB)
- `created_at` (Timestamp UTC)
