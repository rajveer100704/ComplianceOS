# Real-Time Collaboration — Domain Model Reference

## Domain Taxonomy & Entity Relationships

```
Workspace
    │
    ├── ReviewSession
    │       │
    │       ├── Participant (User / AI Agent)
    │       ├── Presence (Status, Cursor Offset)
    │       ├── SectionLock (Section ID, Owner, TTL)
    │       ├── CommentThread (Inline text offset, Mentions, Replies)
    │       ├── Annotation (Highlight, Target Element)
    │       └── ActivityEvent (Audit log entry)
    └── ApprovalGate (Sign-off roles)
```

### Key Models

1. **`Workspace`**: High-level organizational tenant container.
2. **`ReviewSession`**: Active review workstation instance.
3. **`SectionLock`**: Exclusive lock on a document section or claim clause.
4. **`CommentThread`**: Threaded conversation with inline highlight offsets and `@mentions`.
5. **`UserPresence`**: Real-time participant online state and active cursor offset.
6. **`ActivityEvent`**: Audit event stream entry emitted to Memory and Knowledge Graph.
