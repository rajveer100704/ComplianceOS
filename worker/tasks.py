import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

from database.services.unit_of_work import UnitOfWork
from parsers.factory import ParserFactory
from retrieval.container import Container
from worker.state import TaskStateManager
from worker.retry import TaskRetryError, TaskPermanentError

logger = logging.getLogger("worker_tasks")


async def parse_and_index_document_task(
    task_id: str, request_id: int, doc_id: int, file_path: str
) -> Dict[str, Any]:
    """Asynchronously parses an uploaded PDF document, extracts text, and indexes chunks."""
    logger.info(
        f"Starting parse and index task {task_id} for doc {doc_id} of request {request_id}"
    )

    await TaskStateManager.update_task_status(task_id, "RUNNING")

    if not os.path.exists(file_path):
        err_msg = f"Uploaded file not found at path: {file_path}"
        logger.error(err_msg)
        await TaskStateManager.update_task_status(task_id, "FAILED", error=err_msg)
        raise TaskPermanentError(err_msg)

    try:
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
    except Exception as e:
        err_msg = f"Failed to read file: {e}"
        logger.exception(err_msg)
        await TaskStateManager.update_task_status(task_id, "FAILED", error=err_msg)
        raise TaskRetryError(err_msg, delay_sec=10.0)

    try:
        parser = ParserFactory.get_parser()
        filename = os.path.basename(file_path)
        text, metadata = parser.parse(pdf_bytes, filename)
    except Exception as e:
        err_msg = f"PDF Parser failed: {e}"
        logger.exception(err_msg)
        await TaskStateManager.update_task_status(task_id, "FAILED", error=err_msg)
        raise TaskPermanentError(err_msg)

    if not text.strip():
        err_msg = "No extractable text found in PDF"
        logger.error(err_msg)
        await TaskStateManager.update_task_status(task_id, "FAILED", error=err_msg)
        raise TaskPermanentError(err_msg)

    try:
        async with UnitOfWork() as uow:
            doc = await uow.documents.get(doc_id)
            if not doc:
                raise TaskPermanentError(f"Document {doc_id} not found in database")

            doc.text = text
            receipt = {
                "engine": metadata.get("parser_engine", "pymupdf"),
                "engine_version": metadata.get("parser_version", "unknown"),
                "ocr_used": metadata.get("ocr_used", False),
                "tables_found": metadata.get("tables_found", 0),
                "layout": metadata.get("layout", "flow"),
                "pages": metadata.get("pages", 1),
                "chars_extracted": len(text),
                "warnings": metadata.get("warnings", []),
            }

            receipt_dir = (
                Path(__file__).parent.parent
                / "storage"
                / "requests"
                / f"REQ-{request_id}"
                / "documents"
            )
            receipt_dir.mkdir(parents=True, exist_ok=True)
            receipt_path = receipt_dir / f"{filename}.receipt.json"
            with open(receipt_path, "w", encoding="utf-8") as rf:
                json.dump(receipt, rf, indent=2)

            await uow.commit()
    except Exception as e:
        if isinstance(e, TaskPermanentError):
            raise
        err_msg = f"Failed to update document text in DB: {e}"
        logger.exception(err_msg)
        await TaskStateManager.update_task_status(task_id, "FAILED", error=err_msg)
        raise TaskRetryError(err_msg, delay_sec=5.0)

    try:
        if not Container.is_initialized():
            Container.initialize()
        idx_service = Container.get_indexing_service()
        idx_service.index_document(doc_id=doc_id, filename=filename, raw_text=text)
    except Exception as e:
        err_msg = f"Indexing service failed: {e}"
        logger.exception(err_msg)
        await TaskStateManager.update_task_status(task_id, "FAILED", error=err_msg)
        raise TaskRetryError(err_msg, delay_sec=10.0)

    try:
        os.remove(file_path)
    except Exception:
        pass

    result_data = {
        "status": "SUCCESS",
        "chars_extracted": len(text),
        "parser_engine": metadata.get("parser_engine", "pymupdf"),
    }
    await TaskStateManager.update_task_status(task_id, "COMPLETED", result=result_data)
    return result_data


async def create_snapshot_task(
    task_id: str, request_id: int, creator: str
) -> Dict[str, Any]:
    """Background task generating a database snapshot of the request review status."""
    logger.info(f"Starting snapshot generation task {task_id} for request {request_id}")
    await TaskStateManager.update_task_status(task_id, "RUNNING")

    try:
        from review.services.snapshot_service import SnapshotService

        receipt = await SnapshotService.create_snapshot(request_id, creator)

        # Record timeline activity after successful background snapshot completion
        from review.services.review_service import ReviewService

        await ReviewService.log_custom_activity(
            request_id=request_id,
            event_type="snapshot",
            user=creator,
            details=f"Asynchronous background snapshot completion verified for version {receipt.version}.",
        )

        res = {
            "status": "COMPLETED",
            "version": receipt.version,
            "snapshot_id": receipt.snapshot_id,
            "creator": creator,
        }
        await TaskStateManager.update_task_status(task_id, "COMPLETED", result=res)
        return res
    except Exception as e:
        logger.exception(f"Failed to generate snapshot asynchronously: {e}")
        await TaskStateManager.update_task_status(task_id, "FAILED", error=str(e))
        raise TaskPermanentError(str(e))


async def export_report_task(
    task_id: str, report_id: int, format_str: str, exporter_user: str
) -> Dict[str, Any]:
    """Background task exporting a compliance report into the target file format."""
    logger.info(
        f"Starting report export task {task_id} for report {report_id} (format: {format_str})"
    )
    await TaskStateManager.update_task_status(task_id, "RUNNING")

    try:
        from report.services.export_service import ExportService

        receipt = await ExportService.export_report(
            report_id, format_str, exporter_user
        )

        res = {
            "status": "COMPLETED",
            "report_id": report_id,
            "format": format_str,
            "file_path": receipt.file_path,
            "exported_by": exporter_user,
        }
        await TaskStateManager.update_task_status(task_id, "COMPLETED", result=res)
        return res
    except Exception as e:
        logger.exception(f"Failed to export report asynchronously: {e}")
        await TaskStateManager.update_task_status(task_id, "FAILED", error=str(e))
        raise TaskPermanentError(str(e))
