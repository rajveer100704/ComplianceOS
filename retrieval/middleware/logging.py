import logging

logger = logging.getLogger("retrieval_middleware")

class RetrievalLoggingMiddleware:
    """Logs queries and candidate matches across retrieval invocations."""
    
    @staticmethod
    def before_retrieve(query: str, filters: dict) -> None:
        logger.info(f"Retrieval operation initiated for query: '{query}' with filters: {filters}")

    @staticmethod
    def after_retrieve(query: str, results_count: int) -> None:
        logger.info(f"Retrieval operation complete for query: '{query}' - found {results_count} results")
