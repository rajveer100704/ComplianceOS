from retrieval.config.schema import (
    ALLOWED_CHUNKERS, ALLOWED_EMBEDDINGS, ALLOWED_STORES,
    ALLOWED_RETRIEVERS, ALLOWED_RERANKERS, ALLOWED_STRATEGIES, ALLOWED_POLICIES
)

class ConfigValidator:
    """Validator enforcing configurations align with the allowed schemas."""

    @staticmethod
    def validate(config: dict) -> None:
        ret = config.get("retrieval", {})
        if not ret:
            return  # Default fallback handling will kick in

        chunker = ret.get("chunker", {}).get("engine", "section")
        if chunker not in ALLOWED_CHUNKERS:
            raise ValueError(f"Invalid chunker engine configuration: {chunker}")

        embedding = ret.get("embedding", {}).get("engine", "tfidf")
        if embedding not in ALLOWED_EMBEDDINGS:
            raise ValueError(f"Invalid embedding engine configuration: {embedding}")

        store = ret.get("vector_store", {}).get("engine", "local")
        if store not in ALLOWED_STORES:
            raise ValueError(f"Invalid vector store engine configuration: {store}")

        retriever = ret.get("retriever", {}).get("engine", "hybrid")
        if retriever not in ALLOWED_RETRIEVERS:
            raise ValueError(f"Invalid retriever engine configuration: {retriever}")

        strategy = ret.get("retriever", {}).get("strategy", "parallel")
        if strategy not in ALLOWED_STRATEGIES:
            raise ValueError(f"Invalid retrieval strategy configuration: {strategy}")

        policy = ret.get("retriever", {}).get("policy", "balanced")
        if policy not in ALLOWED_POLICIES:
            raise ValueError(f"Invalid retrieval policy configuration: {policy}")

        reranker = ret.get("reranker", {}).get("engine", "cosine")
        if reranker not in ALLOWED_RERANKERS:
            raise ValueError(f"Invalid reranker engine configuration: {reranker}")
