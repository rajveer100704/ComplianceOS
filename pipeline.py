"""
Agent pipeline (ai-agent-development + langgraph).

Explicit graph, not one big prompt:

    START -> parse_documents -> extract_claims -> verify_claims -> draft_summary -> END

Each node is a plain function over shared state; every node writes an
audit_log row so the full decision trail is reconstructable per request.
No LLM call is required for this prototype — verify_claims delegates to
score_claim() (TF-IDF retrieval + threshold scoring) in main.py's engine.
Nodes are the seam for swapping in a real LLM per stage later.
"""

from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, START, END

import db


class PipelineState(TypedDict):
    request_id: int
    run_id: int
    documents: List[Dict[str, Any]]  # [{id, filename, text}]
    claims: List[Dict[str, Any]]  # raw split claim strings, per doc
    results: List[Dict[str, Any]]  # verified ClaimResult dicts
    draft_summary: str


def parse_documents(state: PipelineState) -> dict:
    rid = state["request_id"]
    db.log_audit(
        rid, "parse_documents", f"{len(state['documents'])} document(s) received"
    )
    return {}


def extract_claims(state: PipelineState, split_fn) -> dict:
    rid = state["request_id"]
    claims = []
    for doc in state["documents"]:
        for text in split_fn(doc["text"]):
            claims.append({"document_id": doc["id"], "text": text})
    db.log_audit(rid, "extract_claims", f"{len(claims)} candidate claim(s) extracted")
    return {"claims": claims}


def verify_claims(state: PipelineState, score_fn) -> dict:
    rid, run_id = state["request_id"], state["run_id"]
    results = []
    for c in state["claims"]:
        r = score_fn(c["text"]).model_dump()
        db.save_claim(rid, run_id, c["document_id"], r)
        results.append(r)
    supported = sum(1 for r in results if r["status"] == "SUPPORTED")
    db.log_audit(rid, "verify_claims", f"{supported}/{len(results)} claim(s) SUPPORTED")
    return {"results": results}


def draft_summary(state: PipelineState, corpus_size: int) -> dict:
    rid, run_id = state["request_id"], state["run_id"]
    results = state["results"]
    total = len(results) or 1
    supported = sum(1 for r in results if r["status"] == "SUPPORTED")
    unsupported = [r["claim"] for r in results if r["status"] == "UNSUPPORTED"]
    score = round(supported / total * 100, 1)
    summary = (
        f"Compliance score {score}%. {supported}/{total} claims supported by cited regulation. "
        + (
            f"{len(unsupported)} claim(s) need evidence or rewrite before submission."
            if unsupported
            else "All claims traceable to a regulation."
        )
    )
    from retrieval.config.loader import ConfigLoader

    config = ConfigLoader.load()
    ret_conf = config.get("retrieval", {})
    retrieval_method = ret_conf.get("retriever", {}).get("engine", "hybrid")
    support_thresh = ret_conf.get("thresholds", {}).get("support", 0.35)
    partial_thresh = ret_conf.get("thresholds", {}).get("partial", 0.15)

    receipt = {
        "run_id": run_id,
        "claim_count": len(results),
        "corpus_size": corpus_size,
        "retrieval_method": retrieval_method,
        "threshold_config": {"support": support_thresh, "partial": partial_thresh},
        "score_pct": score,
        "generated_at": db._now(),
    }
    db.log_audit(rid, "draft_summary", summary)
    db.finalize_run(run_id, rid, summary, receipt)
    db.set_status(rid, "needs_review", "Pipeline complete — awaiting human review")
    return {"draft_summary": summary}


def build_graph(split_fn, score_fn, corpus_size: int):
    graph = StateGraph(PipelineState)
    graph.add_node("parse_documents", parse_documents)
    graph.add_node("extract_claims", lambda s: extract_claims(s, split_fn))
    graph.add_node("verify_claims", lambda s: verify_claims(s, score_fn))
    graph.add_node("draft_summary", lambda s: draft_summary(s, corpus_size))

    graph.add_edge(START, "parse_documents")
    graph.add_edge("parse_documents", "extract_claims")
    graph.add_edge("extract_claims", "verify_claims")
    graph.add_edge("verify_claims", "draft_summary")
    graph.add_edge("draft_summary", END)
    return graph.compile()


def run_pipeline(
    request_id: int,
    documents: List[Dict[str, Any]],
    split_fn,
    score_fn,
    corpus_size: int = 0,
) -> dict:
    run_id, version = db.create_run(request_id)
    app = build_graph(split_fn, score_fn, corpus_size)
    db.set_status(request_id, "running", f"Pipeline v{version} started")
    final_state = app.invoke(
        {
            "request_id": request_id,
            "run_id": run_id,
            "documents": documents,
            "claims": [],
            "results": [],
            "draft_summary": "",
        }
    )
    final_state["run_id"] = run_id
    final_state["version"] = version
    return final_state
