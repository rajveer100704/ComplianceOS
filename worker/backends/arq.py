import logging
from typing import Optional, Dict, Any
from worker.backends.base import QueueBackend

logger = logging.getLogger("arq_queue_backend")

try:
    import arq
    from arq.connections import RedisSettings, create_pool
    from arq.jobs import Job
    ARQ_AVAILABLE = True
except ImportError:
    ARQ_AVAILABLE = False

class ARQBackend(QueueBackend):
    """Redis-backed queue driver implementation using arq."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        if not ARQ_AVAILABLE:
            raise ImportError("arq library is not installed. Please install it to use ARQBackend.")
        self.redis_url = redis_url
        self.redis_settings = RedisSettings.from_dsn(redis_url)
        self.pool = None

    async def _get_pool(self):
        if not self.pool:
            self.pool = await create_pool(self.redis_settings)
        return self.pool

    async def enqueue(self, job_id: str, task_name: str, *args, **kwargs) -> str:
        pool = await self._get_pool()
        await pool.enqueue_job(task_name, *args, _job_id=job_id, **kwargs)
        return job_id

    async def cancel(self, job_id: str) -> bool:
        pool = await self._get_pool()
        await pool.setex(f"cancel:{job_id}", 86400, "1")
        try:
            job = Job(job_id, pool)
            await job.abort()
            return True
        except Exception:
            return True

    async def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        pool = await self._get_pool()
        job = Job(job_id, pool)
        try:
            status_val = await job.status()
            status_map = {
                "queued": "QUEUED",
                "in_progress": "RUNNING",
                "deferred": "RETRYING",
                "complete": "COMPLETED",
                "not_found": "FAILED"
            }
            mapped_status = status_map.get(status_val.value if hasattr(status_val, "value") else str(status_val), "QUEUED")
            
            is_cancelled = await pool.get(f"cancel:{job_id}")
            if is_cancelled:
                mapped_status = "CANCELLED"

            info = await job.info()
            return {
                "job_id": job_id,
                "status": mapped_status,
                "result": info.result if info else None,
                "error": info.error if info else None
            }
        except Exception:
            return None

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()
            self.pool = None
