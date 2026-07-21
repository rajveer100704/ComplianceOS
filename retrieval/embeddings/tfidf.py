import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from retrieval.base import BaseEmbeddingProvider
from retrieval.capabilities import EmbeddingCapabilities
from retrieval.registry import register_embedding


@register_embedding("tfidf")
class TFIDFEmbeddingProvider(BaseEmbeddingProvider):
    """Provides local dense-like representations mapping standard TF-IDF vocabularies."""

    def __init__(self, dimension: int = 512, **kwargs):
        self.dimension = dimension
        self.vectorizer = TfidfVectorizer(max_features=dimension, stop_words="english")

        # Fit on regulations corpus on init
        regs_path = Path(__file__).parent.parent.parent / "regulations.json"
        if regs_path.exists():
            try:
                with open(regs_path, "r", encoding="utf-8") as f:
                    regs = json.load(f)
                texts = [r["text"] for r in regs]
                self.vectorizer.fit(texts)
            except Exception:
                self.vectorizer.fit(
                    [
                        "Compliance check safety system FAA rules",
                        "NRC reactor containment regulations",
                    ]
                )
        else:
            self.vectorizer.fit(
                [
                    "Compliance check safety system FAA rules",
                    "NRC reactor containment regulations",
                ]
            )

    @property
    def capabilities(self) -> EmbeddingCapabilities:
        return EmbeddingCapabilities(multivector=False, dimensions=self.dimension)

    @property
    def version(self) -> str:
        return "tfidf_v1"

    def embed_query(self, query: str) -> list[float]:
        vec = self.vectorizer.transform([query]).toarray()[0]
        return [float(v) for v in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vecs = self.vectorizer.transform(texts).toarray()
        return [[float(v) for v in row] for row in vecs]
