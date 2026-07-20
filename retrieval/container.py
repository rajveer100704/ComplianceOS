from retrieval.factory import RetrievalFactory
from retrieval.config.loader import ConfigLoader
from retrieval.services.retrieval_service import RetrievalService
from retrieval.services.indexing_service import IndexingService
from retrieval.services.lifecycle_manager import LifecycleManager
from retrieval.pipeline.planner import QueryPlanner

# Persistence imports
from database.session import engine, async_session_factory
from database.services.persistence_service import PersistenceService
from database.services.unit_of_work import UnitOfWork

class Container:
    """Dependency Injection container assembling service abstractions from config."""
    
    _config = None
    _retrieval_service = None
    _indexing_service = None
    _lifecycle_manager = None
    _persistence_service = None
    _queue_backend = None
    
    @classmethod
    def initialize(cls):
        import logging
        logger = logging.getLogger("container")

        cls._config = ConfigLoader.load()
        ret_conf = cls._config.get("retrieval", {})

        # 1. Resolve chunker
        chunker = RetrievalFactory.get_chunker(ret_conf.get("chunker", {}).get("engine", "section"))

        # 2. Resolve embedding
        emb_conf = ret_conf.get("embedding", {})
        emb_engine = emb_conf.get("engine", "tfidf")
        allow_emb_fallback = emb_conf.get("allow_fallback", True)

        try:
            embedding = RetrievalFactory.get_embedding(
                emb_engine,
                model_name=emb_conf.get("model_name", "BAAI/bge-small-en-v1.5"),
                device=emb_conf.get("device", "auto"),
                warmup=emb_conf.get("warmup", True)
            )
        except Exception as e:
            if not allow_emb_fallback:
                raise
            logger.warning(f"Failed to load embedding engine '{emb_engine}': {e}. Falling back to TF-IDF.")
            embedding = RetrievalFactory.get_embedding("tfidf", dimension=512)

        # 3. Resolve cache
        cache = None
        cache_conf = ret_conf.get("cache", {})
        if cache_conf.get("enabled", True):
            from retrieval.cache.embedding_cache import EmbeddingCache
            cache = EmbeddingCache()
            # Prune stale cache entries
            model_name = getattr(embedding, "model_name", "tfidf")
            model_version = embedding.version
            cache.prune_stale(model_name, model_version)

        # 4. Resolve vector store
        store_conf = ret_conf.get("vector_store", {})
        store_engine = store_conf.get("engine", "local")
        qdrant_conf = store_conf.get("qdrant", {})
        allow_store_fallback = qdrant_conf.get("allow_fallback", True)

        try:
            if store_engine == "qdrant":
                store = RetrievalFactory.get_vector_store(
                    "qdrant",
                    url=qdrant_conf.get("url", "http://localhost:6333"),
                    collection=qdrant_conf.get("collection", "compliance_chunks"),
                    vector_name=qdrant_conf.get("vector_name", "dense"),
                    timeout=qdrant_conf.get("timeout", 5.0)
                )
                dim = embedding.capabilities.dimensions
                store.collection_manager.verify_or_create_collection(dimension=dim)
            else:
                store = RetrievalFactory.get_vector_store("local")
        except Exception as e:
            if not allow_store_fallback:
                raise
            logger.warning(f"Failed to load vector store engine '{store_engine}': {e}. Falling back to memory LocalVectorStore.")
            store = RetrievalFactory.get_vector_store("local")

        # 5. Resolve planner
        planner = QueryPlanner(
            engine=ret_conf.get("retriever", {}).get("engine", "hybrid"),
            strategy=ret_conf.get("retriever", {}).get("strategy", "parallel"),
            policy=ret_conf.get("retriever", {}).get("policy", "balanced")
        )

        # 6. Resolve reranker
        reranker = None
        if ret_conf.get("reranker", {}).get("enabled", True):
            rr_conf = ret_conf.get("reranker", {})
            rr_engine = rr_conf.get("engine", "cosine")
            allow_rr_fallback = rr_conf.get("allow_fallback", True)
            try:
                reranker = RetrievalFactory.get_reranker(
                    rr_engine,
                    model_name=rr_conf.get("model_name", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
                    device=rr_conf.get("device", "auto"),
                    warmup=rr_conf.get("warmup", True)
                )
            except Exception as e:
                if not allow_rr_fallback:
                    raise
                logger.warning(f"Failed to load reranker engine '{rr_engine}': {e}. Falling back to CosineReranker.")
                reranker = RetrievalFactory.get_reranker("cosine", embedding_provider=embedding)

        # Dependency Injection wiring
        cls._indexing_service = IndexingService(chunker, embedding, store, cache=cache)
        cls._retrieval_service = RetrievalService(embedding, store, planner, reranker, cache=cache)
        cls._lifecycle_manager = LifecycleManager(store)
        cls._persistence_service = PersistenceService()

        # Resolve QueueBackend
        redis_conf = cls._config.get("redis", {})
        worker_conf = cls._config.get("worker", {})
        engine_type = worker_conf.get("engine", "arq")
        redis_url = redis_conf.get("url", "redis://localhost:6379/0")
        allow_fallback = redis_conf.get("allow_fallback", True)

        if engine_type == "arq":
            import socket
            from urllib.parse import urlparse
            try:
                url = urlparse(redis_url)
                host = url.hostname or "localhost"
                port = url.port or 6379
                with socket.create_connection((host, port), timeout=1.0):
                    pass
                from worker.backends.arq import ARQBackend
                cls._queue_backend = ARQBackend(redis_url)
            except Exception:
                if not allow_fallback:
                    raise
                from worker.backends.local import LocalQueueBackend
                cls._queue_backend = LocalQueueBackend()
        else:
            from worker.backends.local import LocalQueueBackend
            cls._queue_backend = LocalQueueBackend()

    @classmethod
    def get_retrieval_service(cls) -> RetrievalService:
        if cls._retrieval_service is None:
            cls.initialize()
        return cls._retrieval_service

    @classmethod
    def get_indexing_service(cls) -> IndexingService:
        if cls._indexing_service is None:
            cls.initialize()
        return cls._indexing_service

    @classmethod
    def get_lifecycle_manager(cls) -> LifecycleManager:
        if cls._lifecycle_manager is None:
            cls.initialize()
        return cls._lifecycle_manager

    @classmethod
    def get_db_engine(cls):
        """Returns the configured database engine."""
        return engine

    @classmethod
    def get_session_factory(cls):
        """Returns the configured sessionmaker factory."""
        return async_session_factory

    @classmethod
    def get_unit_of_work(cls) -> UnitOfWork:
        """Returns a new request-scoped UnitOfWork context manager."""
        return UnitOfWork()

    @classmethod
    def get_persistence_service(cls) -> PersistenceService:
        """Returns the singleton PersistenceService instance."""
        if cls._persistence_service is None:
            cls.initialize()
        return cls._persistence_service

    @classmethod
    def get_queue_backend(cls):
        """Returns the configured QueueBackend instance."""
        if cls._queue_backend is None:
            cls.initialize()
        return cls._queue_backend

    @classmethod
    def reset(cls):
        """Clears singletons for testing or config reloads."""
        cls._config = None
        cls._retrieval_service = None
        cls._indexing_service = None
        cls._lifecycle_manager = None
        cls._persistence_service = None
        cls._queue_backend = None
