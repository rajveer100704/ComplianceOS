from sqlalchemy.ext.asyncio import AsyncSession
from database.session import async_session_factory
from database.repositories.request import RequestRepository
from database.repositories.document import DocumentRepository
from database.repositories.run import RunRepository
from database.repositories.claim import ClaimRepository
from database.repositories.receipt import ReceiptRepository
from database.repositories.requirement import RequirementRepository
from database.repositories.task import TaskRepository
from review.repositories.comment import CommentRepository
from review.repositories.evidence import EvidenceRepository
from review.repositories.snapshot import SnapshotRepository
from review.repositories.assignment import AssignmentRepository
from review.repositories.activity_log import ActivityLogRepository
from report.repositories.report import ReportRepository
from report.repositories.template import TemplateRepository
from report.repositories.citation import CitationRepository
from report.repositories.activity_log import ReportActivityLogRepository

class UnitOfWork:
    """Manages transaction scopes and instantiates repositories bound to a single async session."""

    def __init__(self):
        self.session_factory = async_session_factory
        self.session = None

    async def __aenter__(self):
        self.session = self.session_factory()
        self.requests = RequestRepository(self.session)
        self.documents = DocumentRepository(self.session)
        self.runs = RunRepository(self.session)
        self.claims = ClaimRepository(self.session)
        self.receipts = ReceiptRepository(self.session)
        self.requirements = RequirementRepository(self.session)
        self.tasks = TaskRepository(self.session)
        self.comments = CommentRepository(self.session)
        self.evidences = EvidenceRepository(self.session)
        self.snapshots = SnapshotRepository(self.session)
        self.assignments = AssignmentRepository(self.session)
        self.activity_logs = ActivityLogRepository(self.session)
        
        # Report subsystem
        self.reports = ReportRepository(self.session)
        self.templates = TemplateRepository(self.session)
        self.citations = CitationRepository(self.session)
        self.report_activity_logs = ReportActivityLogRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        await self.session.close()

    async def commit(self) -> None:
        """Commits changes pending in the active session."""
        if self.session:
            await self.session.commit()

    async def rollback(self) -> None:
        """Rollbacks transaction modifications in the session."""
        if self.session:
            await self.session.rollback()
