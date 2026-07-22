import time
import json
import logging
import asyncio

logger = logging.getLogger("worker_heartbeat")


class WorkerHeartbeat:
    """Manages worker status heartbeat registration in Redis."""

    def __init__(self, worker_id: str, backend, interval_sec: int = 15):
        self.worker_id = worker_id
        self.backend = backend
        self.interval_sec = interval_sec
        self.start_time = time.time()
        self._task = None

    async def start(self):
        self._task = asyncio.create_task(self._loop())
        logger.info(f"Worker heartbeat logger started for {self.worker_id}")

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        try:
            if hasattr(self.backend, "pool") and self.backend.pool:
                await self.backend.pool.delete(f"worker:heartbeat:{self.worker_id}")
        except Exception:
            pass

    async def _loop(self):
        while True:
            try:
                uptime = time.time() - self.start_time
                info = {
                    "worker_id": self.worker_id,
                    "uptime_sec": round(uptime, 1),
                    "timestamp": time.time(),
                    "status": "ALIVE",
                }

                if hasattr(self.backend, "pool") and self.backend.pool:
                    pool = self.backend.pool
                    await pool.setex(
                        f"worker:heartbeat:{self.worker_id}",
                        self.interval_sec * 2,
                        json.dumps(info),
                    )
                else:
                    logger.debug(f"Heartbeat: {info}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
            await asyncio.sleep(self.interval_sec)
