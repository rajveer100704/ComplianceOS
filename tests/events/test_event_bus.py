"""Unit tests for Unified EventBus publish/subscribe routing engine."""

import pytest
from events import EventBus, PlatformEvent, EventCategory


@pytest.mark.asyncio
async def test_event_bus_subscribe_and_publish():
    bus = EventBus()
    received_events = []

    async def collab_subscriber(event: PlatformEvent):
        received_events.append(event)

    # Subscribe to COLLABORATION events
    bus.subscribe(collab_subscriber, category=EventCategory.COLLABORATION)

    # Publish COLLABORATION event
    evt = PlatformEvent(
        event_type="LOCK_ACQUIRED",
        category=EventCategory.COLLABORATION,
        actor_id="user-alice",
        target_id="CLM-001",
    )
    delivered = await bus.publish(evt)

    assert delivered == 1
    assert len(received_events) == 1
    assert received_events[0].event_type == "LOCK_ACQUIRED"
    assert received_events[0].actor_id == "user-alice"


@pytest.mark.asyncio
async def test_event_bus_wildcard_subscriber():
    bus = EventBus()
    received_events = []

    async def global_subscriber(event: PlatformEvent):
        received_events.append(event)

    # Subscribe to all events (wildcard)
    bus.subscribe(global_subscriber, category=None)

    evt_mem = PlatformEvent(
        event_type="MEMORY_STORED",
        category=EventCategory.MEMORY,
        actor_id="AgentMemory",
        target_id="MEM-001",
    )
    delivered = await bus.publish(evt_mem)

    assert delivered == 1
    assert len(received_events) == 1
    assert received_events[0].event_type == "MEMORY_STORED"
