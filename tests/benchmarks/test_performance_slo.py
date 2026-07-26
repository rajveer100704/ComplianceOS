"""Automated P95 latency SLO benchmark tests for ComplianceOS core engine."""

import time
import pytest
from pipeline import verify_claim


def test_retrieval_p95_latency_slo():
    """Verify that claim verification P95 latency remains strictly below 250ms SLO threshold on dev environment."""
    latencies = []
    sample_claims = [
        "All pressure vessels must comply with ASME Section VIII Division 1 requirements.",
        "Flight safety systems require dual redundancy according to FAA Part 450.",
        "Nuclear piping systems must maintain structural integrity under seismic stress.",
    ]

    # Warmup
    verify_claim(sample_claims[0])

    for _ in range(5):
        for claim in sample_claims:
            t0 = time.perf_counter()
            verify_claim(claim)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)

    latencies.sort()
    p95_index = int(len(latencies) * 0.95)
    p95_latency = latencies[p95_index]

    print(f"\n[SLO Benchmark] Measured P95 Latency: {p95_latency:.2f} ms")
    assert (
        p95_latency < 250.0
    ), f"P95 latency {p95_latency:.2f}ms exceeded 250ms SLO threshold!"
