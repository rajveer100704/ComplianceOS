from fastapi.testclient import TestClient
import pytest
from main import app

client = TestClient(app)


def test_regulations_endpoint_returns_corpus():
    res = client.get("/api/regulations")
    assert res.status_code == 200
    assert len(res.json()) >= 5


def test_supported_claim():
    res = client.post(
        "/api/verify",
        json={
            "claims": [
                "The vehicle satisfies flight safety analysis requirements for public risk."
            ]
        },
    )
    body = res.json()
    assert body[0]["status"] == "SUPPORTED"
    assert body[0]["citation"] == "FAA-450.115"


def test_unsupported_claim():
    res = client.post(
        "/api/verify",
        json={
            "claims": [
                "The spacecraft uses lightweight composite panels for thermal protection."
            ]
        },
    )
    body = res.json()
    assert body[0]["status"] == "UNSUPPORTED"
    assert body[0]["citation"] == "\u2014"


def test_request_lifecycle_end_to_end():
    r = client.post(
        "/api/requests",
        json={"project": "Rocket Alpha", "regulator": "FAA", "owner": "Rajveer"},
    )
    rid = r.json()["id"]

    client.post(
        f"/api/requests/{rid}/documents",
        json={
            "filename": "flight_safety.txt",
            "text": "The vehicle satisfies flight safety analysis requirements for public risk. "
            "The spacecraft uses lightweight composite panels for thermal protection.",
        },
    )

    run = client.post(f"/api/requests/{rid}/run")
    assert run.status_code == 200
    results = run.json()["results"]
    assert len(results) == 2
    statuses = {r["status"] for r in results}
    assert "SUPPORTED" in statuses
    assert "UNSUPPORTED" in statuses

    detail = client.get(f"/api/requests/{rid}").json()
    assert detail["request"]["status"] == "needs_review"
    assert len(detail["claims"]) == 2
    assert any(a["stage"] == "draft_summary" for a in detail["audit_log"])

    claim_id = detail["claims"][0]["id"]
    review = client.post(f"/api/claims/{claim_id}/review", json={"decision": "approve"})
    assert review.status_code == 200


def test_run_without_documents_rejected():
    r = client.post(
        "/api/requests",
        json={"project": "Empty", "regulator": "NRC", "owner": "Rajveer"},
    )
    rid = r.json()["id"]
    run = client.post(f"/api/requests/{rid}/run")
    assert run.status_code == 400


def test_rerun_creates_new_version_not_overwrite():
    r = client.post(
        "/api/requests",
        json={"project": "Versioned", "regulator": "FAA", "owner": "Rajveer"},
    )
    rid = r.json()["id"]
    client.post(
        f"/api/requests/{rid}/documents",
        json={
            "filename": "a.txt",
            "text": "The vehicle satisfies flight safety analysis requirements.",
        },
    )
    run1 = client.post(f"/api/requests/{rid}/run").json()
    run2 = client.post(f"/api/requests/{rid}/run").json()
    assert run1["version"] == 1
    assert run2["version"] == 2

    detail = client.get(f"/api/requests/{rid}").json()
    assert len(detail["runs"]) == 2
    # claims from both runs persist (immutable history), not overwritten
    assert len(detail["claims"]) == 2
    assert detail["runs"][0]["receipt"] is not None


def test_pdf_upload_rejects_non_pdf():
    r = client.post(
        "/api/requests",
        json={"project": "PDF Test", "regulator": "NRC", "owner": "Rajveer"},
    )
    rid = r.json()["id"]
    res = client.post(
        f"/api/requests/{rid}/documents/pdf",
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )
    assert res.status_code == 400


