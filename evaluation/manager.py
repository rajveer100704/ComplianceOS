"""Centralized EvaluationManager facade emitting PlatformEvent streams upon benchmark run completion."""

import logging
from typing import Dict, List, Optional
from evaluation.schemas import BenchmarkTestCase, EvaluationRun, RegressionReport
from evaluation.runners.runner import PlatformRunner
from evaluation.telemetry.prof import RegressionReporter
from events.bus import EventBus
from events.schemas import PlatformEvent, EventCategory

logger = logging.getLogger("evaluation.manager")


class EvaluationManager:
    """Centralized facade for regulatory benchmarks, evaluation runs, regression sweeps, and EventBus telemetry."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.runner = PlatformRunner()
        self.reporter = RegressionReporter()
        self.event_bus = event_bus
        self._datasets: Dict[str, List[BenchmarkTestCase]] = (
            {}
        )  # dataset_id -> List[BenchmarkTestCase]
        self._runs: Dict[str, EvaluationRun] = {}  # run_id -> EvaluationRun

    async def load_benchmark_dataset(
        self,
        dataset_id: str,
        test_cases: List[BenchmarkTestCase],
        organization_id: str = "default",
    ) -> str:
        self._datasets[dataset_id] = test_cases
        logger.info(
            f"Loaded benchmark dataset '{dataset_id}' with {len(test_cases)} case(s)"
        )
        return dataset_id

    async def run_evaluation_sweep(
        self, dataset_id: str, organization_id: str = "default"
    ) -> EvaluationRun:
        cases = self._datasets.get(dataset_id, [])
        run = await self.runner.execute_suite(dataset_id, cases, organization_id)
        self._runs[run.run_id] = run

        # Publish EVALUATION_COMPLETED PlatformEvent onto EventBus for Governance observation
        if self.event_bus:
            evt = PlatformEvent(
                event_id=run.run_id,
                event_type="EVALUATION_COMPLETED",
                category=EventCategory.SYSTEM,
                organization_id=organization_id,
                actor_id="EvaluationManager",
                target_id=dataset_id,
                payload={
                    "total_cases": run.total_cases_evaluated,
                    "recall_at_5": run.recall_at_5,
                    "mrr": run.mrr,
                    "mean_grounding_score": run.mean_grounding_score,
                    "mean_latency_ms": run.mean_latency_ms,
                },
            )
            await self.event_bus.publish(evt)

        return run

    async def compare_runs(
        self, baseline_run_id: str, current_run_id: str
    ) -> Optional[RegressionReport]:
        baseline = self._runs.get(baseline_run_id)
        current = self._runs.get(current_run_id)
        if not baseline or not current:
            logger.error(
                f"Cannot compare runs: baseline='{baseline_run_id}' current='{current_run_id}'"
            )
            return None

        return self.reporter.compare_runs(baseline, current)

    async def get_evaluation_history(
        self, organization_id: str = "default"
    ) -> List[EvaluationRun]:
        return [r for r in self._runs.values() if r.organization_id == organization_id]
