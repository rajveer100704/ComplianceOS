CHUNKER_REGISTRY = {}
EMBEDDING_REGISTRY = {}
VECTOR_STORE_REGISTRY = {}
RETRIEVER_REGISTRY = {}
RERANKER_REGISTRY = {}

def register_chunker(name: str):
    def decorator(cls):
        CHUNKER_REGISTRY[name] = cls
        return cls
    return decorator

def register_embedding(name: str):
    def decorator(cls):
        EMBEDDING_REGISTRY[name] = cls
        return cls
    return decorator

def register_vector_store(name: str):
    def decorator(cls):
        VECTOR_STORE_REGISTRY[name] = cls
        return cls
    return decorator

def register_retriever(name: str):
    def decorator(cls):
        RETRIEVER_REGISTRY[name] = cls
        return cls
    return decorator

def register_reranker(name: str):
    def decorator(cls):
        RERANKER_REGISTRY[name] = cls
        return cls
    return decorator
