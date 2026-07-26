# Benchmark Suite & Evaluation — Implementation Guide

## Ordered Development Phases

1. **Phase A (Core Domain Models & Schemas)**:
   - `evaluation/schemas.py` — `BenchmarkTestCase`, `EvaluationRun`, `RegressionReport`.
2. **Phase B (Metric Evaluators Engine)**:
   - `evaluation/metrics/` — Recall@K, MRR, Precision, Grounding Score, and Latency Telemetry.
3. **Phase C (End-to-End Platform Evaluation Runner)**:
   - `evaluation/runners/runner.py` — Full pipeline test case execution.
4. **Phase D (Regression Sweep Generator)**:
   - `evaluation/telemetry/prof.py` — Baseline vs current run regression reporter.
5. **Phase E (Centralized Facade & EventBus Emitter)**:
   - `evaluation/manager.py` — `EvaluationManager` publishing `PlatformEvent` (`category=SYSTEM`) to `EventBus`.
