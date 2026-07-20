import math
import re
from typing import List, Tuple
from retrieval.base import BaseRetriever, BaseVectorStore
from retrieval.capabilities import RetrieverCapabilities
from retrieval.models.chunk import Chunk
from retrieval.registry import register_retriever

@register_retriever("bm25")
class BM25Retriever(BaseRetriever):
    """Executes local BM25 keyword matching over loaded document chunks."""

    def __init__(self, vector_store: BaseVectorStore, k1: float = 1.5, b: float = 0.75):
        self.vector_store = vector_store
        self.k1 = k1
        self.b = b

    @property
    def capabilities(self) -> RetrieverCapabilities:
        return RetrieverCapabilities(hybrid=False, metadata=True, filters=True)

    def retrieve(self, query: str, limit: int, filters: dict = None) -> List[Tuple[Chunk, float]]:
        # Access local memory chunks from local vector store
        if not hasattr(self.vector_store, "chunks") or not self.vector_store.chunks:
            return []

        chunks = self.vector_store.chunks
        if filters:
            filtered = []
            for c in chunks:
                mismatch = False
                for k, v in filters.items():
                    if c.metadata.get(k) != v:
                        mismatch = True
                        break
                if not mismatch:
                    filtered.append(c)
            chunks = filtered

        if not chunks:
            return []

        def tokenize(text: str) -> List[str]:
            return re.findall(r'\w+', text.lower())

        doc_tokens = [tokenize(c.text) for c in chunks]
        doc_lengths = [len(tokens) for tokens in doc_tokens]
        avg_doc_len = sum(doc_lengths) / len(chunks) if chunks else 1.0

        # Document Frequencies (DF)
        df = {}
        for tokens in doc_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1

        # Inverse Document Frequencies (IDF)
        idf = {}
        N = len(chunks)
        for token, count in df.items():
            idf[token] = math.log((N - count + 0.5) / (count + 0.5) + 1.0)

        query_tokens = tokenize(query)
        scores = []
        for i, chunk in enumerate(chunks):
            tokens = doc_tokens[i]
            doc_len = doc_lengths[i]
            tf_map = {}
            for t in tokens:
                tf_map[t] = tf_map.get(t, 0) + 1

            score = 0.0
            for qt in query_tokens:
                if qt in tf_map:
                    tf = tf_map[qt]
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avg_doc_len))
                    score += idf.get(qt, 0.0) * (numerator / denominator)
            scores.append((chunk, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:limit]
