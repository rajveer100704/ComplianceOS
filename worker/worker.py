import asyncio
import logging
import signal
from typing import Dict, Any

from worker.bootstrap import bootstrap_worker
from worker.state import TaskStateManager

logger = logging.getLogger("background_worker")

class BackgroundWorker:
    """Daemon runner process executing background jobs from QueueBackend."""

    def __init__(self, backend, redis_url: str = None):
        self.backend = backend
        self.redis_url = redis_url
        self.running = False
        self.active_tasks = set()

    async def start(self):
        self.running = True
        logger.info("BackgroundWorker daemon started.")
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
            except NotImplementedError:
                # Windows fallback
                pass

    async def shutdown(self):
        logger.info("Graceful shutdown initiated. Draining active jobs...")
        self.running = False
        if self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} active tasks to finish...")
            await asyncio.gather(*self.active_tasks, return_exceptions=True)
        logger.info("BackgroundWorker daemon shut down cleanly.")

    async def run_loop(self):
        await self.start()
        while self.running:
            await asyncio.sleep(1)
