import time
import logging

logger = logging.getLogger("retrieval_observability")

class RetrievalEvent:
    """Base event payload wrapper for observability metrics logging."""
    def __init__(self, event_type: str, session_id: str, payload: dict = None):
        self.event_type = event_type
        self.session_id = session_id
        self.timestamp = time.time()
        self.payload = payload or {}

    def log(self) -> None:
        logger.info(f"[Session {self.session_id}] Event: {self.event_type} | Data: {self.payload}")

class ObservabilityEvents:
    """Central emitter logging key retrieval lifecycle milestones."""
    
    @staticmethod
    def emit_started(session_id: str, query: str) -> None:
        RetrievalEvent("QueryStarted", session_id, {"query": query}).log()

    @staticmethod
    def emit_chunking_completed(session_id: str, chunk_count: int) -> None:
        RetrievalEvent("ChunkingCompleted", session_id, {"chunks": chunk_count}).log()

    @staticmethod
    def emit_retrieval_completed(session_id: str, candidates_count: int) -> None:
        RetrievalEvent("RetrievalCompleted", session_id, {"candidates": candidates_count}).log()

    @staticmethod
    def emit_fusion_completed(session_id: str, fused_count: int) -> None:
        RetrievalEvent("FusionCompleted", session_id, {"fused": fused_count}).log()

    @staticmethod
    def emit_reranking_completed(session_id: str, count: int) -> None:
        RetrievalEvent("RerankingCompleted", session_id, {"reranked": count}).log()

    @staticmethod
    def emit_selection_completed(session_id: str, selected_count: int) -> None:
        RetrievalEvent("SelectionCompleted", session_id, {"selected": selected_count}).log()
