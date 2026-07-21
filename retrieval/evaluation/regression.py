import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("regression_gates")


class RegressionGates:
    """Enforces CI quality and latency gates comparing current runs against historical baselines."""

    @staticmethod
    def verify(current_report: dict, baseline_run: dict) -> Tuple[bool, list, list]:
        """Compares current vs baseline metrics. Returns (passed, failures, warnings)."""
        failures = []
        warnings = []

        if not baseline_run or "report" not in baseline_run:
            logger.info("No historical baseline run found. Skipping regression checks.")
            return True, [], []

        baseline_report = baseline_run["report"]

        # 1. Fetch overall stats for comparison
        # We compare the standard 'hybrid_reranked' pipeline
        curr_m = (
            current_report.get("pipelines", {})
            .get("hybrid_reranked", {})
            .get("overall", {})
        )
        base_m = (
            baseline_report.get("pipelines", {})
            .get("hybrid_reranked", {})
            .get("overall", {})
        )

        if not curr_m or not base_m:
            # Fallback to direct keys for backward compatibility
            curr_m = current_report.get("hybrid_reranked", {})
            base_m = baseline_report.get("hybrid_reranked", {})

        if not curr_m or not base_m:
            logger.warning(
                "Could not resolve hybrid_reranked metrics for regression checks."
            )
            return True, [], []

        curr_recall = curr_m.get("recall@10", 0.0)
        base_recall = base_m.get("recall@10", 0.0)

        curr_mrr = curr_m.get("mrr", 0.0)
        base_mrr = base_m.get("mrr", 0.0)

        curr_lat = curr_m.get("latency_ms", 0.0)
        base_lat = base_m.get("latency_ms", 0.0)

        # 2. Check Recall (max drop 1%)
        if base_recall > 0:
            recall_change_pct = ((curr_recall - base_recall) / base_recall) * 100
            if recall_change_pct < -1.0:
                failures.append(
                    f"Recall@10 dropped by {abs(recall_change_pct):.2f}% (Limit: 1.00%)"
                )

        # 3. Check MRR (max drop 2%)
        if base_mrr > 0:
            mrr_change_pct = ((curr_mrr - base_mrr) / base_mrr) * 100
            if mrr_change_pct < -2.0:
                failures.append(
                    f"MRR dropped by {abs(mrr_change_pct):.2f}% (Limit: 2.00%)"
                )

        # 4. Check Latency (hard limit 10% increase, warning 5% increase)
        if base_lat > 0:
            latency_change_pct = ((curr_lat - base_lat) / base_lat) * 100
            if latency_change_pct > 10.0:
                failures.append(
                    f"Latency increased by {latency_change_pct:.2f}% (Limit: 10.00%)"
                )
            elif latency_change_pct > 5.0:
                warnings.append(
                    f"Latency increased by {latency_change_pct:.2f}% (Warning Limit: 5.00%)"
                )

        passed = len(failures) == 0
        return passed, failures, warnings
