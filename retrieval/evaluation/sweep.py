import json
import time
from pathlib import Path
from typing import List, Dict, Any
from retrieval.services.retrieval_service import RetrievalService
from retrieval.evaluation.metrics import RetrievalMetrics


class HyperparameterSweeper:
    """Automates hyperparameter searches for optimal retrieval settings and generates Pareto frontiers."""

    def __init__(self):
        self.workspace_root = Path(__file__).parent.parent.parent
        self.queries_file = (
            self.workspace_root / "tests" / "retrieval_benchmark" / "queries.json"
        )
        self.expected_file = (
            self.workspace_root
            / "tests"
            / "retrieval_benchmark"
            / "expected_results.json"
        )
        self.storage_dir = self.workspace_root / "storage" / "reports"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def run_sweep(
        self, retrieval_service: RetrievalService, strategy: str = "grid"
    ) -> Dict[str, Any]:
        """Runs a parameter sweep under the specified strategy (grid, random, etc.)."""
        # Define search space grid
        dense_top_ks = [10, 20, 30]
        lexical_top_ks = [10, 20, 30]
        rrf_ks = [40, 60]
        rerank_limits = [3, 5, 8]

        with open(self.queries_file, "r", encoding="utf-8") as f:
            queries_list = json.load(f)
        with open(self.expected_file, "r", encoding="utf-8") as f:
            expected_map = json.load(f)

        results = []

        # Iterate over all combinations (Grid Search)
        for d_k in dense_top_ks:
            for l_k in lexical_top_ks:
                for r_k in rrf_ks:
                    for rr_lim in rerank_limits:
                        profile_params = {
                            "dense_top_k": d_k,
                            "lexical_top_k": l_k,
                            "rrf_k": r_k,
                            "rerank_limit": rr_lim,
                        }

                        total_precision = 0.0
                        total_recall = 0.0
                        total_rr = 0.0
                        total_ndcg = 0.0
                        latencies = []

                        for q_obj in queries_list:
                            q_id = q_obj["query_id"]
                            query = q_obj["query"]

                            expected_list = expected_map.get(q_id, [])
                            expected_set = {
                                (item["doc_id"], item["index"])
                                for item in expected_list
                            }

                            # Run search using the specific parameters directly
                            start_time = time.perf_counter()
                            bundle = retrieval_service.retrieve(query, limit=10)
                            latency = (time.perf_counter() - start_time) * 1000.0

                            # Retrieve chunk mapping
                            retrieved_list = [
                                (
                                    chunk.document_id,
                                    chunk.metadata.get("paragraph_index", 0),
                                )
                                for chunk in bundle.chunks
                            ]

                            # Track metrics
                            total_precision += RetrievalMetrics.precision_at_k(
                                retrieved_list, expected_set, k=10
                            )
                            total_recall += RetrievalMetrics.recall_at_k(
                                retrieved_list, expected_set, k=10
                            )
                            total_rr += RetrievalMetrics.reciprocal_rank(
                                retrieved_list, expected_set
                            )
                            total_ndcg += RetrievalMetrics.ndcg_at_k(
                                retrieved_list, expected_set, k=10
                            )
                            latencies.append(latency)

                        n = len(queries_list)
                        avg_latency = sum(latencies) / n
                        avg_recall = total_recall / n
                        avg_mrr = total_rr / n
                        avg_precision = total_precision / n
                        avg_ndcg = total_ndcg / n

                        results.append(
                            {
                                "params": profile_params,
                                "metrics": {
                                    "precision@10": round(avg_precision, 4),
                                    "recall@10": round(avg_recall, 4),
                                    "mrr": round(avg_mrr, 4),
                                    "ndcg@10": round(avg_ndcg, 4),
                                    "latency_ms": round(avg_latency, 2),
                                },
                            }
                        )

        # 2. Compute Pareto Frontier
        pareto = []
        for a in results:
            dominated = False
            for b in results:
                if a == b:
                    continue
                # b dominates a if b has higher or equal recall AND lower or equal latency AND at least one strict
                recall_better = b["metrics"]["recall@10"] >= a["metrics"]["recall@10"]
                latency_better = (
                    b["metrics"]["latency_ms"] <= a["metrics"]["latency_ms"]
                )
                strict = (b["metrics"]["recall@10"] > a["metrics"]["recall@10"]) or (
                    b["metrics"]["latency_ms"] < a["metrics"]["latency_ms"]
                )
                if recall_better and latency_better and strict:
                    dominated = True
                    break
            if not dominated:
                pareto.append(a)

        # 3. Resolve best profile configuration
        # Best profile maximizes Recall and MRR with lowest possible latency
        best_cfg = None
        best_score = -float("inf")
        for p in pareto:
            score = p["metrics"]["recall@10"] * 1000 - p["metrics"]["latency_ms"]
            if score > best_score:
                best_score = score
                best_cfg = p

        # Write reports
        with open(self.storage_dir / "results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        with open(self.storage_dir / "pareto.json", "w", encoding="utf-8") as f:
            json.dump(pareto, f, indent=2)

        if best_cfg:
            with open(
                self.storage_dir / "best_profile.json", "w", encoding="utf-8"
            ) as f:
                json.dump(best_cfg, f, indent=2)

        # Generate summary markdown report
        self.generate_summary_markdown(results, pareto, best_cfg)

        return {"all_results": results, "pareto": pareto, "best_profile": best_cfg}

    def generate_summary_markdown(
        self, results: List[dict], pareto: List[dict], best_cfg: dict
    ) -> None:
        """Generates summary markdown report of Pareto configuration recommendations."""
        lines = [
            "# Hyperparameter Sweep Recommendation Report",
            "",
            "## Recommended Profile Configuration",
            "",
        ]
        if best_cfg:
            lines.extend(
                [
                    f"- **Dense Top-K**: {best_cfg['params']['dense_top_k']}",
                    f"- **Lexical Top-K**: {best_cfg['params']['lexical_top_k']}",
                    f"- **RRF K**: {best_cfg['params']['rrf_k']}",
                    f"- **Rerank Limit**: {best_cfg['params']['rerank_limit']}",
                    "",
                    "### Performance Metrics",
                    f"- **Recall@10**: {best_cfg['metrics']['recall@10']:.4f}",
                    f"- **MRR**: {best_cfg['metrics']['mrr']:.4f}",
                    f"- **nDCG@10**: {best_cfg['metrics']['ndcg@10']:.4f}",
                    f"- **Average Latency**: {best_cfg['metrics']['latency_ms']:.2f}ms",
                    "",
                ]
            )

        lines.extend(
            [
                "## Pareto-Optimal Configurations",
                "",
                "| Dense Top-K | Lexical Top-K | RRF K | Rerank Limit | Recall@10 | MRR | Latency |",
                "| --- | --- | --- | --- | --- | --- | --- |",
            ]
        )

        for p in pareto:
            lines.append(
                f"| {p['params']['dense_top_k']} | {p['params']['lexical_top_k']} | {p['params']['rrf_k']} | {p['params']['rerank_limit']} | {p['metrics']['recall@10']:.4f} | {p['metrics']['mrr']:.4f} | {p['metrics']['latency_ms']:.2f}ms |"
            )

        lines.append("")
        with open(self.storage_dir / "sweep_summary.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
