import asyncio
import logging
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import func
from concurrent.futures import ThreadPoolExecutor

from database.services.persistence_service import PersistenceService, LockedError
from database.migration_manager import MigrationManager
from database.bootstrap import bootstrap_database

logger = logging.getLogger("db_sync_wrapper")
_executor = ThreadPoolExecutor(max_workers=8)

class TransitionError(Exception):
    """Raised when a lifecycle transition is attempted from an invalid state."""
    pass

def run_sync(coro):
    """Executes an asynchronous coroutine synchronously, safely handling running event loops."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
        
    def _run():
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()
            
    future = _executor.submit(_run)
    return future.result()

def init_db():
    """Initializes the database schema and upgrades using Alembic migrations."""
    run_sync(bootstrap_database())
    MigrationManager.upgrade_to_head()

def seed_requirements(regulations: list):
    """Seeds regulations requirement corpus into the database."""
    run_sync(PersistenceService.seed_requirements(regulations))

def _now() -> str:
    """Returns ISO format timestamp for database receipts."""
    return datetime.now(timezone.utc).isoformat()

def log_audit(request_id: int, stage: str, detail: str) -> None:
    """Logs an audit log action to requests metadata table."""
    async def _log():
        from database.services.unit_of_work import UnitOfWork
        from database.models.audit import AuditLogModel
        async with UnitOfWork() as uow:
            log_item = AuditLogModel(request_id=request_id, stage=stage, detail=detail)
            await uow.receipts.add(log_item)
            await uow.commit()
    run_sync(_log())

def create_request(project: str, regulator: str, owner: str) -> int:
    """Creates a new request and records an audit log entry."""
    return run_sync(PersistenceService.create_request(project, regulator, owner))

def add_document(request_id: int, filename: str, text: str, source_type: str = "text") -> int:
    """Adds an uploaded document source file text."""
    return run_sync(PersistenceService.add_document(request_id, filename, text, source_type))

def create_run(request_id: int) -> Tuple[int, int]:
    """Generates a new run version metadata."""
    return run_sync(PersistenceService.create_run(request_id))

def finalize_run(run_id: int, request_id: int, summary: str, receipt: dict):
    """Finalizes run results and logs receipt."""
    run_sync(PersistenceService.finalize_run(run_id, request_id, summary, receipt))

def set_status(request_id: int, status: str, detail: str = ""):
    """Modifies the status state of a request."""
    run_sync(PersistenceService.set_status(request_id, status, detail))

def save_claim(request_id: int, run_id: int, document_id: int, result: dict) -> int:
    """Saves verified claim details."""
    return run_sync(PersistenceService.save_claim(request_id, run_id, document_id, result))

def review_claim(claim_id: int, decision: str) -> None:
    """Saves a reviewer's decision on a claim."""
    run_sync(PersistenceService.review_claim(claim_id, decision))

def comment_claim(claim_id: int, comment: str) -> None:
    """Appends a comment to a claim."""
    run_sync(PersistenceService.comment_claim(claim_id, comment))

def resolve_claim(claim_id: int) -> None:
    """Resolves comments on a claim."""
    run_sync(PersistenceService.resolve_claim(claim_id, 1))

def review_queue() -> list:
    """Lists pending claims across requests."""
    async def _queue():
        from sqlalchemy import select
        from database.services.unit_of_work import UnitOfWork
        from database.models.claim import ClaimModel
        from database.models.request import RequestModel
        async with UnitOfWork() as uow:
            stmt = select(ClaimModel, RequestModel.project, RequestModel.regulator)\
                   .join(RequestModel, ClaimModel.request_id == RequestModel.id)\
                   .where(ClaimModel.reviewer_decision == "pending")\
                   .order_by(ClaimModel.request_id.desc(), ClaimModel.id.desc())
            res = await uow.session.execute(stmt)
            rows = res.all()
            results = []
            for claim, project, regulator in rows:
                results.append({
                    "id": claim.id,
                    "request_id": claim.request_id,
                    "run_id": claim.run_id,
                    "document_id": claim.document_id,
                    "text": claim.text,
                    "status": claim.status,
                    "confidence": claim.confidence,
                    "citation": claim.citation,
                    "citation_title": claim.citation_title,
                    "snippet": claim.snippet,
                    "reason": claim.reason,
                    "reviewer_decision": claim.reviewer_decision,
                    "comment": claim.comment,
                    "resolved": claim.resolved,
                    "project": project,
                    "regulator": regulator
                })
            return results
    return run_sync(_queue())

