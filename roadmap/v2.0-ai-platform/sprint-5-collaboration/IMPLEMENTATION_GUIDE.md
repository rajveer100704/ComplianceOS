# Real-Time Collaboration — Implementation Guide

## Ordered Development Phases

1. **Phase A (Core Domain Models & Schemas)**:
   - `collaboration/schemas.py` — `Workspace`, `ReviewSession`, `SectionLock`, `CommentThread`, `UserPresence`, `ActivityEvent`.
2. **Phase B (Threaded Comments & Annotations Engine)**:
   - `collaboration/comments/store.py` — Comment thread creation, nested reply tree, `@mention` parser.
3. **Phase C (Presence & Concurrency Lock Manager)**:
   - `collaboration/presence/lock_manager.py` — Non-blocking section lock engine with TTL auto-expiration.
   - `collaboration/presence/tracker.py` — Presence heartbeat tracker.
4. **Phase D (Activity Audit Stream & Event Bus)**:
   - `collaboration/webhooks/dispatcher.py` — Activity stream dispatcher logging to Memory & Knowledge Graph.
5. **Phase E (Centralized Facade & Integration)**:
   - `collaboration/manager.py` — `CollaborationManager` facade serving SPA workstation requests.
