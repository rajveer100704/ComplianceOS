class RetrievalValidationMiddleware:
    """Interceptor validating query arguments for constraints before parsing."""

    @staticmethod
    def validate_query(query: str, limit: int) -> None:
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty")
        if limit <= 0:
            raise ValueError(
                f"Retrieval limit must be a positive integer, got: {limit}"
            )
