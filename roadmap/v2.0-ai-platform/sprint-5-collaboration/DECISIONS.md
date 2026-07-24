# Real-Time Collaboration — Key Design Decisions Log

## Summary of Decisions

1. **Non-Blocking Section Locking**: Section locks are exclusive per section ID with mandatory TTL auto-expiry.
2. **Integrated Activity Stream**: Every collaboration action (comment, lock, approval) emits an `ActivityEvent` indexed into Sprint 3 Reviewer Memory and Sprint 4 Knowledge Graph.
3. **Stateless Presence Tracker**: Heartbeat-based presence tracker evaluating active session timeouts without blocking database locks.
