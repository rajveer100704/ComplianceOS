from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class QueueBackend(ABC):
    """Abstract interface defining the requirements for background processing queue backends."""

    @abstractmethod
    async def enqueue(self, job_id: str, task_name: str, *args, **kwargs) -> str:
        """Enqueues a background task with a specific unique job identifier."""
        pass

    @abstractmethod
    async def cancel(self, job_id: str) -> bool:
        """Attempts to cancel a scheduled or running background job."""
        pass

    @abstractmethod
    async def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Queries the current status and metadata of a background job."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Cleanly releases any connection pools or resources."""
        pass
