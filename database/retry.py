import asyncio
import logging

logger = logging.getLogger("database_retry")

async def retry_async(func, retries: int = 5, backoff_seconds: float = 1.0, *args, **kwargs):
    """Retries an asynchronous database invocation with exponential backoff."""
    for attempt in range(1, retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == retries:
                logger.error(f"Permanent connection failure after {retries} attempts: {e}")
                raise e
            sleep_time = backoff_seconds * (2 ** (attempt - 1))
            logger.warning(f"Database connection failed (attempt {attempt}/{retries}): {e}. Retrying in {sleep_time:.2f}s...")
            await asyncio.sleep(sleep_time)
