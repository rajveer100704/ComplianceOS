import numpy as np
from typing import List, Dict


class LatencyPercentiles:
    """Calculates statistical latency percentiles for observability reports."""

    @staticmethod
    def calculate(latencies: List[float]) -> Dict[str, float]:
        """Returns p50, p90, p95, p99 and average for a list of latencies in ms."""
        if not latencies:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0}

        return {
            "p50": round(float(np.percentile(latencies, 50)), 2),
            "p90": round(float(np.percentile(latencies, 90)), 2),
            "p95": round(float(np.percentile(latencies, 95)), 2),
            "p99": round(float(np.percentile(latencies, 99)), 2),
            "avg": round(float(np.mean(latencies)), 2),
        }