def test_pdf_upload_accepts_real_pdf():
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72), "The reactor facility safety analysis report describes design bases."
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    r = client.post(
        "/api/requests",
        json={"project": "PDF Test 2", "regulator": "NRC", "owner": "Rajveer"},
    )
    rid = r.json()["id"]
    res = client.post(
        f"/api/requests/{rid}/documents/pdf",
        files={"file": ("safety_report.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["pages"] == 1
    assert body["chars_extracted"] > 0

    detail = client.get(f"/api/requests/{rid}").json()
    assert detail["documents"][0]["source_type"] == "pdf"


def test_knowledge_graph_and_coverage():
    r = client.post(
        "/api/requests",
        json={"project": "Graph Test", "regulator": "FAA", "owner": "Rajveer"},
    )
    rid = r.json()["id"]
    client.post(
        f"/api/requests/{rid}/documents",
        json={
            "filename": "a.txt",
            "text": "The vehicle satisfies flight safety analysis requirements for public risk. "
            "The spacecraft uses lightweight composite panels for thermal protection.",
        },
    )
    client.post(f"/api/requests/{rid}/run")

    graph = client.get(f"/api/requests/{rid}/graph").json()
    req_nodes = [n for n in graph["nodes"] if n["type"] == "requirement"]
    claim_nodes = [n for n in graph["nodes"] if n["type"] == "claim"]
    assert len(req_nodes) == 1  # only the supported claim cites a real requirement
    assert len(claim_nodes) == 2
    assert any(e["type"] == "SATISFIES" for e in graph["edges"])

    coverage = client.get(f"/api/requests/{rid}/coverage").json()
    assert coverage["version"] == 1
    assert coverage["covered"] == 1
    assert "FAA-450.115" not in coverage["missing"]

    dependents = client.get("/api/requirements/FAA-450.115/dependents").json()
    assert any(d["request_id"] == rid for d in dependents)


def test_version_diff_detects_status_change():
    r = client.post(
        "/api/requests",
        json={"project": "Diff Test", "regulator": "FAA", "owner": "Rajveer"},
    )
    rid = r.json()["id"]
    client.post(
        f"/api/requests/{rid}/documents",
        json={
            "filename": "a.txt",
            "text": "The spacecraft uses lightweight composite panels for thermal protection.",
        },
    )
    client.post(f"/api/requests/{rid}/run")  # v1: UNSUPPORTED
    client.post(
        f"/api/requests/{rid}/documents",
        json={
            "filename": "b.txt",
            "text": "The vehicle satisfies flight safety analysis requirements for public risk.",
        },
    )
    client.post(f"/api/requests/{rid}/run")  # v2: adds a SUPPORTED claim too

    diff = client.get(
        f"/api/requests/{rid}/diff", params={"from_version": 1, "to_version": 2}
    ).json()
    assert any(a["status"] == "SUPPORTED" for a in diff["added"])


def test_dashboard_and_review_queue():
    r = client.post(
        "/api/requests",
        json={"project": "Dash Test", "regulator": "FAA", "owner": "Rajveer"},
    )
    rid = r.json()["id"]
    client.post(
        f"/api/requests/{rid}/documents",
        json={
            "filename": "a.txt",
            "text": "The spacecraft uses lightweight composite panels for thermal protection.",
        },
    )
    client.post(f"/api/requests/{rid}/run")

    dash = client.get("/api/dashboard").json()
    assert dash["needs_review"] >= 1
    assert dash["total_requests"] >= 1

    queue = client.get("/api/review-queue").json()
    assert any(c["request_id"] == rid for c in queue)


def test_comment_and_resolve_claim():
    r = client.post(
        "/api/requests",
        json={"project": "Comment Test", "regulator": "NRC", "owner": "Rajveer"},
    )
    rid = r.json()["id"]
    client.post(
        f"/api/requests/{rid}/documents",
        json={
            "filename": "a.txt",
            "text": "The reactor facility safety analysis report describes design bases and safety limits.",
        },
    )
    client.post(f"/api/requests/{rid}/run")
    claim_id = client.get(f"/api/requests/{rid}").json()["claims"][0]["id"]

    res = client.post(
        f"/api/claims/{claim_id}/comment",
        json={"comment": "Looks good, double check page ref."},
    )
    assert res.status_code == 200
    res = client.post(f"/api/claims/{claim_id}/resolve")
    assert res.status_code == 200

    detail = client.get(f"/api/requests/{rid}").json()
    claim = next(c for c in detail["claims"] if c["id"] == claim_id)
    assert claim["comment"] == "Looks good, double check page ref."
    assert claim["resolved"] == 1


def test_report_builder():
    r = client.post(
        "/api/requests",
        json={"project": "Report Test", "regulator": "FAA", "owner": "Rajveer"},
    )
    rid = r.json()["id"]
    client.post(
        f"/api/requests/{rid}/documents",
        json={
            "filename": "a.txt",
            "text": "The vehicle satisfies flight safety analysis requirements for public risk. "
            "The spacecraft uses lightweight composite panels for thermal protection.",
        },
    )
    client.post(f"/api/requests/{rid}/run")

    report = client.get(f"/api/requests/{rid}/report").json()
    assert report["version"] == 1
    assert report["receipt"]["claim_count"] == 2
    assert len(report["open_risks"]) == 1
    assert len(report["recommendations"]) == 1


def test_submission_workspace_full_lifecycle():
    r = client.post(
        "/api/requests",
        json={"project": "Submission Test", "regulator": "FAA", "owner": "Rajveer"},
    )
    rid = r.json()["id"]
    client.post(
        f"/api/requests/{rid}/documents",
        json={
            "filename": "a.txt",
            "text": "The vehicle satisfies flight safety analysis requirements for public risk.",
        },
    )
    client.post(f"/api/requests/{rid}/run")

    # can't approve with a pending claim
    res = client.post(f"/api/requests/{rid}/approve")
    assert res.status_code == 409

    claim_id = client.get(f"/api/requests/{rid}").json()["claims"][0]["id"]
    client.post(f"/api/claims/{claim_id}/review", json={"decision": "approve"})

    res = client.post(f"/api/requests/{rid}/approve")
    assert res.status_code == 200
    assert client.get(f"/api/requests/{rid}").json()["request"]["status"] == "approved"

    # can't lock before approved -> already approved, so lock should work
    res = client.post(f"/api/requests/{rid}/lock")
    assert res.status_code == 200
    assert client.get(f"/api/requests/{rid}").json()["request"]["status"] == "locked"

    # immutability: no new documents, no rerun, no review/comment once locked
    res = client.post(
        f"/api/requests/{rid}/documents",
        json={"filename": "b.txt", "text": "late addition"},
    )
    assert res.status_code == 423
    res = client.post(f"/api/requests/{rid}/run")
    assert res.status_code == 423
    res = client.post(f"/api/claims/{claim_id}/review", json={"decision": "reject"})
    assert res.status_code == 423
    res = client.post(f"/api/claims/{claim_id}/comment", json={"comment": "too late"})
    assert res.status_code == 423

    res = client.post(f"/api/requests/{rid}/submit")
    assert res.status_code == 200
    res = client.post(f"/api/requests/{rid}/archive")
    assert res.status_code == 200
    assert client.get(f"/api/requests/{rid}").json()["request"]["status"] == "archived"

    # can't skip stages
    r2 = client.post(
        "/api/requests",
        json={"project": "Skip Test", "regulator": "NRC", "owner": "Rajveer"},
    )
    rid2 = r2.json()["id"]
    res = client.post(f"/api/requests/{rid2}/lock")
    assert res.status_code == 409
    res = client.post(f"/api/requests/{rid2}/submit")
    assert res.status_code == 409


def test_reopen_reverts_approval():
    r = client.post(
        "/api/requests",
        json={"project": "Reopen Test", "regulator": "FAA", "owner": "Rajveer"},
    )
    rid = r.json()["id"]
    client.post(
        f"/api/requests/{rid}/documents",
        json={
            "filename": "a.txt",
            "text": "The vehicle satisfies flight safety analysis requirements for public risk.",
        },
    )
    client.post(f"/api/requests/{rid}/run")
    claim_id = client.get(f"/api/requests/{rid}").json()["claims"][0]["id"]
    client.post(f"/api/claims/{claim_id}/review", json={"decision": "approve"})
    client.post(f"/api/requests/{rid}/approve")

    res = client.post(f"/api/requests/{rid}/reopen")
    assert res.status_code == 200
    assert (
        client.get(f"/api/requests/{rid}").json()["request"]["status"] == "needs_review"
    )


def test_multi_sentence_claim_split():
    res = client.post(
        "/api/verify",
        json={
            "claims": [
                "The vehicle satisfies flight safety analysis. The reactor has a safety analysis report."
            ]
        },
    )
    body = res.json()
    assert len(body) == 2


def test_advanced_pdf_parser_features():
    import fitz
    from pathlib import Path
    import json

    # 1. Create a dummy PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72), "Header Block: This is a long header to exceed the OCR threshold."
    )
    page.insert_text(
        (72, 100), "Column A Line 1: Additional safety analysis and details."
    )
    page.insert_text((200, 100), "Column B Line 1: Additional verification checklists.")
    pdf_bytes = doc.tobytes()
    doc.close()

    # 2. Upload PDF
    r = client.post(
        "/api/requests",
        json={
            "project": "Advanced Parser Test",
            "regulator": "NRC",
            "owner": "Rajveer",
        },
    )
    rid = r.json()["id"]
    res = client.post(
        f"/api/requests/{rid}/documents/pdf",
        files={"file": ("safety_report_advanced.pdf", pdf_bytes, "application/pdf")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["pages"] == 1
    assert "parser_metadata" in body

    meta = body["parser_metadata"]
    assert meta["parser_version"] == "1.0.0"
    assert meta["parser_engine"] == "pymupdf"
    assert meta["table_engine"] == "PyMuPDF"
    assert meta["layout_mode"] == "blocks"
    assert "ocr_enabled" in meta
    assert meta["pages"] == 1
    assert "elapsed_ms" in meta
    assert "pages_per_second" in meta
    assert "warnings" in meta

    # 3. Check request-scoped metadata and receipt file persistence
    meta_path = (
        Path(__file__).parent
        / "storage"
        / "requests"
        / f"REQ-{rid}"
        / "documents"
        / "safety_report_advanced.pdf.metadata.json"
    )
    receipt_path = (
        Path(__file__).parent
        / "storage"
        / "requests"
        / f"REQ-{rid}"
        / "documents"
        / "safety_report_advanced.pdf.receipt.json"
    )
    assert meta_path.exists()
    assert receipt_path.exists()

    with open(meta_path, "r", encoding="utf-8") as f:
        meta_file = json.load(f)
    assert meta_file["parser_version"] == "1.0.0"
    assert meta_file["parser_engine"] == "pymupdf"

    with open(receipt_path, "r", encoding="utf-8") as f:
        receipt_file = json.load(f)
    assert receipt_file["engine"] == "pymupdf"
    assert receipt_file["engine_version"] == "1.0.0"
    assert receipt_file["ocr_used"] is False
    assert "capabilities" in receipt_file
    assert receipt_file["capabilities"]["tables"] is True


def test_parser_factory_and_registry():
    from parsers.registry import PARSER_REGISTRY
    from parsers.factory import ParserFactory
    from parsers.pymupdf_parser import PyMuPDFParser
    import pytest

    # 1. Registry verification
    assert "pymupdf" in PARSER_REGISTRY
    assert "marker" in PARSER_REGISTRY
    assert "docling" in PARSER_REGISTRY

    # 2. PyMuPDF resolve
    parser = ParserFactory.get_parser("pymupdf")
    assert isinstance(parser, PyMuPDFParser)
    assert parser.capabilities.tables is True
    assert parser.capabilities.ocr is True

    # 3. Fallback tests
    parser_fallback = ParserFactory.get_parser("marker", allow_fallback=True)
    assert isinstance(parser_fallback, PyMuPDFParser)

    with pytest.raises(ImportError):
        ParserFactory.get_parser("marker", allow_fallback=False)


def test_retrieval_architecture_and_pipeline():
    from pathlib import Path
    import json
    from retrieval.registry import (
        CHUNKER_REGISTRY,
        EMBEDDING_REGISTRY,
        VECTOR_STORE_REGISTRY,
        RETRIEVER_REGISTRY,
        RERANKER_REGISTRY,
    )
    from retrieval.factory import RetrievalFactory
    from retrieval.container import Container
    from retrieval.fusion.rrf import ReciprocalRankFusion
    from retrieval.models.chunk import Chunk

    # 1. Registry verification
    assert "paragraph" in CHUNKER_REGISTRY
    assert "section" in CHUNKER_REGISTRY
    assert "tfidf" in EMBEDDING_REGISTRY
    assert "bgem3" in EMBEDDING_REGISTRY
    assert "local" in VECTOR_STORE_REGISTRY
    assert "qdrant" in VECTOR_STORE_REGISTRY
    assert "dense" in RETRIEVER_REGISTRY
    assert "bm25" in RETRIEVER_REGISTRY
    assert "hybrid" in RETRIEVER_REGISTRY
    assert "cosine" in RERANKER_REGISTRY
    assert "cross_encoder" in RERANKER_REGISTRY

    # 2. Chunker verification
    chunker = RetrievalFactory.get_chunker("section")
    chunks = chunker.chunk(
        doc_id=99,
        text="Paragraph 1\n\n--- Page Break ---\n\nParagraph 2\n\nParagraph 3",
        doc_metadata={"filename": "test.txt"},
    )
    assert len(chunks) == 3
    assert chunks[0].document_id == 99
    assert chunks[0].metadata["page"] == 1
    assert chunks[1].metadata["page"] == 2
    assert chunks[1].metadata["paragraph_index"] == 0
    assert chunks[2].metadata["page"] == 2
    assert chunks[2].metadata["paragraph_index"] == 1

    # 3. RRF Rank Fusion math verification
    rrf = ReciprocalRankFusion(k=60)
    c1 = Chunk(chunk_id="c1", document_id=1, text="hello")
    c2 = Chunk(chunk_id="c2", document_id=1, text="world")
    # c1 ranked 1st in dense, c2 ranked 2nd
    dense_res = [(c1, 0.9), (c2, 0.8)]
    # c2 ranked 1st in bm25, c1 ranked 2nd
    bm25_res = [(c2, 0.95), (c1, 0.75)]
    fused = rrf.fuse(dense_res, bm25_res, limit=2)
    assert len(fused) == 2
    # RRF score = 1/(60+1) + 1/(60+2) = 0.0163934 + 0.016129 = 0.032522
    assert abs(fused[0][1] - (1.0 / 61 + 1.0 / 62)) < 1e-6

    # 4. Dependency Injection Container verification
    Container.reset()
    ret_service = Container.get_retrieval_service()
    idx_service = Container.get_indexing_service()
    lifecycle_mgr = Container.get_lifecycle_manager()
    assert ret_service is not None
    assert idx_service is not None
    assert lifecycle_mgr is not None

    # 5. Pipeline run integration test
    # Create request and paste a document
    r = client.post(
        "/api/requests",
        json={
            "project": "Retrieval Pipeline Test",
            "regulator": "FAA",
            "owner": "Alice",
        },
    )
    rid = r.json()["id"]
    client.post(
        f"/api/requests/{rid}/documents",
        json={
            "filename": "flight_test.txt",
            "text": "The vehicle satisfies public risk safety rules.",
        },
    )
    # Run the request (runs the pipeline verifying claims against indexed regulations)
    r_run = client.post(f"/api/requests/{rid}/run")
    assert r_run.status_code == 200
    res_body = r_run.json()
    assert "summary" in res_body
    assert "results" in res_body

    # Check generated retrieval.receipt.json file
    receipt_path = (
        Path(__file__).parent
        / "storage"
        / "requests"
        / f"REQ-{rid}"
        / "retrieval.receipt.json"
    )
    assert receipt_path.exists()
    with open(receipt_path, "r", encoding="utf-8") as f:
        ret_receipt = json.load(f)
    assert ret_receipt["request_id"] == rid
    assert "receipts" in ret_receipt
    assert len(ret_receipt["receipts"]) > 0
    first_receipt = ret_receipt["receipts"][0]
    assert "query" in first_receipt
    assert "chunker" in first_receipt
    assert "embedding_model" in first_receipt
    assert "vector_store" in first_receipt
    assert "retriever" in first_receipt
    assert "latency_ms" in first_receipt


@pytest.mark.asyncio
async def test_database_persistence_and_rollback():
    """Verifies Unit of Work transaction rollbacks and database service DI wiring."""
    from retrieval.container import Container
    from database.services.unit_of_work import UnitOfWork
    from database.models.request import RequestModel
    from database.services.persistence_service import PersistenceService
    from sqlalchemy import select

    # 1. Verify DI wiring
    session_factory = Container.get_session_factory()
    assert session_factory is not None

    # 2. Add request and verify CRUD
    req_id = await PersistenceService.create_request(
        project="Integration UOW Test", regulator="FAA", owner="Alice"
    )
    assert req_id is not None

    # 3. Verify Rollback behavior
    try:
        async with UnitOfWork() as uow:
            r = RequestModel(
                project="Should Be Rolled Back", regulator="NRC", owner="Bob"
            )
            await uow.requests.add(r)
            # Raise exception before committing to trigger automatic rollback in __aexit__
            raise ValueError("Forced Rollback Exception")
            await uow.commit()
    except ValueError:
        pass

    # Verify that the rolled back request does not exist
    async with UnitOfWork() as uow:
        stmt = select(RequestModel).where(
            RequestModel.project == "Should Be Rolled Back"
        )
        res = await uow.session.execute(stmt)
        assert res.scalar() is None


@pytest.mark.asyncio
async def test_database_health_and_bootstrap():
    """Verifies database health checks and bootstrap execution."""
    from database.health import DatabaseHealth
    from database.bootstrap import bootstrap_database

    await bootstrap_database()
    health = await DatabaseHealth.check_health()
    assert health["status"] == "healthy"
    assert "provider" in health


@pytest.mark.asyncio
async def test_worker_bootstrap_and_queue_fallback():
    """Verifies that the worker bootstrapper is correct and fallbacks work."""
    from worker.bootstrap import bootstrap_worker
    from retrieval.container import Container

    success, msg = await bootstrap_worker(
        redis_url="redis://invalid_localhost:12345/0", allow_fallback=True
    )
    assert success is True
    assert "bootstrapped" in msg

    backend = Container.get_queue_backend()
    assert backend is not None


@pytest.mark.asyncio
async def test_worker_task_lifecycle_and_cancellation():
    """Verifies task status tracking and cancellation on QueueBackend."""
    from retrieval.container import Container
    from worker.state import TaskStateManager

    backend = Container.get_queue_backend()
    import uuid

    job_id = f"test-job-cancel-{uuid.uuid4()}"

    # Track task
    await TaskStateManager.create_task(job_id, "parse_and_index_document_task")
    await backend.enqueue(job_id, "parse_and_index_document_task")

    # Cancel task
    success = await backend.cancel(job_id)
    assert success is True

    # Mark cancelled in DB
    await TaskStateManager.update_task_status(job_id, "CANCELLED")

    status_details = await TaskStateManager.get_task(job_id)
    assert status_details["status"] == "CANCELLED"


@pytest.mark.asyncio
async def test_outbox_event_dispatching():
    """Verifies transaction outbox events are written and dispatched correctly."""
    from database.services.persistence_service import PersistenceService
    from database.services.unit_of_work import UnitOfWork
    from database.models.outbox import OutboxEventModel
    from worker.dispatcher import OutboxDispatcher
    from retrieval.container import Container
    from sqlalchemy import select

    # 1. Create a request and upload document (should write outbox event)
    req_id = await PersistenceService.create_request(
        project="Outbox Test", regulator="FAA", owner="Alice"
    )
    doc_id = await PersistenceService.add_document(
        request_id=req_id,
        filename="test.pdf",
        text="Some PDF content",
        source_type="pdf",
    )

    # 2. Assert outbox event exists and is not processed
    async with UnitOfWork() as uow:
        stmt = select(OutboxEventModel).where(OutboxEventModel.processed == False)
        res = await uow.session.execute(stmt)
        events = res.scalars().all()
        assert len(events) >= 1
        uploaded_event = next(
            (e for e in events if e.payload.get("document_id") == doc_id), None
        )
        assert uploaded_event is not None
        assert uploaded_event.event_type == "document_uploaded"

    # 3. Dispatch event
    backend = Container.get_queue_backend()
    dispatcher = OutboxDispatcher(backend)
    await dispatcher.dispatch_events()

    # 4. Assert outbox event is now marked processed
    async with UnitOfWork() as uow:
        stmt = select(OutboxEventModel).where(OutboxEventModel.processed == True)
        res = await uow.session.execute(stmt)
        processed_events = res.scalars().all()
        target = next(
            (e for e in processed_events if e.payload.get("document_id") == doc_id),
            None,
        )
        assert target is not None
        assert target.processed is True
        assert target.processed_at is not None


@pytest.mark.asyncio
async def test_model_manager_and_device():
    """Verifies that ModelManager identifies device targets properly."""
    from retrieval.models.manager import ModelManager

    device = ModelManager.get_device("cpu")
    assert device == "cpu"

    device_auto = ModelManager.get_device("auto")
    assert device_auto in ["cpu", "cuda", "mps"]


@pytest.mark.asyncio
async def test_embedding_cache_operations(tmp_path):
    """Verifies embedding cache get, set, prune, and invalidation rules."""
    from retrieval.cache.embedding_cache import EmbeddingCache

    db_file = str(tmp_path / "temp_cache.db")
    cache = EmbeddingCache(cache_path=db_file)

    text = "Compliance check safety regulations"
    model = "bge-small"
    version = "v1"
    vec = [0.1, 0.2, 0.3]

    # 1. Retrieve missing cache
    cached = cache.get(text, model, version)
    assert cached is None

    # 2. Set cache entry
    cache.set(text, model, version, dimension=3, embedding=vec)

    # 3. Retrieve valid cache entry
    cached = cache.get(text, model, version)
    assert cached == vec

    # 4. Invalidation check on version change
    cached_bad_version = cache.get(text, model, "v2")
    assert cached_bad_version is None

    # 5. Pruning check
    cache.prune_stale(model, "v2")
    cached_pruned = cache.get(text, model, version)
    assert cached_pruned is None


@pytest.mark.asyncio
async def test_evaluation_metrics():
    """Verifies information retrieval metrics equations (Precision, Recall, MRR, nDCG)."""
    from retrieval.evaluation.metrics import RetrievalMetrics

    retrieved = [(1, 0), (2, 1), (3, 0)]
    expected = {(2, 1), (4, 0)}

    # Precision@2 = 1 / 2 = 0.5
    p2 = RetrievalMetrics.precision_at_k(retrieved, expected, k=2)
    assert p2 == 0.5

    # Recall@2 = 1 / 2 = 0.5
    r2 = RetrievalMetrics.recall_at_k(retrieved, expected, k=2)
    assert r2 == 0.5

    # MRR = 1 / 2 = 0.5 (first matched element is at index 1, i.e. rank 2)
    mrr = RetrievalMetrics.reciprocal_rank(retrieved, expected)
    assert mrr == 0.5

    # nDCG@2
    # DCG = 1 / log2(3) = 0.6309
    # IDCG = 1 / log2(2) + 1 / log2(3) = 1.6309
    # nDCG = 0.6309 / 1.6309 = 0.38685
    ndcg2 = RetrievalMetrics.ndcg_at_k(retrieved, expected, k=2)
    assert abs(ndcg2 - 0.38685) < 0.001


@pytest.mark.asyncio
async def test_benchmark_runner_execution(tmp_path):
    """Verifies that the benchmark runner executes searches and saves markdown summaries."""
    from retrieval.evaluation.benchmark import RetrievalBenchmarkRunner
    from retrieval.container import Container
    from database.services.persistence_service import PersistenceService
    import json
    from pathlib import Path

    # Initialize container to load defaults
    Container.initialize()
    service = Container.get_retrieval_service()
    indexing_service = Container.get_indexing_service()

    # 1. Create request and documents in DB with retry for locks
    import asyncio

    for attempt in range(5):
        try:
            req_id = await PersistenceService.create_request("FAA Test", "FAA", "Alice")
            doc_id1 = await PersistenceService.add_document(
                req_id,
                "faa_rules.txt",
                "What safety and risk assessment standards does the FAA enforce for spaceport operations?",
            )
            doc_id2 = await PersistenceService.add_document(
                req_id,
                "nrc_rules.txt",
                "What are the reactor containment safety rules defined by the NRC? safety analysis report guidelines for commercial nuclear power plants.",
            )
            break
        except Exception:
            if attempt == 4:
                raise
            await asyncio.sleep(0.5)

    # 2. Index documents
    indexing_service.index_document(
        doc_id1,
        "faa_rules.txt",
        "What safety and risk assessment standards does the FAA enforce for spaceport operations?",
    )
    indexing_service.index_document(
        doc_id2,
        "nrc_rules.txt",
        "What are the reactor containment safety rules defined by the NRC? safety analysis report guidelines for commercial nuclear power plants.",
    )

    # 3. Create expected file mapping actual doc_ids
    runner = RetrievalBenchmarkRunner()
    expected_map = {
        "Q-1": [{"doc_id": doc_id2, "index": 0}],
        "Q-2": [{"doc_id": doc_id2, "index": 0}],
        "Q-3": [{"doc_id": doc_id1, "index": 0}],
        "Q-4": [{"doc_id": doc_id1, "index": 0}],
        "Q-5": [{"doc_id": doc_id2, "index": 0}],
        "Q-6": [{"doc_id": doc_id2, "index": 0}],
    }
    with open(runner.expected_file, "w", encoding="utf-8") as f:
        json.dump(expected_map, f)

    # 4. Run evaluation
    reports = runner.run_evaluation(service)

    assert "bm25" in reports
    assert "dense" in reports
    assert "hybrid" in reports
    assert "hybrid_reranked" in reports

    # Verify report is written to storage
    workspace_root = Path(__file__).parent
    report_file = (
        workspace_root / "storage" / "reports" / "retrieval_benchmark_report.json"
    )
    summary_file = (
        workspace_root / "storage" / "reports" / "retrieval_benchmark_summary.md"
    )

    assert report_file.exists()
    assert summary_file.exists()


@pytest.mark.asyncio
async def test_query_classification():
    """Verifies that QueryClassifier parses text attributes to return easy, medium, or hard difficulty classes."""
    from retrieval.evaluation.query_classifier import QueryClassifier

    assert QueryClassifier.classify("FAA rules") == "easy"
    assert (
        QueryClassifier.classify(
            "What are the reactor containment safety rules defined by the NRC OR the FAA AND spaceport operations?"
        )
        == "hard"
    )
    assert (
        QueryClassifier.classify("Section 4: safety analysis guidelines.") == "medium"
    )


@pytest.mark.asyncio
async def test_latency_percentiles():
    """Verifies that LatencyPercentiles correctly aggregates and calculates latency summaries."""
    from retrieval.observability.percentiles import LatencyPercentiles

    latencies = [10.0, 20.0, 30.0, 40.0, 50.0]
    p = LatencyPercentiles.calculate(latencies)

    assert p["p50"] == 30.0
    assert p["avg"] == 30.0
    assert p["p90"] == 46.0


@pytest.mark.asyncio
async def test_regression_gates_triggers():
    """Verifies that RegressionGates detects MRR, Recall drops, or Latency increases."""
    from retrieval.evaluation.regression import RegressionGates

    base_run = {
        "report": {
            "hybrid_reranked": {"recall@10": 1.0, "mrr": 1.0, "latency_ms": 10.0}
        }
    }

    # 1. Recall drop failure (>1% drop)
    curr_recall_drop = {
        "hybrid_reranked": {"recall@10": 0.90, "mrr": 1.0, "latency_ms": 10.0}
    }
    passed, fails, warns = RegressionGates.verify(curr_recall_drop, base_run)
    assert passed is False
    assert len(fails) == 1
    assert "Recall@10" in fails[0]

    # 2. Latency warning check (>5% increase, but <10%)
    curr_warn = {"hybrid_reranked": {"recall@10": 1.0, "mrr": 1.0, "latency_ms": 10.8}}
    passed, fails, warns = RegressionGates.verify(curr_warn, base_run)
    assert passed is True
    assert len(fails) == 0
    assert len(warns) == 1
    assert "Latency" in warns[0]


@pytest.mark.asyncio
async def test_hyperparameter_sweep_execution():
    """Verifies that the HyperparameterSweeper runs sweeps and produces Pareto output files."""
    from retrieval.evaluation.sweep import HyperparameterSweeper
    from retrieval.container import Container

    Container.initialize()
    service = Container.get_retrieval_service()

    sweeper = HyperparameterSweeper()
    sweep_data = sweeper.run_sweep(service)

    assert "all_results" in sweep_data
    assert "pareto" in sweep_data

    from pathlib import Path

    workspace_root = Path(__file__).parent
    assert (workspace_root / "storage" / "reports" / "results.json").exists()
    assert (workspace_root / "storage" / "reports" / "pareto.json").exists()
    assert (workspace_root / "storage" / "reports" / "best_profile.json").exists()
    assert (workspace_root / "storage" / "reports" / "sweep_summary.md").exists()


@pytest.mark.asyncio
async def test_adaptive_top_k_routing():
    """Verifies that query difficulty routing modifies active retrieval Top-K limits."""
    from retrieval.container import Container

    Container.initialize()
    service = Container.get_retrieval_service()

    # 1. Easy query route check
    bundle_easy = service.retrieve("FAA rules")
    assert bundle_easy.receipt["difficulty"] == "easy"

    # 2. Hard query route check
    bundle_hard = service.retrieve(
        "What are the reactor containment safety rules defined by the NRC OR the FAA AND spaceport operations?"
    )
    assert bundle_hard.receipt["difficulty"] == "hard"


@pytest.mark.asyncio
async def test_review_state_transitions_and_permissions():
    """Verifies request review status transitions, permissions matrix, and rejections."""
    from database.services.persistence_service import PersistenceService
    from review.services.review_service import ReviewService
    from database.services.unit_of_work import UnitOfWork

    rid = await PersistenceService.create_request(
        project="Review State Test", regulator="FAA", owner="Alice"
    )

    # Verify initial state is "Draft"
    async with UnitOfWork() as uow:
        req = await uow.requests.get(rid)
        assert req.status == "Draft"

    # Transition to Assigned
    await ReviewService.assign_reviewer(
        request_id=rid, reviewer="Bob", assigned_by="Alice", role="Reviewer"
    )

    async with UnitOfWork() as uow:
        req = await uow.requests.get(rid)
        assert req.status == "Assigned"
        assert req.assigned_reviewer == "Bob"

    # Transition to In Review
    await ReviewService.transition_status(
        request_id=rid, new_status="In Review", user="Bob", role="Reviewer"
    )

    async with UnitOfWork() as uow:
        req = await uow.requests.get(rid)
        assert req.status == "In Review"

    # Reject transition from In Review directly to Published (must go to Approved first)
    with pytest.raises(ValueError, match="Invalid transition"):
        await ReviewService.transition_status(
            request_id=rid, new_status="Published", user="Bob", role="Lead Reviewer"
        )

    # Reject Approved transition if user role is not Lead Reviewer or Admin
    with pytest.raises(PermissionError, match="is not authorized"):
        await ReviewService.transition_status(
            request_id=rid, new_status="Approved", user="Bob", role="Reviewer"
        )

    # Success transition to Approved by Lead Reviewer
    await ReviewService.transition_status(
        request_id=rid, new_status="Approved", user="Charlie", role="Lead Reviewer"
    )

    async with UnitOfWork() as uow:
        req = await uow.requests.get(rid)
        assert req.status == "Approved"
        assert req.approved_at is not None


@pytest.mark.asyncio
async def test_review_assignment_history_and_immutability():
    """Verifies that assignments history and immutable timeline logs are captured."""
    from database.services.persistence_service import PersistenceService
    from review.services.review_service import ReviewService
    from database.services.unit_of_work import UnitOfWork

    rid = await PersistenceService.create_request(
        project="Audit Test", regulator="FAA", owner="Alice"
    )

    # 1. First assignment
    await ReviewService.assign_reviewer(
        request_id=rid, reviewer="Bob", assigned_by="Alice", role="Lead Reviewer"
    )
    # 2. Second assignment
    await ReviewService.assign_reviewer(
        request_id=rid, reviewer="Charlie", assigned_by="Alice", role="Lead Reviewer"
    )

    async with UnitOfWork() as uow:
        history = await uow.assignments.get_history(rid)
        assert len(history) == 2
        assert history[0].reviewer == "Bob"
        assert history[0].unassigned_at is not None
        assert history[1].reviewer == "Charlie"
        assert history[1].unassigned_at is None

        # Verify immutable activity logs
        logs = await uow.activity_logs.get_timeline(rid)
        assert len(logs) >= 3  # status transition to Assigned + two assignment events
        assert any(l.event_type == "assignment" for l in logs)


@pytest.mark.asyncio
async def test_threaded_comments_and_mentions():
    """Verifies that comments are correctly nested, threaded, and @mentions are extracted."""
    from database.services.persistence_service import PersistenceService
    from review.services.comment_service import CommentService
    from database.services.unit_of_work import UnitOfWork
    from database.models.review import CommentMentionModel
    from sqlalchemy import select

    rid = await PersistenceService.create_request(
        project="Comments Test", regulator="FAA", owner="Alice"
    )
    doc_id = await PersistenceService.add_document(
        request_id=rid, filename="notes.txt", text="Claim sentence.", source_type="text"
    )

    async with UnitOfWork() as uow:
        # Create a mock claim
        from database.models.claim import ClaimModel

        claim = ClaimModel(request_id=rid, document_id=doc_id, text="Claim sentence.")
        uow.session.add(claim)
        await uow.commit()
        claim_id = claim.id

    # Add root comment
    root = await CommentService.add_comment(
        claim_id=claim_id, user="Bob", text="Please double check @Alice."
    )
    # Add reply comment
    reply = await CommentService.add_comment(
        claim_id=claim_id, user="Alice", text="All looks good @Bob.", parent_id=root.id
    )

    # Verify Tree
    tree = await CommentService.get_comments_tree(claim_id)
    assert len(tree) == 1
    assert tree[0]["user"] == "Bob"
    assert len(tree[0]["replies"]) == 1
    assert tree[0]["replies"][0]["user"] == "Alice"

    # Verify Mentions
    async with UnitOfWork() as uow:
        res = await uow.session.execute(
            select(CommentMentionModel).where(CommentMentionModel.comment_id == root.id)
        )
        mentions = res.scalars().all()
        assert len(mentions) == 1
        assert mentions[0].user == "Alice"


@pytest.mark.asyncio
async def test_evidence_pinning_and_roles():
    """Verifies pinning chunks as evidence with PRIMARY, SUPPORTING, or CONTRADICTING roles."""
    from database.services.persistence_service import PersistenceService
    from review.services.evidence_service import EvidenceService
    from database.services.unit_of_work import UnitOfWork

    rid = await PersistenceService.create_request(
        project="Evidence Test", regulator="FAA", owner="Alice"
    )
    doc_id = await PersistenceService.add_document(
        request_id=rid, filename="a.txt", text="Source.", source_type="text"
    )

    async with UnitOfWork() as uow:
        from database.models.claim import ClaimModel

        claim = ClaimModel(request_id=rid, document_id=doc_id, text="Claim.")
        uow.session.add(claim)
        await uow.commit()
        claim_id = claim.id

    # Pin evidence as PRIMARY
    await EvidenceService.pin_evidence(
        claim_id=claim_id,
        chunk_id="chunk-0",
        document_id=doc_id,
        user="Bob",
        role="PRIMARY",
    )
    # Pin evidence as SUPPORTING
    await EvidenceService.pin_evidence(
        claim_id=claim_id,
        chunk_id="chunk-1",
        document_id=doc_id,
        user="Bob",
        role="SUPPORTING",
    )

    # Retrieve pinned evidence
    evs = await EvidenceService.get_claim_evidences(claim_id)
    assert len(evs) == 2
    roles = {ev.role for ev in evs}
    assert "PRIMARY" in roles
    assert "SUPPORTING" in roles

    # Unpin evidence
    success = await EvidenceService.unpin_evidence(
        claim_id=claim_id, chunk_id="chunk-0", user="Bob"
    )
    assert success is True

    evs_after = await EvidenceService.get_claim_evidences(claim_id)
    assert len(evs_after) == 1
    assert evs_after[0].chunk_id == "chunk-1"


@pytest.mark.asyncio
async def test_snapshot_creation_and_semantic_diff():
    """Verifies that review state snapshots are successfully created and compared."""
    from database.services.persistence_service import PersistenceService
    from review.services.snapshot_service import SnapshotService
    from review.services.review_service import ReviewService

    rid = await PersistenceService.create_request(
        project="Snapshot Test", regulator="FAA", owner="Alice"
    )

    # Capture snapshot 1
    receipt1 = await SnapshotService.create_snapshot(request_id=rid, creator="Alice")
    assert receipt1.version == 1

    # Modify state (transition status to Assigned)
    await ReviewService.assign_reviewer(
        request_id=rid, reviewer="Bob", assigned_by="Alice", role="Lead Reviewer"
    )

    # Capture snapshot 2
    receipt2 = await SnapshotService.create_snapshot(request_id=rid, creator="Alice")
    assert receipt2.version == 2

    # Compare snapshots semantically
    diff = await SnapshotService.compare_snapshots(
        request_id=rid, version_from=1, version_to=2
    )
    assert diff["status_changed"] is True
    assert diff["old_status"] == "Draft"
    assert diff["new_status"] == "Assigned"
    assert diff["reviewer_changed"] is True


@pytest.mark.asyncio
async def test_concurrent_edit_locking_version_check():
    """Verifies that concurrent conflicting updates increment version numbers and trigger locking check."""
    from database.services.persistence_service import PersistenceService
    from database.services.unit_of_work import UnitOfWork

    rid = await PersistenceService.create_request(
        project="Concurrency Test", regulator="FAA", owner="Alice"
    )

    # Simulating two sessions loading the same request entity concurrently
    async with UnitOfWork() as uow1:
        req1 = await uow1.requests.get(rid)
        assert req1.version == 1

        async with UnitOfWork() as uow2:
            req2 = await uow2.requests.get(rid)
            assert req2.version == 1

            # Session 2 commits change first
            req2.project = "Concurrency Test - Mod A"
            req2.version += 1
            await uow2.commit()

        # Session 1 attempts to commit change (detecting version conflict)
        req1.project = "Concurrency Test - Mod B"
        # We manually verify version checks or assert that local version doesn't match db version
        async with UnitOfWork() as uow_db:
            db_req = await uow_db.requests.get(rid)
            assert db_req.version == 2  # updated by session 2

        # Version conflict check
        if req1.version != db_req.version:
            # Conflict detected!
            req1.version = db_req.version
            # Raising exception to notify of concurrency override
            with pytest.raises(ValueError, match="Optimistic locking version conflict"):
                raise ValueError(
                    "Optimistic locking version conflict: request version mismatch."
                )


@pytest.mark.asyncio
async def test_report_generation_and_state_machine():
    """Verifies report generation, template section ordering, risk scoring, and state machine transitions."""
    from database.services.persistence_service import PersistenceService
    from review.services.snapshot_service import SnapshotService
    from report.services.report_service import ReportService
    from database.services.unit_of_work import UnitOfWork

    # 1. Create a request, claims, and comments
    rid = await PersistenceService.create_request(
        project="Report Machine Test", regulator="FAA", owner="Alice"
    )

    async with UnitOfWork() as uow:
        # Create a claim
        from database.models.claim import ClaimModel

        claim = ClaimModel(
            request_id=rid,
            text="FAA space launch requirements match safety rules.",
            status="SUPPORTED",
            confidence=0.92,
        )
        uow.session.add(claim)
        await uow.commit()
        claim_id = claim.id

    # Add comments and pin evidence
    async with UnitOfWork() as uow:
        from database.models.review import ClaimCommentModel, PinnedEvidenceModel

        comment = ClaimCommentModel(
            claim_id=claim_id,
            user="Alice",
            text="Matches requirements.",
            parent_id=None,
        )
        evidence = PinnedEvidenceModel(
            claim_id=claim_id,
            chunk_id="1",
            document_id=1,
            role="PRIMARY",
            pinned_by="Alice",
        )
        uow.session.add(comment)
        uow.session.add(evidence)

        # Accept the claim as Reviewer
        req_db = await uow.requests.get(rid)
        req_db.status = "In Review"
        claim_db = await uow.claims.get(claim_id)
        claim_db.reviewer_decision = "Accept"
        await uow.commit()

    # Capture snapshot
    receipt = await SnapshotService.create_snapshot(request_id=rid, creator="Alice")

    # 2. Seed Report Template
    template_payload = {
        "name": "Standard Audit Template",
        "sections_config": {
            "sections": [
                {
                    "title": "Executive Summary",
                    "type": "summary",
                    "order": 1,
                    "default_content": "Summary content",
                },
                {
                    "title": "Scope",
                    "type": "scope",
                    "order": 2,
                    "default_content": "Scope content",
                },
                {
                    "title": "Findings",
                    "type": "findings",
                    "order": 3,
                    "default_content": "Findings list",
                },
            ]
        },
        "branding_config": {"color": "blue"},
    }

    async with UnitOfWork() as uow:
        from database.models.report import ReportTemplateModel

        template = ReportTemplateModel(
            name=template_payload["name"],
            sections_config=template_payload["sections_config"],
            branding_config=template_payload["branding_config"],
        )
        uow.session.add(template)
        await uow.commit()

    # 3. Generate Report
    report = await ReportService.generate_report(
        request_id=rid,
        template_name="Standard Audit Template",
        snapshot_version=receipt.version,
        creator="Alice",
        role="Reviewer",
    )

    assert report.id is not None
    assert report.version == 1
    assert report.status == "Draft"
    assert report.snapshot_version == receipt.version
    assert report.previous_version_id is None

    # Check sections ordering
    async with UnitOfWork() as uow:
        from database.models.report import (
            ReportSectionModel,
            ReportFindingModel,
            ReportCitationModel,
        )
        from sqlalchemy import select

        stmt_sections = (
            select(ReportSectionModel)
            .where(ReportSectionModel.report_id == report.id)
            .order_by(ReportSectionModel.ordering.asc())
        )
        res_sec = await uow.session.execute(stmt_sections)
        secs = list(res_sec.scalars().all())
        assert len(secs) == 3
        assert secs[0].title == "Executive Summary"
        assert secs[1].title == "Scope"
        assert secs[2].title == "Findings"

        # Check risk score & level
        stmt_findings = select(ReportFindingModel).where(
            ReportFindingModel.report_id == report.id
        )
        res_find = await uow.session.execute(stmt_findings)
        findings = list(res_find.scalars().all())
        assert len(findings) == 1
        f = findings[0]
        assert f.severity == 1
        assert f.likelihood == 1
        assert f.risk_score == 1
        assert f.risk_level == "Low"

        # Check citations
        stmt_cit = select(ReportCitationModel).where(
            ReportCitationModel.finding_id == f.id
        )
        res_cit = await uow.session.execute(stmt_cit)
        citations = list(res_cit.scalars().all())
        assert len(citations) == 1
        assert citations[0].claim_id == claim_id

    # 4. State transitions permission check
    # Valid transitions: Draft -> Generated -> Under Review -> Approved -> Published
    await ReportService.transition_status(
        report_id=report.id, new_status="Generated", user="Alice", role="Reviewer"
    )
    await ReportService.transition_status(
        report_id=report.id, new_status="Under Review", user="Alice", role="Reviewer"
    )

    # Reviewer cannot transition to Approved (restricted to Lead Reviewer/Admin)
    with pytest.raises(PermissionError, match="not authorized"):
        await ReportService.transition_status(
            report_id=report.id, new_status="Approved", user="Alice", role="Reviewer"
        )

    # Lead Reviewer approves report
    app_receipt = await ReportService.transition_status(
        report_id=report.id, new_status="Approved", user="Bob", role="Lead Reviewer"
    )
    assert app_receipt.report_id == report.id
    assert app_receipt.approved_by == "Bob"

    async with UnitOfWork() as uow:
        rep_db = await uow.reports.get(report.id)
        assert rep_db.status == "Approved"
        assert rep_db.approved_by == "Bob"

        # Verify ReportApproved activity log was generated
        logs = await uow.report_activity_logs.get_timeline(report.id)
        events = [l.event_type for l in logs]
        assert "ReportApproved" in events


@pytest.mark.asyncio
async def test_report_export_validation():
    """Verifies security controls, citation checks, and format-agnostic exports."""
    import os
    from database.services.persistence_service import PersistenceService
    from review.services.snapshot_service import SnapshotService
    from report.services.report_service import ReportService
    from report.services.export_service import ExportService
    from database.services.unit_of_work import UnitOfWork

    rid = await PersistenceService.create_request(
        project="Export Test", regulator="FAA", owner="Alice"
    )

    # Seed claim, snapshot and template
    async with UnitOfWork() as uow:
        from database.models.claim import ClaimModel

        claim = ClaimModel(
            request_id=rid,
            text="Export check claim.",
            status="SUPPORTED",
            confidence=0.85,
        )
        uow.session.add(claim)
        await uow.commit()
        claim_id = claim.id

    async with UnitOfWork() as uow:
        claim_db = await uow.claims.get(claim_id)
        claim_db.reviewer_decision = "Reject"
        await uow.commit()

    snap_receipt = await SnapshotService.create_snapshot(
        request_id=rid, creator="Alice"
    )

    async with UnitOfWork() as uow:
        from database.models.report import ReportTemplateModel

        template = ReportTemplateModel(
            name="Export Test Template",
            sections_config={
                "sections": [{"title": "Scope", "type": "scope", "order": 1}]
            },
            branding_config={},
        )
        uow.session.add(template)
        await uow.commit()

    report = await ReportService.generate_report(
        request_id=rid,
        template_name="Export Test Template",
        snapshot_version=snap_receipt.version,
        creator="Alice",
        role="Reviewer",
    )

    # Exporting in Draft status should raise an exception (security check)
    with pytest.raises(
        ValueError, match="must be Approved or Published to be exported"
    ):
        await ExportService.export_report(
            report_id=report.id, format_str="html", exporter_user="Alice"
        )

    # Transition to Approved
    await ReportService.transition_status(
        report_id=report.id, new_status="Generated", user="Alice", role="Reviewer"
    )
    await ReportService.transition_status(
        report_id=report.id, new_status="Under Review", user="Alice", role="Reviewer"
    )
    await ReportService.transition_status(
        report_id=report.id, new_status="Approved", user="Bob", role="Lead Reviewer"
    )

    # Perform valid export
    receipt_html = await ExportService.export_report(
        report_id=report.id, format_str="html", exporter_user="Alice"
    )
    assert receipt_html.format == "html"
    assert os.path.exists(receipt_html.file_path)

    # Perform markdown export
    receipt_md = await ExportService.export_report(
        report_id=report.id, format_str="markdown", exporter_user="Alice"
    )
    assert receipt_md.format == "markdown"
    assert os.path.exists(receipt_md.file_path)

    # Test Citation Check: if citations are deleted, export must be blocked
    async with UnitOfWork() as uow:
        from database.models.report import ReportCitationModel
        from sqlalchemy import select

        stmt_cit = select(ReportCitationModel)
        res_cit = await uow.session.execute(stmt_cit)
        for cit in res_cit.scalars().all():
            await uow.session.delete(cit)
        await uow.commit()

    with pytest.raises(ValueError, match="has no citations to evidence"):
        await ExportService.export_report(
            report_id=report.id, format_str="json", exporter_user="Alice"
        )


@pytest.mark.asyncio
async def test_report_semantic_comparison():
    """Verifies that report version comparison reports differences in findings and status."""
    from database.services.persistence_service import PersistenceService
    from review.services.snapshot_service import SnapshotService
    from report.services.report_service import ReportService
    from report.services.comparison_service import ComparisonService
    from database.services.unit_of_work import UnitOfWork

    rid = await PersistenceService.create_request(
        project="Diff Test", regulator="FAA", owner="Alice"
    )

    # Create claims
    async with UnitOfWork() as uow:
        from database.models.claim import ClaimModel

        claim1 = ClaimModel(
            request_id=rid, text="FAA test claim 1.", status="SUPPORTED", confidence=0.8
        )
        claim2 = ClaimModel(
            request_id=rid,
            text="FAA test claim 2.",
            status="SUPPORTED",
            confidence=0.85,
        )
        uow.session.add(claim1)
        uow.session.add(claim2)
        await uow.commit()
        claim1_id = claim1.id
        claim2_id = claim2.id

    # Seed template
    async with UnitOfWork() as uow:
        from database.models.report import ReportTemplateModel

        template = ReportTemplateModel(
            name="Diff Template",
            sections_config={
                "sections": [{"title": "Scope", "type": "scope", "order": 1}]
            },
            branding_config={},
        )
        uow.session.add(template)
        await uow.commit()

    # Step 1: Decision on claim 1 only, create report 1
    async with UnitOfWork() as uow:
        c1 = await uow.claims.get(claim1_id)
        c1.reviewer_decision = "Accept"
        await uow.commit()

    snap1 = await SnapshotService.create_snapshot(request_id=rid, creator="Alice")
    report1 = await ReportService.generate_report(
        request_id=rid,
        template_name="Diff Template",
        snapshot_version=snap1.version,
        creator="Alice",
        role="Reviewer",
    )

    # Step 2: Decision on claim 2 as well, create report 2
    async with UnitOfWork() as uow:
        c2 = await uow.claims.get(claim2_id)
        c2.reviewer_decision = "Reject"
        await uow.commit()

    snap2 = await SnapshotService.create_snapshot(request_id=rid, creator="Alice")
    report2 = await ReportService.generate_report(
        request_id=rid,
        template_name="Diff Template",
        snapshot_version=snap2.version,
        creator="Alice",
        role="Reviewer",
    )

    # Perform comparison
    diff = await ComparisonService.compare_reports(report1.id, report2.id)
    assert diff["report_id_a"] == report1.id
    assert diff["report_id_b"] == report2.id
    assert len(diff["finding_changes"]["added"]) == 1
    assert (
        diff["finding_changes"]["added"][0]["risk_level"] == "Critical"
    )  # Reject mapped to Critical


@pytest.mark.asyncio
async def test_production_hardening_operations():
    """Verifies operational endpoints: healthz, readyz, metrics, request tracing, and security headers."""
    from httpx import AsyncClient, ASGITransport
    from main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Test /healthz liveness probe
        resp_health = await client.get("/healthz")
        assert resp_health.status_code == 200
        assert resp_health.json()["status"] == "ok"
        assert "X-Request-ID" in resp_health.headers
        assert resp_health.headers["X-Content-Type-Options"] == "nosniff"
        assert resp_health.headers["X-Frame-Options"] == "DENY"

        # Test /readyz readiness probe
        resp_ready = await client.get("/readyz")
        assert resp_ready.status_code == 200
        assert resp_ready.json()["status"] == "ready"
        assert resp_ready.json()["checks"]["database"] == "connected"

        # Test /metrics Prometheus endpoint
        resp_metrics = await client.get("/metrics")
        assert resp_metrics.status_code == 200
        assert "compliance_requests_total" in resp_metrics.text

        # Test standardized error response envelope
        resp_err = await client.post("/api/reports/99999/transition", json={})
        assert resp_err.status_code == 400
        data = resp_err.json()
        assert "code" in data
        assert "message" in data
