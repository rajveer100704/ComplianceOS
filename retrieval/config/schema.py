# Allowed config values for validation checks
ALLOWED_CHUNKERS = {"paragraph", "section", "semantic"}
ALLOWED_EMBEDDINGS = {"tfidf", "bgem3"}
ALLOWED_STORES = {"local", "qdrant"}
ALLOWED_RETRIEVERS = {"dense", "bm25", "hybrid"}
ALLOWED_RERANKERS = {"cosine", "cross_encoder"}
ALLOWED_STRATEGIES = {"sequential", "parallel", "cascade"}
ALLOWED_POLICIES = {"strict", "balanced", "recall"}
