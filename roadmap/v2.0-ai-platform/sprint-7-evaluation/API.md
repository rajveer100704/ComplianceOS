# Benchmark Suite & Evaluation — API Specification

## `EvaluationManager` Interface Methods

```python
async def load_benchmark_dataset(dataset_id: str, test_cases: List[BenchmarkTestCase]) -> str:
    ...

async def run_evaluation_sweep(
    dataset_id: str, organization_id: str = "default"
) -> EvaluationRun:
    ...

async def compare_runs(baseline_run_id: str, current_run_id: str) -> RegressionReport:
    ...

async def get_evaluation_history(organization_id: str = "default") -> List[EvaluationRun]:
    ...
```
