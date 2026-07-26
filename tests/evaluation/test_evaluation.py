"""Unit & integration tests for Benchmark Suite & Evaluation Engine (Sprint 7)."""

import pytest
from events import EventBus
from governance import GovernanceManager
from evaluation import (
    EvaluationManager,
    BenchmarkTestCase,
    MetricEvaluator,
)


@pytest.mark.asyncio
async def test_evaluation_metric_evaluator_calculations():
    # Test Recall@K
    retrieved = ["doc-1", "doc-2", "doc-3", "doc-4", "doc-5"]
    expected = ["doc-2", "doc-5", "doc-9"]
    recall = MetricEvaluator.calculate_recall_at_k(retrieved, expected, k=5)
    assert recall == 0.6667

    # Test MRR
    mrr = MetricEvaluator.calculate_mrr(retrieved, expected)
    assert mrr == 0.5  # doc-2 found at rank 2 (1/2 = 0.5)


@pytest.mark.asyncio
async def test_evaluation_manager_sweep_and_eventbus_observation():
    bus = EventBus()
    gov = GovernanceManager(event_bus=bus)
    eval_mgr = EvaluationManager(event_bus=bus)

    # 1. Load benchmark dataset
    cases = [
        BenchmarkTestCase(
            query_text="FAA 450 public risk casualty expectancy limits",
            expected_document_ids=["doc-450-115-a", "doc-450-115-b"],
            organization_id="org-acme",
        ),
        BenchmarkTestCase(
            query_text="ASME BPVC pressure vessel thermal protection requirements",
            expected_document_ids=["doc-asme-bpvc-01"],
            organization_id="org-acme",
        ),
    ]
    await eval_mgr.load_benchmark_dataset(
        "faa-part-450", cases, organization_id="org-acme"
    )

    # 2. Run evaluation sweep -> publishes PlatformEvent (EVALUATION_COMPLETED) onto EventBus
    run = await eval_mgr.run_evaluation_sweep(
        "faa-part-450", organization_id="org-acme"
    )
    assert run.total_cases_evaluated == 2
    assert run.recall_at_5 > 0.0

    # 3. Verify Sprint 6 GovernanceManager observed evaluation completion automatically
    audit_entries = await gov.get_audit_trail("org-acme")
    assert len(audit_entries) >= 1
    assert audit_entries[-1].event_type == "EVALUATION_COMPLETED"


@pytest.mark.asyncio
async def test_evaluation_regression_sweep_comparison():
    eval_mgr = EvaluationManager()

    cases = [
        BenchmarkTestCase(
            query_text="FAA Part 450 launch safety analysis",
            expected_document_ids=["doc-101"],
            organization_id="org-acme",
        )
    ]
    await eval_mgr.load_benchmark_dataset(
        "dataset-01", cases, organization_id="org-acme"
    )

    # Baseline run
    run_baseline = await eval_mgr.run_evaluation_sweep(
        "dataset-01", organization_id="org-acme"
    )

    # Current run
    run_current = await eval_mgr.run_evaluation_sweep(
        "dataset-01", organization_id="org-acme"
    )

    # Compare
    report = await eval_mgr.compare_runs(run_baseline.run_id, run_current.run_id)
    assert report is not None
    assert report.is_regression is False
