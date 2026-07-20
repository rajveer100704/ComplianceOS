import asyncio
import logging
from typing import Tuple
from database.bootstrap import bootstrap_database
from database.health import DatabaseHealth

logger = logging.getLogger("worker_bootstrap")

async def bootstrap_worker(redis_url: str, allow_fallback: bool = True) -> Tuple[bool, str]:
    """Verifies that database connection, migration head, and Redis connection are healthy."""
    logger.info("Initializing worker bootstrap checks...")

    # 1. Database setup
    try:
        await bootstrap_database()
        db_health = await DatabaseHealth.check_health()
        if db_health["status"] != "healthy":
            return False, f"Database health check failed: {db_health.get('detail')}"
    except Exception as e:
        logger.exception("Database bootstrap check encountered an error")
        return False, f"Database bootstrap failed: {e}"

    # 2. Redis setup
    if redis_url:
        try:
            from urllib.parse import urlparse
            url = urlparse(redis_url)
            host = url.hostname or "localhost"
            port = url.port or 6379

            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=3.0
            )
            writer.close()
            await writer.wait_closed()
            logger.info("Redis connectivity check passed.")
        except Exception as e:
            logger.warning(f"Redis connectivity failed: {e}")
            if not allow_fallback:
                return False, f"Redis required but unreachable: {e}"
            logger.info("Redis offline: falling back to in-memory local fallback.")

    logger.info("Worker bootstrap check completed successfully.")
    return True, "Worker successfully bootstrapped"
