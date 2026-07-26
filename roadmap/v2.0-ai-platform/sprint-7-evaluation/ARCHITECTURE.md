# Benchmark Suite & Evaluation Engine — Architecture Blueprint

```mermaid
graph TD
    EvalManager[EvaluationManager Facade] --> BenchmarkLoader[Benchmark Dataset Loader]
    EvalManager --> PlatformRunner[Platform Pipeline Runner]

    subgraph EvaluationEngine [evaluation/ Subsystem]
        PlatformRunner --> MetricEngine[Metric Evaluators]
        MetricEngine --> RecallEvaluator[Recall@K & MRR]
        MetricEngine --> GroundingEvaluator[Grounding & Hallucination Risk]
        MetricEngine --> LatencyEvaluator[Latency Telemetry]
    end

    EvalManager -->|PlatformEvent| EventBus[events/ EventBus]
    EventBus -->|Subscribe| GovManager[Sprint 6 GovernanceManager]
```

---

## Evaluation Sweep Sequence Flow

```mermaid
sequenceDiagram
    autonumber
    actor Engineer as QA Engineer
    participant Mgr as EvaluationManager
    participant Runner as PlatformRunner
    participant Bus as EventBus
    participant Gov as GovernanceManager

    Engineer->>Mgr: run_evaluation_sweep(dataset_id="faa-part-450")
    Mgr->>Runner: execute_benchmark_suite(cases)
    Runner-->>Mgr: EvaluationRun (recall_at_5=0.92, grounding_score=0.89)
    Mgr->>Bus: publish(PlatformEvent: EVALUATION_COMPLETED)
    Bus->>Gov: handle_platform_event()
    Gov-->>Gov: Record AuditLedgerEntry (seq=N)
    Mgr-->>Engineer: Evaluation Summary & Regression Report
```
