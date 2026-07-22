import json
import time
import subprocess
from pathlib import Path
from typing import Optional


class BenchmarkHistoryManager:
    """Manages historical benchmark reports and metadata for trend analysis and regression testing."""

    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent.parent
        self.history_dir = self.workspace_root / "storage" / "benchmark_history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def get_git_commit(self) -> str:
        """Retrieves current git commit hash, returning fallback on failure."""
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                cwd=str(self.workspace_root),
            )
            return res.stdout.strip()
        except Exception:
            return "unknown-commit"

    def save_run(
        self,
        report: dict,
        embedding_model: str,
        reranker: str,
        profile: str,
        dataset_version: str,
    ) -> str:
        """Saves a benchmark run to historical storage alongside detailed system metadata."""
        timestamp = time.strftime("%Y-%m-%d_%H%M%S")
        filename = f"{timestamp}.json"
        filepath = self.history_dir / filename

        run_data = {
            "metadata": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "embedding_model": embedding_model,
                "reranker": reranker,
                "profile": profile,
                "dataset_version": dataset_version,
                "git_commit": self.get_git_commit(),
            },
            "report": report,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(run_data, f, indent=2)

        return str(filepath)

    def load_latest_run(self) -> Optional[dict]:
        """Loads and returns the most recent historical benchmark run from storage."""
        files = sorted(self.history_dir.glob("*.json"))
        if not files:
            return None

        # Load the latest file
        try:
            with open(files[-1], "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
