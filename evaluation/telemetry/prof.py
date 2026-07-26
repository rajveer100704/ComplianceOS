"""Regression reporter comparing current evaluation runs against baseline sweeps."""

import logging
from evaluation.schemas import EvaluationRun, RegressionReport

logger = logging.getLogger("evaluation.telemetry.prof")


class RegressionReporter:
    """Generates quantitative delta comparisons between baseline and current evaluation runs."""

    @staticmethod
    def compare_runs(
        baseline: EvaluationRun, current: EvaluationRun
    ) -> RegressionReport:
        delta_r5 = round(current.recall_at_5 - baseline.recall_at_5, 4)
        delta_mrr = round(current.mrr - baseline.mrr, 4)
        delta_grounding = round(
            current.mean_grounding_score - baseline.mean_grounding_score, 4
        )
        delta_latency = round(current.mean_latency_ms - baseline.mean_latency_ms, 2)

        # Flag regression if recall or grounding drops by more than 5% (0.05)
        is_regression = (delta_r5 < -0.05) or (delta_grounding < -0.05)

        report = RegressionReport(
            organization_id=current.organization_id,
            baseline_run_id=baseline.run_id,
            current_run_id=current.run_id,
            is_regression=is_regression,
            delta_recall_at_5=delta_r5,
            delta_mrr=delta_mrr,
            delta_grounding_score=delta_grounding,
            delta_latency_ms=delta_latency,
        )
        if is_regression:
            logger.warning(
                f"Performance regression detected in run '{current.run_id}': delta_recall={delta_r5} delta_grounding={delta_grounding}"
            )
        else:
            logger.info(
                f"Evaluation comparison passed for run '{current.run_id}' delta_recall={delta_r5}"
            )
        return report
