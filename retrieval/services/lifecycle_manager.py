from pathlib import Path
from retrieval.base import BaseVectorStore
from retrieval.indexing.manifest import IndexManifest

class LifecycleManager:
    """Manages index initializations, resets, and manifests."""

    def __init__(self, vector_store: BaseVectorStore):
        self.vector_store = vector_store

    def reset_index(self) -> None:
        """Clears all indices and cached vectors."""
        self.vector_store.clear()

    def generate_manifest(self, version: str, embedding_engine: str, dimension: int, chunk_count: int, doc_count: int) -> None:
        """Saves current index footprint stats to manifest JSON file."""
        manifest_dir = Path(__file__).parent.parent.parent / "storage" / "indexes"
        IndexManifest.save_manifest(manifest_dir, version, embedding_engine, dimension, chunk_count, doc_count)
