# Real-Time Collaboration — Risk Management Document

## Identified Risks & Mitigation Strategies

1. **Deadlock in Section Locking**: Reviewer acquiring lock and abandoning browser session.
   - *Mitigation*: Enforce mandatory TTL (default 300s) on all section locks and auto-release on stale presence timeout.
2. **Cross-Tenant Comment Leakage**: Reviewer comment threads visible across organization boundaries.
   - *Mitigation*: Mandatory `organization_id` partitioning on all queries.
3. **Stale Presence Overcount**: Disconnected reviewers remaining flagged `ONLINE`.
   - *Mitigation*: 30-second heartbeat window with automatic status demotion to `IDLE` / `OFFLINE`.
