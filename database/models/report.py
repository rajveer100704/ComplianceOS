from sqlalchemy import String, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.models.base import Base, AuditMixin

class ReportTemplateModel(Base, AuditMixin):
    """Configurable report templates mapping formatting and required sections."""
    __tablename__ = "report_templates"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sections_config: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSON list of dicts (title, type, order)
    branding_config: Mapped[dict] = mapped_column(JSON, nullable=False)  # JSON styling parameters (colors, fonts)


class ReportModel(Base, AuditMixin):
    """Compliance output report documenting reviewed request findings."""
    __tablename__ = "reports"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("requests.id"), nullable=False)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("report_templates.id"), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    previous_version_id: Mapped[int | None] = mapped_column(ForeignKey("reports.id"), nullable=True)
    snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False)  # linked review snapshot version
    status: Mapped[str] = mapped_column(String(50), default="Draft", nullable=False)
    
    # Audit info
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    published_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    sections = relationship("ReportSectionModel", back_populates="report", cascade="all, delete-orphan", lazy="raise")
    findings = relationship("ReportFindingModel", back_populates="report", cascade="all, delete-orphan", lazy="raise")
    activity_logs = relationship("ReportActivityLogModel", back_populates="report", cascade="all, delete-orphan", lazy="raise")


class ReportSectionModel(Base, AuditMixin):
    """Structured report sections belonging to a compliance report."""
    __tablename__ = "report_sections"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(nullable=False)
    section_type: Mapped[str] = mapped_column(String(100), nullable=False)
    ordering: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    report = relationship("ReportModel", back_populates="sections", lazy="raise")


class ReportFindingModel(Base, AuditMixin):
    """Reported compliance finding with recommendations and risk matrix levels."""
    __tablename__ = "report_findings"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    recommendation: Mapped[str] = mapped_column(nullable=False)
    remediation: Mapped[str] = mapped_column(nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False)  # High, Medium, Low
    severity: Mapped[int] = mapped_column(Integer, nullable=False)
    likelihood: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False)  # Low, Medium, High, Critical

    # Relationships
    report = relationship("ReportModel", back_populates="findings", lazy="raise")
    citations = relationship("ReportCitationModel", back_populates="finding", cascade="all, delete-orphan", lazy="raise")


class ReportCitationModel(Base, AuditMixin):
    """Traceability map linking report findings back to reviewed claims, evidence, and comments."""
    __tablename__ = "report_citations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    finding_id: Mapped[int] = mapped_column(ForeignKey("report_findings.id"), nullable=False)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id"), nullable=False)
    evidence_id: Mapped[int | None] = mapped_column(ForeignKey("pinned_evidences.id"), nullable=True)
    comment_id: Mapped[int | None] = mapped_column(ForeignKey("claim_comments.id"), nullable=True)

    # Relationships
    finding = relationship("ReportFindingModel", back_populates="citations", lazy="raise")
    claim = relationship("ClaimModel", lazy="raise")
    evidence = relationship("PinnedEvidenceModel", lazy="raise")
    comment = relationship("ClaimCommentModel", lazy="raise")


class ReportActivityLogModel(Base, AuditMixin):
    """Immutable audit trail log for report lifecycle state changes and exports."""
    __tablename__ = "report_activity_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)  # ReportGenerated, ReportApproved, ReportPublished, etc.
    user: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[str] = mapped_column(nullable=False)

    # Relationships
    report = relationship("ReportModel", back_populates="activity_logs", lazy="raise")
