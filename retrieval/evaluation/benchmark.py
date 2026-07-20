import json
import time
from pathlib import Path
from typing import Dict, Any, List

from retrieval.evaluation.metrics import RetrievalMetrics
from retrieval.services.retrieval_service import RetrievalService
from retrieval.evaluation.query_classifier import QueryClassifier

class RetrievalBenchmarkRunner:
    """Runs retrieval quality evaluations against golden query benchmarks."""

    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = str(Path(__file__).parent.parent.parent / "tests" / "retrieval_benchmark")
        self.base_dir = Path(base_dir)
        self.queries_file = self.base_dir / "queries.json"
        self.expected_file = self.base_dir / "expected_results.json"
        self.metadata_file = self.base_dir / "metadata.json"

    def run_evaluation(self, retrieval_service: RetrievalService) -> dict:
        """Executes full evaluation pipeline comparing BM25, Dense, Hybrid (RRF), and Cross-Encoder."""
        with open(self.queries_file, "r", encoding="utf-8") as f:
            queries_list = json.load(f)
        with open(self.expected_file, "r", encoding="utf-8") as f:
            expected_map = json.load(f)

        original_dense = retrieval_service.pipeline.dense_retriever
        original_bm25 = retrieval_service.pipeline.bm25_retriever
        original_reranker = retrieval_service.pipeline.reranker

        def evaluate_config(pipeline_name: str, profile_name: str) -> dict:
            # Configure pipeline components
            if pipeline_name == "bm25":
                retrieval_service.pipeline.dense_retriever = None
                retrieval_service.pipeline.bm25_retriever = original_bm25
                retrieval_service.pipeline.reranker = None
            elif pipeline_name == "dense":
                retrieval_service.pipeline.dense_retriever = original_dense
                retrieval_service.pipeline.bm25_retriever = None
                retrieval_service.pipeline.reranker = None
            elif pipeline_name == "hybrid":
                retrieval_service.pipeline.dense_retriever = original_dense
                retrieval_service.pipeline.bm25_retriever = original_bm25
                retrieval_service.pipeline.reranker = None
            else:  # hybrid_reranked
                retrieval_service.pipeline.dense_retriever = original_dense
                retrieval_service.pipeline.bm25_retriever = original_bm25
                retrieval_service.pipeline.reranker = original_reranker

            results_by_diff = {"easy": [], "medium": [], "hard": []}
            all_metrics = []

            for q_obj in queries_list:
                q_id = q_obj["query_id"]
                query = q_obj["query"]
                diff = QueryClassifier.classify(query)

                expected_list = expected_map.get(q_id, [])
                expected_set = {(item["doc_id"], item["index"]) for item in expected_list}

                start_time = time.perf_counter()
                bundle = retrieval_service.retrieve(query, limit=10, profile=profile_name)
                latency = (time.perf_counter() - start_time) * 1000.0

                retrieved_list = [(chunk.document_id, chunk.metadata.get("paragraph_index", 0)) for chunk in bundle.chunks]

                precision = RetrievalMetrics.precision_at_k(retrieved_list, expected_set, k=10)
                recall = RetrievalMetrics.recall_at_k(retrieved_list, expected_set, k=10)
                mrr = RetrievalMetrics.reciprocal_rank(retrieved_list, expected_set)
                ndcg = RetrievalMetrics.ndcg_at_k(retrieved_list, expected_set, k=10)

                q_metrics = {
                    "precision@10": precision,
                    "recall@10": recall,
                    "mrr": mrr,
                    "ndcg@10": ndcg,
                    "latency_ms": latency
                }
                all_metrics.append(q_metrics)
                results_by_diff[diff].append(q_metrics)

            def aggregate(lst):
                if not lst:
                    return {"precision@10": 0.0, "recall@10": 0.0, "mrr": 0.0, "ndcg@10": 0.0, "latency_ms": 0.0}
                n = len(lst)
                return {
                    "precision@10": round(sum(x["precision@10"] for x in lst) / n, 4),
                    "recall@10": round(sum(x["recall@10"] for x in lst) / n, 4),
                    "mrr": round(sum(x["mrr"] for x in lst) / n, 4),
                    "ndcg@10": round(sum(x["ndcg@10"] for x in lst) / n, 4),
                    "latency_ms": round(sum(x["latency_ms"] for x in lst) / n, 2)
                }

            return {
                "overall": aggregate(all_metrics),
                "by_difficulty": {k: aggregate(v) for k, v in results_by_diff.items()}
            }

        # 1. Run ablation pipeline stages on "balanced" profile
        pipelines = ["bm25", "dense", "hybrid", "hybrid_reranked"]
        pipeline_reports = {}
        for p in pipelines:
            pipeline_reports[p] = evaluate_config(p, "balanced")

        # 2. Run search profile breakdowns on "hybrid_reranked"
        profiles = ["fast", "balanced", "quality"]
        profile_reports = {}
        for prof in profiles:
            profile_reports[prof] = evaluate_config("hybrid_reranked", prof)

        # Restore original pipeline components
        retrieval_service.pipeline.dense_retriever = original_dense
        retrieval_service.pipeline.bm25_retriever = original_bm25
        retrieval_service.pipeline.reranker = original_reranker

        reports = {
            "pipelines": pipeline_reports,
            "profiles": profile_reports
        }

        # backward compatibility fallback fields for old tests:
        reports["bm25"] = pipeline_reports["bm25"]["overall"]
        reports["dense"] = pipeline_reports["dense"]["overall"]
        reports["hybrid"] = pipeline_reports["hybrid"]["overall"]
        reports["hybrid_reranked"] = pipeline_reports["hybrid_reranked"]["overall"]

        output_dir = Path(__file__).parent.parent.parent / "storage" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_dir / "retrieval_benchmark_report.json", "w", encoding="utf-8") as f:
            json.dump(reports, f, indent=2)

        self._write_summary_markdown(reports, output_dir / "retrieval_benchmark_summary.md")
        return reports

    def _write_summary_markdown(self, reports: dict, path: Path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("# Retrieval Benchmark Evaluation Summary\n\n")
            
            f.write("## 1. Pipeline Ablation Study (Profile: Balanced)\n\n")
            f.write("| Pipeline | Precision@10 | Recall@10 | MRR | nDCG@10 | Avg Latency (ms) |\n")
            f.write("| --- | --- | --- | --- | --- | --- |\n")
            for p in ["bm25", "dense", "hybrid", "hybrid_reranked"]:
                metrics = reports["pipelines"][p]["overall"]
                f.write(
                    f"| {p.upper()} | {metrics['precision@10']:.4f} | {metrics['recall@10']:.4f} | "
                    f"{metrics['mrr']:.4f} | {metrics['ndcg@10']:.4f} | {metrics['latency_ms']:.2f}ms |\n"
                )
            f.write("\n")

            f.write("## 2. Search Profiles Performance Breakdown\n\n")
            f.write("| Profile | Precision@10 | Recall@10 | MRR | nDCG@10 | Avg Latency (ms) |\n")
            f.write("| --- | --- | --- | --- | --- | --- |\n")
            for prof in ["fast", "balanced", "quality"]:
                metrics = reports["profiles"][prof]["overall"]
                f.write(
                    f"| {prof.upper()} | {metrics['precision@10']:.4f} | {metrics['recall@10']:.4f} | "
                    f"{metrics['mrr']:.4f} | {metrics['ndcg@10']:.4f} | {metrics['latency_ms']:.2f}ms |\n"
                )
            f.write("\n")

            f.write("## 3. Query Difficulty Breakdowns (Profile: Balanced)\n\n")
            f.write("| Difficulty | Pipeline | Precision@10 | Recall@10 | MRR | Latency |\n")
            f.write("| --- | --- | --- | --- | --- | --- |\n")
            for diff in ["easy", "medium", "hard"]:
                for p in ["hybrid", "hybrid_reranked"]:
                    metrics = reports["pipelines"][p]["by_difficulty"][diff]
                    f.write(
                        f"| {diff.upper()} | {p.upper()} | {metrics['precision@10']:.4f} | {metrics['recall@10']:.4f} | "
                        f"{metrics['mrr']:.4f} | {metrics['latency_ms']:.2f}ms |\n"
                    )
            f.write("\n")

            hybrid_mrr = reports["pipelines"]["hybrid_reranked"]["overall"]["mrr"]
            dense_mrr = reports["pipelines"]["dense"]["overall"]["mrr"]
            if hybrid_mrr >= dense_mrr:
                f.write("### ✅ Verification Status: PASS\n")
                f.write("Reranked hybrid pipeline meets quality thresholds and matches or exceeds dense baseline performance.\n")
            else:
                f.write("### ⚠️ Verification Status: WARNING\n")
                f.write("Reranked hybrid pipeline MRR degraded compared to dense baseline. Investigation recommended.\n")
