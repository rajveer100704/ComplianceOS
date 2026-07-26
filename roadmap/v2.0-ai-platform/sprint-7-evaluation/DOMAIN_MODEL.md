# Benchmark Suite & Evaluation — Domain Model Reference

## Domain Taxonomy & Entity Relationships

```
EvaluationManager
    │
    ├── Benchmark Dataset Loader (BenchmarkTestCase, Ground Truths)
    ├── Metric Engine (Recall@K, MRR, Grounding Score, Hallucination Risk, Latency)
    ├── Platform Runner (Full pipeline execution across Sprints 1–6)
    ├── Regression Report Generator (Baseline vs Current Run Delta)
    └── PlatformEvent Emitter (Publishes EVALUATION_COMPLETED to EventBus)
```

### Key Models

1. **`BenchmarkTestCase`**: Standardized evaluation input with query text and expected ground truth document IDs.
2. **`EvaluationRun`**: Aggregated evaluation result containing Recall@K, MRR, Mean Grounding Score, and Latency.
3. **`RegressionReport`**: Quantitative comparison between baseline and current evaluation runs detecting quality drift.