def approve_request(request_id: int) -> None:
    """Approves a request, updating requests and audit_logs tables."""
    async def _approve():
        from sqlalchemy import select
        from database.services.unit_of_work import UnitOfWork
        from database.models.request import RequestModel
        from database.models.run import RunModel
        from database.models.claim import ClaimModel
        from database.models.audit import AuditLogModel
        async with UnitOfWork() as uow:
            req = await uow.requests.get(request_id)
            if not req:
                raise TransitionError("Request not found")
            if req.status != "needs_review":
                raise TransitionError(f"Cannot transition from '{req.status}' — expected needs_review")
            
            stmt = select(RunModel).where(RunModel.request_id == request_id).order_by(RunModel.version.desc()).limit(1)
            res = await uow.session.execute(stmt)
            latest_run = res.scalar()
            if not latest_run:
                raise TransitionError("No pipeline run to approve")
            
            stmt_pending = select(func.count()).select_from(ClaimModel)\
                           .where(ClaimModel.run_id == latest_run.id, ClaimModel.reviewer_decision == "pending")
            res_pending = await uow.session.execute(stmt_pending)
            pending = res_pending.scalar() or 0
            if pending > 0:
                raise TransitionError(f"{pending} claim(s) still pending review")
                
            req.status = "approved"
            req.approved_at = datetime.now(timezone.utc).isoformat() + "Z"
            
            log_item = AuditLogModel(
                request_id=request_id,
                stage="approved",
                detail=f"Request approved on run v{latest_run.version}"
            )
            await uow.receipts.add(log_item)
            await uow.commit()
    run_sync(_approve())

def lock_request(request_id: int) -> None:
    """Locks a request making runs and files immutable."""
    async def _lock():
        from database.services.unit_of_work import UnitOfWork
        from database.models.audit import AuditLogModel
        async with UnitOfWork() as uow:
            req = await uow.requests.get(request_id)
            if not req:
                raise TransitionError("Request not found")
            if req.status != "approved":
                raise TransitionError(f"Cannot transition from '{req.status}' — expected approved")
            
            req.status = "locked"
            req.approved_at = datetime.now(timezone.utc).isoformat() + "Z"
            log_item = AuditLogModel(
                request_id=request_id,
                stage="locked",
                detail="Request locked — claims, evidence, and citations are now immutable"
            )
            await uow.receipts.add(log_item)
            await uow.commit()
    run_sync(_lock())

def submit_request(request_id: int) -> None:
    """Submits a locked request."""
    async def _submit():
        from database.services.unit_of_work import UnitOfWork
        from database.models.audit import AuditLogModel
        async with UnitOfWork() as uow:
            req = await uow.requests.get(request_id)
            if not req:
                raise TransitionError("Request not found")
            if req.status != "locked":
                raise TransitionError(f"Cannot transition from '{req.status}' — expected locked")
            
            req.status = "submitted"
            log_item = AuditLogModel(
                request_id=request_id,
                stage="submitted",
                detail="Request submitted"
            )
            await uow.receipts.add(log_item)
            await uow.commit()
    run_sync(_submit())

def archive_request(request_id: int) -> None:
    """Archives a submitted request."""
    async def _archive():
        from database.services.unit_of_work import UnitOfWork
        from database.models.audit import AuditLogModel
        async with UnitOfWork() as uow:
            req = await uow.requests.get(request_id)
            if not req:
                raise TransitionError("Request not found")
            if req.status != "submitted":
                raise TransitionError(f"Cannot transition from '{req.status}' — expected submitted")
            
            req.status = "archived"
            log_item = AuditLogModel(
                request_id=request_id,
                stage="archived",
                detail="Request archived"
            )
            await uow.receipts.add(log_item)
            await uow.commit()
    run_sync(_archive())

def reopen_request(request_id: int) -> None:
    """Reopens a request reverting approved status to needs_review."""
    async def _reopen():
        from database.services.unit_of_work import UnitOfWork
        from database.models.audit import AuditLogModel
        async with UnitOfWork() as uow:
            req = await uow.requests.get(request_id)
            if not req:
                raise TransitionError("Request not found")
            if req.status != "approved":
                raise TransitionError(f"Cannot transition from '{req.status}' — expected approved")
            
            req.status = "needs_review"
            req.approved_at = None
            log_item = AuditLogModel(
                request_id=request_id,
                stage="reopened",
                detail="Approval reverted — back to needs_review"
            )
            await uow.receipts.add(log_item)
            await uow.commit()
    run_sync(_reopen())

