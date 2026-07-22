from database.models.base import Base, AuditMixin, generate_uuid
from database.models.enums import (
    UserRole,
    UserStatus,
    MembershipRole,
    InvitationStatus,
    OrganizationPlan,
)
from database.models.organization import Organization
from database.models.membership import OrganizationMembership
from database.models.team import Team
from database.models.invitation import Invitation
from database.models.user import User
from database.models.oauth_account import OAuthAccount
from database.models.refresh_token import RefreshToken
from database.models.session_model import SessionModel

# Import all domain models so Base.metadata contains all table definitions
from database.models.requirement import RequirementModel
from database.models.claim import ClaimModel
from database.models.document import DocumentModel
from database.models.chunk import ChunkModel
from database.models.request import RequestModel
from database.models.review import (
    ClaimCommentModel,
    CommentMentionModel,
    PinnedEvidenceModel,
    ReviewAssignmentModel,
    ReviewActivityLogModel,
    ReviewSnapshotModel,
)
from database.models.report import (
    ReportModel,
    ReportTemplateModel,
    ReportSectionModel,
    ReportFindingModel,
    ReportCitationModel,
    ReportActivityLogModel,
)
from database.models.outbox import OutboxEventModel
from database.models.audit import AuditLogModel
from database.models.run import RunModel
from database.models.task import TaskModel

__all__ = [
    "Base",
    "AuditMixin",
    "generate_uuid",
    # Enums
    "UserRole",
    "UserStatus",
    "MembershipRole",
    "InvitationStatus",
    "OrganizationPlan",
    # v1.2 Multi-tenant models
    "Organization",
    "OrganizationMembership",
    "Team",
    "Invitation",
    # Auth models
    "User",
    "OAuthAccount",
    "RefreshToken",
    "SessionModel",
    # Domain models
    "RequirementModel",
    "ClaimModel",
    "DocumentModel",
    "ChunkModel",
    "RequestModel",
    "ClaimCommentModel",
    "CommentMentionModel",
    "PinnedEvidenceModel",
    "ReviewAssignmentModel",
    "ReviewActivityLogModel",
    "ReviewSnapshotModel",
    "ReportModel",
    "ReportTemplateModel",
    "ReportSectionModel",
    "ReportFindingModel",
    "ReportCitationModel",
    "ReportActivityLogModel",
    "OutboxEventModel",
    "AuditLogModel",
    "RunModel",
    "TaskModel",
]
