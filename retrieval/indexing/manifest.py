import json
from pathlib import Path
from datetime import datetime, timezone


class IndexManifest:
    """Manages index versioning details and metadata stats for reproducibility."""

    @staticmethod
    def save_manifest(
        index_dir: Path,
        version: str,
        embedding_engine: str,
        dimension: int,
        chunk_count: int,
        doc_count: int,
    ) -> None:
        manifest = {
            "index_version": version,
            "embedding": embedding_engine,
            "dimension": dimension,
            "chunks": chunk_count,
            "documents": doc_count,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        index_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = index_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    @staticmethod
    def load_manifest(index_dir: Path) -> dict:
        manifest_path = index_dir / "manifest.json"
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
