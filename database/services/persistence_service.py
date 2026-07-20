import json
import datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy import select, func
from database.services.unit_of_work import UnitOfWork
from database.models.request import RequestModel
from database.models.document import DocumentModel
from database.models.run import RunModel
from database.models.claim import ClaimModel
from database.models.audit import AuditLogModel
from database.models.requirement import RequirementModel

LOCKED_STATUSES = ("locked", "submitted", "archived")

class LockedError(Exception):
    pass

class PersistenceService:
    """Async service facade orchestrating transactional database operations across UOW repositories."""

    @staticmethod
    async def _assert_not_locked(uow: UnitOfWork, request_id: int) -> None:
        req = await uow.requests.get(request_id)
        if req and req.status in LOCKED_STATUSES:
            raise LockedError(f"Request is {req.status} and can no longer be modified")

    @staticmethod
    async def create_request(project: str, regulator: str, owner: str) -> int:
        async with UnitOfWork() as uow:
            req = RequestModel(project=project, regulator=regulator, owner=owner)
            await uow.requests.add(req)
            await uow.commit()
            
            log_item = AuditLogModel(
                request_id=req.id, 
                stage="created", 
                detail=f"Request created for project '{project}' under {regulator}"
            )
            await uow.receipts.add(log_item)
            await uow.commit()
            return req.id

    @staticmethod
    async def list_requests() -> List[dict]:
        async with UnitOfWork() as uow:
            # Query all requests order by id
            stmt = select(RequestModel).order_by(RequestModel.id)
            res = await uow.session.execute(stmt)
            requests = res.scalars().all()
            return [
                {
                    "id": r.id,
                    "project": r.project,
                    "regulator": r.regulator,
                    "status": r.status,
                    "owner": r.owner,
                    "created_at": r.created_at.isoformat() + "Z"
                } for r in requests
            ]

    @staticmethod
    async def get_request(request_id: int) -> Optional[dict]:
        async with UnitOfWork() as uow:
            req = await uow.requests.get(request_id)
            if not req:
                return None
            
            # Documents
            stmt_doc = select(DocumentModel).where(DocumentModel.request_id == request_id).order_by(DocumentModel.id)
            res_doc = await uow.session.execute(stmt_doc)
            documents = res_doc.scalars().all()

            # Runs
            stmt_run = select(RunModel).where(RunModel.request_id == request_id).order_by(RunModel.id)
            res_run = await uow.session.execute(stmt_run)
            runs = res_run.scalars().all()

            # Claims
            stmt_claim = select(ClaimModel).where(ClaimModel.request_id == request_id).order_by(ClaimModel.run_id, ClaimModel.id)
            res_claim = await uow.session.execute(stmt_claim)
            claims = res_claim.scalars().all()

            # Audit log
            stmt_audit = select(AuditLogModel).where(AuditLogModel.request_id == request_id).order_by(AuditLogModel.id)
            res_audit = await uow.session.execute(stmt_audit)
            audit_logs = res_audit.scalars().all()

            return {
                "request": {
                    "id": req.id,
                    "project": req.project,
                    "regulator": req.regulator,
                    "status": req.status,
                    "owner": req.owner,
                    "created_at": req.created_at.isoformat() + "Z",
                    "approved_at": req.approved_at,
                },
                "documents": [
                    {
                        "id": d.id,
                        "request_id": d.request_id,
                        "filename": d.filename,
                        "text": d.text,
                        "source_type": d.source_type
                    } for d in documents
                ],
                "runs": [
                    {
                        "id": rn.id,
                        "request_id": rn.request_id,
                        "version": rn.version,
                        "created_at": rn.created_at.isoformat() + "Z",
                        "summary": rn.summary,
                        "receipt": json.loads(rn.receipt) if rn.receipt else None
                    } for rn in runs
                ],
                "claims": [
                    {
                        "id": c.id,
                        "request_id": c.request_id,
                        "run_id": c.run_id,
                        "document_id": c.document_id,
                        "text": c.text,
                        "status": c.status,
                        "confidence": c.confidence,
                        "citation": c.citation,
                        "citation_title": c.citation_title,
                        "snippet": c.snippet,
                        "reason": c.reason,
                        "reviewer_decision": c.reviewer_decision,
                        "comment": c.comment,
                        "resolved": c.resolved
                    } for c in claims
                ],
                "audit_log": [
                    {
                        "id": a.id,
                        "request_id": a.request_id,
                        "stage": a.stage,
                        "detail": a.detail,
                        "created_at": a.created_at.isoformat() + "Z"
                    } for a in audit_logs
                ]
            }

    @staticmethod
    async def add_document(request_id: int, filename: str, text: str, source_type: str = "text") -> int:
        from database.models.outbox import OutboxEventModel
        async with UnitOfWork() as uow:
            await PersistenceService._assert_not_locked(uow, request_id)
            doc = DocumentModel(request_id=request_id, filename=filename, text=text, source_type=source_type)
            await uow.documents.add(doc)
            await uow.commit()

            log_item = AuditLogModel(
                request_id=request_id,
                stage="document_uploaded",
                detail=f"{filename} ({source_type}, {len(text)} chars)"
            )
            await uow.receipts.add(log_item)

            event = OutboxEventModel(
                event_type="document_uploaded",
                payload={
                    "request_id": request_id,
                    "document_id": doc.id,
                    "filename": filename,
                    "source_type": source_type
                }
            )
            uow.session.add(event)

            await uow.commit()
            return doc.id

    @staticmethod
    async def seed_requirements(regulations: List[dict]) -> None:
        async with UnitOfWork() as uow:
            for r in regulations:
                req = await uow.requirements.get(r["id"])
                if not req:
                    req = RequirementModel(reg_id=r["id"], title=r["title"], text=r["text"])
                    await uow.requirements.add(req)
            await uow.commit()

    @staticmethod
    async def create_run(request_id: int) -> Tuple[int, int]:
        async with UnitOfWork() as uow:
            await PersistenceService._assert_not_locked(uow, request_id)
            stmt = select(func.max(RunModel.version)).where(RunModel.request_id == request_id)
            res = await uow.session.execute(stmt)
            max_v = res.scalar() or 0
            version = max_v + 1

            rn = RunModel(request_id=request_id, version=version)
            await uow.runs.add(rn)
            await uow.commit()

            log_item = AuditLogModel(
                request_id=request_id,
                stage="run_started",
                detail=f"Run v{version} started"
            )
            await uow.receipts.add(log_item)
            await uow.commit()
            return rn.id, version

    @staticmethod
    async def finalize_run(run_id: int, request_id: int, summary: str, receipt: dict) -> None:
        async with UnitOfWork() as uow:
            rn = await uow.runs.get(run_id)
            if rn:
                rn.summary = summary
                rn.receipt = json.dumps(receipt)
                
                log_item = AuditLogModel(
                    request_id=request_id,
                    stage="run_finalized",
                    detail=f"Run {run_id} receipt recorded ({receipt.get('claim_count', 0)} claims)"
                )
                await uow.receipts.add(log_item)
                await uow.commit()

    @staticmethod
    async def save_claim(request_id: int, run_id: int, document_id: int, c: dict) -> int:
        async with UnitOfWork() as uow:
            claim = ClaimModel(
                request_id=request_id,
                run_id=run_id,
                document_id=document_id,
                text=c["claim"],
                status=c["status"],
                confidence=c["confidence"],
                citation=c["citation"],
                citation_title=c["citation_title"],
                snippet=c["snippet"],
                reason=c["reason"],
                reviewer_decision="pending"
            )
            await uow.claims.add(claim)
            await uow.commit()
            return claim.id

    @staticmethod
    async def review_claim(claim_id: int, decision: str) -> None:
        async with UnitOfWork() as uow:
            c = await uow.claims.get(claim_id)
            if c:
                await PersistenceService._assert_not_locked(uow, c.request_id)
                c.reviewer_decision = decision
                
                log_item = AuditLogModel(
                    request_id=c.request_id,
                    stage="claim_reviewed",
                    detail=f"Claim {claim_id} reviewed: {decision}"
                )
                await uow.receipts.add(log_item)
                await uow.commit()

    @staticmethod
    async def comment_claim(claim_id: int, comment: str) -> None:
        async with UnitOfWork() as uow:
            c = await uow.claims.get(claim_id)
            if c:
                await PersistenceService._assert_not_locked(uow, c.request_id)
                c.comment = comment
                await uow.commit()

    @staticmethod
    async def resolve_claim(claim_id: int, resolved: int) -> None:
        async with UnitOfWork() as uow:
            c = await uow.claims.get(claim_id)
            if c:
                await PersistenceService._assert_not_locked(uow, c.request_id)
                c.resolved = resolved
                await uow.commit()

    @staticmethod
    async def set_status(request_id: int, status: str, detail: str) -> None:
        async with UnitOfWork() as uow:
            req = await uow.requests.get(request_id)
            if req:
                req.status = status
                if status == "approved":
                    req.approved_at = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"
                
                log_item = AuditLogModel(
                    request_id=request_id,
                    stage="status_changed",
                    detail=detail
                )
                await uow.receipts.add(log_item)
                await uow.commit()

    @staticmethod
    async def graph_for_request(request_id: int) -> dict:
        async with UnitOfWork() as uow:
            stmt = select(ClaimModel).where(ClaimModel.request_id == request_id).order_by(ClaimModel.run_id, ClaimModel.id)
            res = await uow.session.execute(stmt)
            claims = res.scalars().all()
            
            reg_ids = sorted({c.citation for c in claims if c.citation and c.citation != "—"})
            reqs = {}
            for rid_ in reg_ids:
                req = await uow.requirements.get(rid_)
                if req:
                    reqs[rid_] = req

            nodes = []
            edges = []
            for reg_id, r in reqs.items():
                nodes.append({"id": reg_id, "type": "requirement", "label": r.title})
            for c in claims:
                claim_node = f"claim-{c.id}"
                nodes.append({"id": claim_node, "type": "claim", "label": c.text[:60], "status": c.status})
                if c.citation and c.citation != "—":
                    edges.append({
                        "from": claim_node, "to": c.citation,
                        "type": "SATISFIES" if c.status == "SUPPORTED" else "PARTIALLY_SATISFIES" if c.status == "PARTIAL" else "UNSUPPORTED_BY",
                    })
                edges.append({"from": claim_node, "to": claim_node, "type": "REVIEW_STATUS", "detail": c.reviewer_decision})
            return {"nodes": nodes, "edges": edges}

    @staticmethod
    async def coverage_for_request(request_id: int) -> dict:
        async with UnitOfWork() as uow:
            # Get latest run
            stmt_run = select(RunModel).where(RunModel.request_id == request_id).order_by(RunModel.version.desc()).limit(1)
            res_run = await uow.session.execute(stmt_run)
            latest_run = res_run.scalar()
            if not latest_run:
                return {"version": None, "total_requirements": 0, "covered": 0, "missing": [], "rows": []}

            # Get claims for latest run
            stmt = select(ClaimModel).where(ClaimModel.request_id == request_id, ClaimModel.run_id == latest_run.id).order_by(ClaimModel.id)
            res = await uow.session.execute(stmt)
            claims = res.scalars().all()
            
            # Get requirements
            stmt_req = select(RequirementModel)
            res_req = await uow.session.execute(stmt_req)
            all_reqs = res_req.scalars().all()
            
            covered_ids = {c.citation for c in claims if c.status == "SUPPORTED"}
            rows = []
            for r in all_reqs:
                matching = [c for c in claims if c.citation == r.reg_id]
                status = "PASS" if r.reg_id in covered_ids else ("WARNING" if matching else "NO_CLAIM")
                rows.append({"reg_id": r.reg_id, "title": r.title, "status": status, "claim_count": len(matching)})
                
            return {
                "version": latest_run.version,
                "total_requirements": len(all_reqs),
                "covered": len(covered_ids),
                "missing": [r.reg_id for r in all_reqs if r.reg_id not in covered_ids],
                "rows": rows
            }

    @staticmethod
    async def requirement_dependents(reg_id: str) -> list:
        async with UnitOfWork() as uow:
            stmt = select(ClaimModel).where(ClaimModel.citation == reg_id).order_by(ClaimModel.id)
            res = await uow.session.execute(stmt)
            claims = res.scalars().all()
            return [
                {
                    "request_id": c.request_id,
                    "claim_id": c.id,
                    "text": c.text,
                    "status": c.status,
                    "decision": c.reviewer_decision
                } for c in claims
            ]

    @staticmethod
    async def diff_runs(request_id: int, from_version: int, to_version: int) -> dict:
        async with UnitOfWork() as uow:
            stmt_from = select(RunModel).where(RunModel.request_id == request_id, RunModel.version == from_version)
            res_from = await uow.session.execute(stmt_from)
            r_from = res_from.scalar()
            
            stmt_to = select(RunModel).where(RunModel.request_id == request_id, RunModel.version == to_version)
            res_to = await uow.session.execute(stmt_to)
            r_to = res_to.scalar()

            if not r_from or not r_to:
                return {"added": [], "removed": [], "changed": []}

            stmt_c_from = select(ClaimModel).where(ClaimModel.run_id == r_from.id)
            res_c_from = await uow.session.execute(stmt_c_from)
            claims_from = res_c_from.scalars().all()

            stmt_c_to = select(ClaimModel).where(ClaimModel.run_id == r_to.id)
            res_c_to = await uow.session.execute(stmt_c_to)
            claims_to = res_c_to.scalars().all()

            map_from = {c.text: c for c in claims_from}
            map_to = {c.text: c for c in claims_to}

            added = []
            removed = []
            changed = []

            for text, c_to in map_to.items():
                if text not in map_from:
                    added.append({"claim": text, "status": c_to.status})
                else:
                    c_from = map_from[text]
                    if c_from.status != c_to.status or c_from.citation != c_to.citation:
                        changed.append({
                            "claim": text,
                            "old_status": c_from.status,
                            "new_status": c_to.status,
                            "old_citation": c_from.citation,
                            "new_citation": c_to.citation
                        })

            for text, c_from in map_from.items():
                if text not in map_to:
                    removed.append({"claim": text, "status": c_from.status})

            return {"added": added, "removed": removed, "changed": changed}
