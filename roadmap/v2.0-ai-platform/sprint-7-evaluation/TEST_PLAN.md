# Benchmark Suite & Evaluation — Test Plan

## Test Strategy

1. **Unit Tests (`tests/evaluation/test_evaluation.py`)**: Validate Recall@K, MRR, Grounding Score calculations, and dataset loaders.
2. **EventBus Telemetry Tests**: Verify that completing an evaluation run publishes `EVALUATION_COMPLETED` `PlatformEvent` onto `EventBus`.
3. **Regression Sweep Tests**: Verify `compare_runs()` correctly flags metric drops exceeding 5%.
