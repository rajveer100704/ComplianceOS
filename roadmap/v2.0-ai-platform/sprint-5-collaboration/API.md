# Real-Time Collaboration — API Specification

## `CollaborationManager` Interface Methods

```python
async def create_workspace(name: str, organization_id: str = "default") -> Workspace:
    ...

async def create_session(workspace_id: str, title: str, organization_id: str = "default") -> ReviewSession:
    ...

async def acquire_lock(session_id: str, section_id: str, user_id: str, ttl_seconds: int = 300) -> LockStatus:
    ...

async def release_lock(session_id: str, section_id: str, user_id: str) -> bool:
    ...

async def add_comment(
    session_id: str,
    section_id: str,
    author_id: str,
    content: str,
    parent_comment_id: Optional[str] = None,
    mentions: Optional[List[str]] = None,
) -> CommentThread:
    ...

async def update_presence(session_id: str, user_id: str, status: PresenceStatus) -> UserPresence:
    ...

async def get_activity_log(session_id: str) -> List[ActivityEvent]:
    ...
```
