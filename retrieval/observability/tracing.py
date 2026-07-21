import time


class RetrievalTracer:
    """Collects step-by-step latency timeline checks across retrieval pipelines."""

    def __init__(self):
        self._spans = {}

    def start_span(self, name: str) -> None:
        self._spans[name] = {"start": time.perf_counter()}

    def end_span(self, name: str) -> None:
        if name in self._spans:
            self._spans[name]["duration_ms"] = int(
                (time.perf_counter() - self._spans[name]["start"]) * 1000
            )

    def get_traces(self) -> dict:
        return {name: span.get("duration_ms", 0) for name, span in self._spans.items()}