def dashboard_stats() -> dict:
    """Compiles dashboard usage statistics."""
    async def _stats():
        from sqlalchemy import select, func, not_
        from database.services.unit_of_work import UnitOfWork
        from database.models.request import RequestModel
        from database.models.claim import ClaimModel
        from database.models.run import RunModel
        async with UnitOfWork() as uow:
            stmt_open = select(func.count()).select_from(RequestModel)\
                        .where(not_(RequestModel.status.in_(["submitted", "archived"])))
            res_open = await uow.session.execute(stmt_open)
            open_requests = res_open.scalar() or 0

            stmt_pending = select(func.count()).select_from(ClaimModel)\
                           .where(ClaimModel.reviewer_decision == "pending")
            res_pending = await uow.session.execute(stmt_pending)
            needs_review = res_pending.scalar() or 0

            stmt_tot_req = select(func.count()).select_from(RequestModel)
            res_tot_req = await uow.session.execute(stmt_tot_req)
            total_requests = res_tot_req.scalar() or 0

            stmt_tot_runs = select(func.count()).select_from(RunModel)
            res_tot_runs = await uow.session.execute(stmt_tot_runs)
            total_runs = res_tot_runs.scalar() or 0

            stmt_locked = select(func.count()).select_from(RequestModel).where(RequestModel.status == "locked")
            res_locked = await uow.session.execute(stmt_locked)
            locked_requests = res_locked.scalar() or 0

            stmt_sub = select(func.count()).select_from(RequestModel).where(RequestModel.status == "submitted")
            res_sub = await uow.session.execute(stmt_sub)
            submitted_requests = res_sub.scalar() or 0

            stmt_latest_run = select(RunModel.version).order_by(RunModel.id.desc()).limit(1)
            res_latest_run = await uow.session.execute(stmt_latest_run)
            latest_run_v = res_latest_run.scalar()
            latest_run = f"v{latest_run_v}" if latest_run_v else "—"

            stmt_recent = select(RequestModel).order_by(RequestModel.id.desc()).limit(5)
            res_recent = await uow.session.execute(stmt_recent)
            recent_activity = [
                {
                    "id": r.id,
                    "project": r.project,
                    "status": r.status,
                    "regulator": r.regulator,
                    "created_at": r.created_at.isoformat() + "Z"
                } for r in res_recent.scalars().all()
            ]
            return {
                "open_requests": open_requests,
                "needs_review": needs_review,
                "total_requests": total_requests,
                "total_runs": total_runs,
                "locked_requests": locked_requests,
                "submitted_requests": submitted_requests,
                "latest_run": latest_run,
                "recent_activity": recent_activity
            }
    return run_sync(_stats())

def report_for_request(request_id: int) -> dict:
    """Executive summary combining coverage, latest receipt, and open risks."""
    async def _report():
        import json as _json
        from sqlalchemy import select
        from database.services.unit_of_work import UnitOfWork
        from database.models.run import RunModel
        async with UnitOfWork() as uow:
            data = await PersistenceService.get_request(request_id)
            if not data:
                return None
                
            stmt_run = select(RunModel).where(RunModel.request_id == request_id).order_by(RunModel.version.desc()).limit(1)
            res_run = await uow.session.execute(stmt_run)
            latest_run = res_run.scalar()
            
            receipt = _json.loads(latest_run.receipt) if latest_run and latest_run.receipt else None
            coverage = await PersistenceService.coverage_for_request(request_id)
            
            latest_run_id = latest_run.id if latest_run else None
            latest_claims = [c for c in data["claims"] if c["run_id"] == latest_run_id]
            
            open_risks = [c for c in latest_claims if c["status"] in ("UNSUPPORTED", "PARTIAL")]
            unresolved_comments = [c for c in latest_claims if c["comment"] and not c["resolved"]]
            
            recommendations = []
            for c in open_risks:
                if c["status"] == "UNSUPPORTED":
                    recommendations.append(f"Add supporting evidence or a valid citation for: \"{c['text'][:80]}\"")
                else:
                    recommendations.append(f"Strengthen evidence for partially-supported claim: \"{c['text'][:80]}\"")
                      
            return {
                "request": data,
                "version": latest_run.version if latest_run else None,
                "summary": latest_run.summary if latest_run else "No runs yet.",
                "coverage": coverage,
                "open_risks": [{"claim": c["text"], "status": c["status"], "reason": c["reason"]} for c in open_risks],
                "unresolved_comments": [{"claim": c["text"], "comment": c["comment"]} for c in unresolved_comments],
                "recommendations": recommendations,
                "receipt": receipt,
                "audit_log": data["audit_log"]
            }
    return run_sync(_report())

def get_request(request_id: int) -> dict:
    """Fetches details of a single request."""
    return run_sync(PersistenceService.get_request(request_id))

def list_requests() -> list:
    """Lists requests."""
    return run_sync(PersistenceService.list_requests())

def graph_for_request(request_id: int) -> dict:
    """Constructs request claim-citations relationship graph."""
    return run_sync(PersistenceService.graph_for_request(request_id))

def requirement_dependents(reg_id: str) -> list:
    """Finds claims depending on a requirement."""
    return run_sync(PersistenceService.requirement_dependents(reg_id))

def coverage_for_request(request_id: int) -> dict:
    """Calculates coverage stats for a request."""
    return run_sync(PersistenceService.coverage_for_request(request_id))

def diff_runs(request_id: int, from_version: int, to_version: int) -> dict:
    """Diffs claim statuses between versions."""
    return run_sync(PersistenceService.diff_runs(request_id, from_version, to_version))
