# Real-Time Collaboration — Database Schema & Data Models

## Relational Schema Definitions

### `workspaces` Table
- `id` (UUID, Primary Key)
- `organization_id` (String, Indexed)
- `name` (String)
- `description` (Text)
- `status` (Enum: `active`, `archived`)
- `created_at` (Timestamp UTC)

### `review_sessions` Table
- `id` (UUID, Primary Key)
- `workspace_id` (UUID, Foreign Key)
- `organization_id` (String, Indexed)
- `title` (String)
- `active_participants_count` (Integer)
- `created_at` (Timestamp UTC)

### `section_locks` Table
- `id` (UUID, Primary Key)
- `session_id` (UUID, Foreign Key)
- `section_id` (String, Indexed)
- `owner_user_id` (String)
- `expires_at` (Timestamp UTC)
- `created_at` (Timestamp UTC)

### `comment_threads` Table
- `id` (UUID, Primary Key)
- `session_id` (UUID, Foreign Key)
- `section_id` (String, Indexed)
- `author_id` (String)
- `content` (Text)
- `parent_comment_id` (UUID, Optional)
- `mentions` (JSONB)
- `created_at` (Timestamp UTC)
