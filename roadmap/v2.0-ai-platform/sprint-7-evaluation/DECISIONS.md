# Benchmark Suite & Evaluation — Key Design Decisions Log

## Summary of Decisions

1. **Platform-Wide Pipeline Measurement**: Evaluation measures full platform retrieval + reasoning + governance performance rather than isolated LLM text prompts.
2. **EventBus Telemetry Emitter**: `EvaluationManager` publishes `PlatformEvent` (`category=SYSTEM`) to `EventBus` allowing Sprint 6 Governance to record evaluation audit logs automatically.
3. **Delta Regression Sweeps**: `compare_runs()` evaluates delta score drops against baseline runs to flag performance regressions.
