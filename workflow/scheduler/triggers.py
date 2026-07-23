"""Extensible trigger types for workflow scheduling and invocation."""

import enum
from abc import ABC, abstractmethod


class TriggerType(str, enum.Enum):
    CRON = "CRON"
    EVENT = "EVENT"
    MANUAL = "MANUAL"
    WEBHOOK = "WEBHOOK"
    SCHEDULED = "SCHEDULED"


class BaseTrigger(ABC):
    """Abstract interface for workflow invocation triggers."""

    @property
    @abstractmethod
    def trigger_type(self) -> TriggerType:
        pass


class CronTrigger(BaseTrigger):
    def __init__(self, cron_expression: str):
        self.cron_expression = cron_expression

    @property
    def trigger_type(self) -> TriggerType:
        return TriggerType.CRON


class EventTrigger(BaseTrigger):
    def __init__(self, event_name: str):
        self.event_name = event_name

    @property
    def trigger_type(self) -> TriggerType:
        return TriggerType.EVENT


class ManualTrigger(BaseTrigger):
    def __init__(self, user_id: str):
        self.user_id = user_id

    @property
    def trigger_type(self) -> TriggerType:
        return TriggerType.MANUAL


class WebhookTrigger(BaseTrigger):
    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url

    @property
    def trigger_type(self) -> TriggerType:
        return TriggerType.WEBHOOK


class ScheduledTrigger(BaseTrigger):
    def __init__(self, run_at_timestamp: str):
        self.run_at_timestamp = run_at_timestamp

    @property
    def trigger_type(self) -> TriggerType:
        return TriggerType.SCHEDULED
