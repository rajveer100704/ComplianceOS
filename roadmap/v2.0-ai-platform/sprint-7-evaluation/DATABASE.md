# Benchmark Suite & Evaluation — Database Schema & Data Models

## Relational Schema Definitions

### `benchmark_test_cases` Table
- `case_id` (UUID, Primary Key)
- `dataset_id` (String, Indexed) — e.g. `faa-part-450`, `nrc-10-cfr`
- `organization_id` (String, Indexed)
- `query_text` (Text)
- `expected_document_ids` (JSONB)
- `expected_claims` (JSONB)
- `created_at` (Timestamp UTC)

### `evaluation_runs` Table
- `run_id` (UUID, Primary Key)
- `dataset_id` (String, Foreign Key)
- `organization_id` (String, Indexed)
- `total_cases_evaluated` (Integer)
- `recall_at_5` (Float)
- `mrr` (Float)
- `mean_grounding_score` (Float)
- `mean_latency_ms` (Float)
- `created_at` (Timestamp UTC)

### `regression_reports` Table
- `report_id` (UUID, Primary Key)
- `organization_id` (String, Indexed)
- `baseline_run_id` (UUID, Foreign Key)
- `current_run_id` (UUID, Foreign Key)
- `is_regression` (Boolean)
- `delta_metrics` (JSONB)
- `created_at` (Timestamp UTC)
