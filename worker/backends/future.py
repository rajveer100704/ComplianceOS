from typing import Optional, Dict, Any
from worker.backends.base import QueueBackend


class FutureTaskIQBackend(QueueBackend):
    """Placeholder for future TaskIQ or Celery integrations."""

    def __init__(self, settings: dict):
        self.settings = settings

    async def enqueue(self, job_id: str, task_name: str, *args, **kwargs) -> str:
        raise NotImplementedError(
            "FutureTaskIQBackend is a placeholder and not implemented."
        )

    async def cancel(self, job_id: str) -> bool:
        raise NotImplementedError(
            "FutureTaskIQBackend is a placeholder and not implemented."
        )

    async def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError(
            "FutureTaskIQBackend is a placeholder and not implemented."
        )

    async def close(self) -> None:
        pass
