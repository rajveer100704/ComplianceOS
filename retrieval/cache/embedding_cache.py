import sqlite3
import json
import hashlib
from pathlib import Path
import logging

logger = logging.getLogger("embedding_cache")


class EmbeddingCache:
    """Persistent SQLite-backed cache for computed dense vectors with automatic version invalidation."""

    def __init__(self, cache_path: str = None):
        if cache_path is None:
            cache_path = str(
                Path(__file__).parent.parent.parent / "storage" / "embeddings_cache.db"
            )

        Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        self.cache_path = cache_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    chunk_hash TEXT,
                    model_name TEXT,
                    model_version TEXT,
                    dimension INTEGER,
                    embedding TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (chunk_hash, model_name, model_version)
                )
            """)
            conn.commit()

    @staticmethod
    def _compute_hash(text: str) -> str:
        """Computes SHA-256 hash of text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str, model_name: str, model_version: str) -> list[float] | None:
        """Retrieves cached embedding if model name and version match exactly."""
        chunk_hash = self._compute_hash(text)
        try:
            with sqlite3.connect(self.cache_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT embedding FROM embedding_cache WHERE chunk_hash = ? AND model_name = ? AND model_version = ?",
                    (chunk_hash, model_name, model_version),
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
        except Exception as e:
            logger.error(f"Error reading embedding cache: {e}")
        return None

    def set(
        self,
        text: str,
        model_name: str,
        model_version: str,
        dimension: int,
        embedding: list[float],
    ):
        """Persists embedding vector with model and dimension metadata."""
        chunk_hash = self._compute_hash(text)
        try:
            with sqlite3.connect(self.cache_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO embedding_cache (chunk_hash, model_name, model_version, dimension, embedding)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_hash,
                        model_name,
                        model_version,
                        dimension,
                        json.dumps(embedding),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error writing embedding cache: {e}")

    def prune_stale(self, current_model_name: str, current_model_version: str):
        """Purges cached vectors computed using older/other model configurations to prevent bloat."""
        try:
            with sqlite3.connect(self.cache_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM embedding_cache WHERE model_name != ? OR model_version != ?",
                    (current_model_name, current_model_version),
                )
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(
                        f"Pruned {cursor.rowcount} stale embeddings from cache."
                    )
        except Exception as e:
            logger.error(f"Error pruning embedding cache: {e}")
