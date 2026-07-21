class RetrievalHealthCheck:
    """Performs system diagnostic queries validating subsystem availability."""

    @staticmethod
    def check_health(embedding, store, reranker) -> dict:
        status = "healthy"
        details = {}

        try:
            # Check embedding
            details["embedding"] = {
                "status": "online",
                "version": embedding.version,
                "dimensions": embedding.capabilities.dimensions,
            }
        except Exception as e:
            status = "unhealthy"
            details["embedding"] = {"status": "offline", "error": str(e)}

        try:
            # Check store
            if hasattr(store, "collection_manager"):
                col_health = store.collection_manager.get_health_status()
                details["store"] = {
                    "status": col_health["status"],
                    "engine": "qdrant",
                    "collection": store.collection_name,
                    "info": col_health,
                }
                if col_health["status"] != "healthy":
                    status = "unhealthy"
            else:
                details["store"] = {"status": "online", "engine": "local"}
        except Exception as e:
            status = "unhealthy"
            details["store"] = {"status": "offline", "error": str(e)}

        try:
            details["reranker"] = {
                "status": "online" if reranker else "disabled",
                "model_name": (
                    getattr(reranker, "model_name", "unknown") if reranker else None
                ),
            }
        except Exception as e:
            details["reranker"] = {"status": "error", "error": str(e)}

        return {"status": status, "details": details}
