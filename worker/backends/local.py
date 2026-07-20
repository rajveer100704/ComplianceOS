import asyncio
import logging
from typing import Optional, Dict, Any
from worker.backends.base import QueueBackend

logger = logging.getLogger("local_queue_backend")

class LocalQueueBackend(QueueBackend):
    """In-memory thread-safe fallback task runner using asyncio.Queue."""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.jobs = {}
        self._runner_task = None
        self._registry = {}

    def register_task(self, name: str, func):
        self._registry[name] = func

    def start(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        if not self._runner_task or self._runner_task.done():
            self._runner_task = loop.create_task(self._loop())

    async def _loop(self):
        while True:
            try:
                job_id, task_name, args, kwargs = await self.queue.get()
                if job_id not in self.jobs or self.jobs[job_id]["status"] == "CANCELLED":
                    self.queue.task_done()
                    continue
                
                self.jobs[job_id]["status"] = "RUNNING"
                
                # Resolve task function
                func = self._registry.get(task_name)
                if not func:
                    # Fallback dynamic import from worker.tasks
                    try:
                        import worker.tasks as t
                        func = getattr(t, task_name, None)
                    except Exception:
                        pass

                if not func:
                    logger.error(f"Task {task_name} not found in registry or worker.tasks")
                    self.jobs[job_id]["status"] = "FAILED"
                    self.jobs[job_id]["error"] = f"Task {task_name} not found"
                    self.queue.task_done()
                    continue

                try:
                    if asyncio.iscoroutinefunction(func):
                        res = await func(*args, **kwargs)
                    else:
                        res = func(*args, **kwargs)
                    self.jobs[job_id]["status"] = "COMPLETED"
                    self.jobs[job_id]["result"] = res
                except Exception as e:
                    logger.exception(f"Error running local task {task_name}")
                    self.jobs[job_id]["status"] = "FAILED"
                    self.jobs[job_id]["error"] = str(e)
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in local queue processing loop")

    async def enqueue(self, job_id: str, task_name: str, *args, **kwargs) -> str:
        self.start()
        self.jobs[job_id] = {
            "job_id": job_id,
            "task_name": task_name,
            "status": "QUEUED",
            "result": None,
            "error": None
        }
        await self.queue.put((job_id, task_name, args, kwargs))
        return job_id

    async def cancel(self, job_id: str) -> bool:
        if job_id in self.jobs and self.jobs[job_id]["status"] == "QUEUED":
            self.jobs[job_id]["status"] = "CANCELLED"
            return True
        return False

    async def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self.jobs.get(job_id)

    async def close(self) -> None:
        if self._runner_task:
            self._runner_task.cancel()
            try:
                await self._runner_task
            except asyncio.CancelledError:
                pass
