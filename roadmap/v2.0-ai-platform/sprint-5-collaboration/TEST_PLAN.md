# Real-Time Collaboration — Test Plan

## Test Strategy

1. **Unit Tests (`tests/collaboration/test_collaboration_core.py`)**: Validate workspace creation, session management, and comment tree nesting.
2. **Section Lock Concurrency Tests (`tests/collaboration/test_section_locks.py`)**: Test concurrent lock acquisition attempts, verify lock rejections, and test TTL auto-expiration.
3. **Presence Tracker Tests (`tests/collaboration/test_presence.py`)**: Test heartbeat updates and stale presence timeout filtering.
4. **Audit Activity & Integration Tests (`tests/collaboration/test_activity_stream.py`)**: Verify activity events emit correctly to Sprint 3 Memory and Sprint 4 Knowledge Graph.
