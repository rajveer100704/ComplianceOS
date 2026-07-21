import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from database.services.unit_of_work import UnitOfWork
from database.models.review import ReviewSnapshotModel, ReviewActivityLogModel
from review.receipts.snapshot import SnapshotReceipt
from review.events import ReviewEventPublisher
from retrieval.container import Container

logger = logging.getLogger("snapshot_service")


class SnapshotService:
    """Orchestrates review snapshot creations, background queues, and semantic diff engines."""

    @staticmethod
    async def create_snapshot_async(request_id: int, creator: str) -> str:
        """Enqueues a background worker task to generate the review snapshot asynchronously."""
        from worker.state import TaskStateManager

        backend = Container.get_queue_backend()
        import uuid

        job_id = f"snapshot-{request_id}-{uuid.uuid4().hex[:8]}"
        await TaskStateManager.create_task(job_id, "create_snapshot_task")
        await backend.enqueue(
            job_id,
            "create_snapshot_task",
            task_id=job_id,
            request_id=request_id,
            creator=creator,
        )
        return job_id

    @staticmethod
    async def create_snapshot(request_id: int, creator: str) -> SnapshotReceipt:
        """Creates a database snapshot of the current request review state and timeline."""
        async with UnitOfWork() as uow:
            request = await uow.requests.get(request_id)
            if not request:
                raise ValueError(f"Request with ID {request_id} not found.")

            # Resolve next version number
            next_version = await uow.snapshots.get_latest_version(request_id) + 1

            # Build request details payload
            payload = {
                "request": {
                    "id": request.id,
                    "project": request.project,
                    "regulator": request.regulator,
                    "status": request.status,
                    "owner": request.owner,
                    "assigned_reviewer": request.assigned_reviewer,
                    "review_notes": request.review_notes,
                },
                "claims": [],
                "timeline": [],
            }

            from sqlalchemy import select
            from database.models.claim import ClaimModel

            stmt_claims = select(ClaimModel).where(ClaimModel.request_id == request_id)
            res_claims = await uow.session.execute(stmt_claims)
            claims = res_claims.scalars().all()

            # Map claims and nested associations
            for claim in claims:
                claim_payload = {
                    "id": claim.id,
                    "text": claim.text,
                    "status": claim.status,
                    "reviewer_decision": claim.reviewer_decision,
                    "resolved": claim.resolved,
                    "review_notes": claim.review_notes,
                    "citation": claim.citation,
                    "comments": [],
                    "pinned_evidence": [],
                }

                # Load claim comments
                comments = await uow.comments.get_by_claim(claim.id)
                for comment in comments:
                    claim_payload["comments"].append(
                        {
                            "id": comment.id,
                            "user": comment.user,
                            "text": comment.text,
                            "parent_id": comment.parent_id,
                            "created_at": comment.created_at.isoformat(),
                        }
                    )

                # Load claim pinned evidence
                evidences = await uow.evidences.get_by_claim(claim.id)
                for ev in evidences:
                    claim_payload["pinned_evidence"].append(
                        {
                            "id": ev.id,
                            "chunk_id": ev.chunk_id,
                            "document_id": ev.document_id,
                            "role": ev.role,
                            "pinned_by": ev.pinned_by,
                        }
                    )

                payload["claims"].append(claim_payload)

            # Build snapshot record
            snapshot = ReviewSnapshotModel(
                request_id=request_id,
                version=next_version,
                creator=creator,
                request_status=request.status,
                config_hash="default-v1",
                payload=payload,
            )
            uow.session.add(snapshot)

            # Record timeline activity
            now_str = datetime.now(timezone.utc).isoformat()
            activity = ReviewActivityLogModel(
                request_id=request_id,
                event_type="snapshot",
                user=creator,
                details=f"Generated review snapshot version {next_version}.",
            )
            uow.session.add(activity)
            await uow.commit()

            # Publish event
            await ReviewEventPublisher.publish_snapshot_created(
                request_id, snapshot.id, next_version, creator
            )

            return SnapshotReceipt(
                request_id=request_id,
                snapshot_id=snapshot.id,
                version=next_version,
                creator=creator,
                timestamp=now_str,
                config_hash="default-v1",
            )

    @staticmethod
    async def compare_snapshots(
        request_id: int, version_from: int, version_to: int
    ) -> Dict[str, Any]:
        """Performs semantic comparison between two snapshots highlighting reviewer-visible updates."""
        async with UnitOfWork() as uow:
            snap_from = await uow.snapshots.get_by_version(request_id, version_from)
            snap_to = await uow.snapshots.get_by_version(request_id, version_to)

            if not snap_from or not snap_to:
                raise ValueError(
                    f"Snapshot versions ({version_from}, {version_to}) not found for request {request_id}"
                )

            payload_from = snap_from.payload
            payload_to = snap_to.payload

            diff = {
                "request_id": request_id,
                "version_from": version_from,
                "version_to": version_to,
                "status_changed": False,
                "old_status": payload_from["request"]["status"],
                "new_status": payload_to["request"]["status"],
                "reviewer_changed": payload_from["request"]["assigned_reviewer"]
                != payload_to["request"]["assigned_reviewer"],
                "claims_modified": [],
                "comments_added": [],
                "evidence_changes": [],
            }

            diff["status_changed"] = diff["old_status"] != diff["new_status"]

            # Map claims from to simplify comparison
            claims_from = {c["id"]: c for c in payload_from["claims"]}
            claims_to = {c["id"]: c for c in payload_to["claims"]}

            # 1. Compare claim decisions and details
            for cid, c_to in claims_to.items():
                c_from = claims_from.get(cid)
                if not c_from:
                    continue  # Ignores added claims for simple verification

                decision_changed = (
                    c_from["reviewer_decision"] != c_to["reviewer_decision"]
                )
                resolved_changed = c_from["resolved"] != c_to["resolved"]
                notes_changed = c_from["review_notes"] != c_to["review_notes"]

                if decision_changed or resolved_changed or notes_changed:
                    diff["claims_modified"].append(
                        {
                            "claim_id": cid,
                            "text": c_to["text"],
                            "changes": {
                                "decision": {
                                    "from": c_from["reviewer_decision"],
                                    "to": c_to["reviewer_decision"],
                                },
                                "resolved": {
                                    "from": c_from["resolved"],
                                    "to": c_to["resolved"],
                                },
                                "notes": {
                                    "from": c_from["review_notes"],
                                    "to": c_to["review_notes"],
                                },
                            },
                        }
                    )

                # 2. Compare comments
                comments_from = {comm["id"] for comm in c_from["comments"]}
                for comm in c_to["comments"]:
                    if comm["id"] not in comments_from:
                        diff["comments_added"].append(
                            {
                                "claim_id": cid,
                                "comment_id": comm["id"],
                                "user": comm["user"],
                                "text": comm["text"],
                            }
                        )

                # 3. Compare evidence
                evidence_from = {ev["chunk_id"]: ev for ev in c_from["pinned_evidence"]}
                evidence_to = {ev["chunk_id"]: ev for ev in c_to["pinned_evidence"]}

                for chid, ev in evidence_to.items():
                    if chid not in evidence_from:
                        diff["evidence_changes"].append(
                            {
                                "claim_id": cid,
                                "chunk_id": chid,
                                "action": "pinned",
                                "role": ev["role"],
                            }
                        )
                    elif evidence_from[chid]["role"] != ev["role"]:
                        diff["evidence_changes"].append(
                            {
                                "claim_id": cid,
                                "chunk_id": chid,
                                "action": "role_updated",
                                "old_role": evidence_from[chid]["role"],
                                "new_role": ev["role"],
                            }
                        )

                for chid in evidence_from:
                    if chid not in evidence_to:
                        diff["evidence_changes"].append(
                            {"claim_id": cid, "chunk_id": chid, "action": "unpinned"}
                        )

            return diff
