"""
ClauseIQ — Contract ORM Model

Per AGENT.md Section 8.1: id, project_id (FK), filename, file_path,
file_type (pdf/docx), page_count, processing_status, overall_risk_level, uploaded_at.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProcessingStatus(str, enum.Enum):
    """Contract document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, enum.Enum):
    """Overall contract risk level, derived from highest detected risk severity."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FileType(str, enum.Enum):
    """Supported contract file types."""
    PDF = "pdf"
    DOCX = "docx"


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    file_type: Mapped[FileType] = mapped_column(
        Enum(FileType, name="file_type_enum", create_constraint=True),
        nullable=False,
    )
    page_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status_enum", create_constraint=True),
        default=ProcessingStatus.PENDING,
        nullable=False,
    )
    overall_risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risk_level_enum", create_constraint=True),
        default=RiskLevel.NONE,
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", back_populates="contracts")
    chunks = relationship(
        "DocumentChunk",
        back_populates="contract",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    clauses = relationship(
        "ExtractedClause",
        back_populates="contract",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    risks = relationship(
        "DetectedRisk",
        back_populates="contract",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    executive_summary = relationship(
        "ExecutiveSummary",
        back_populates="contract",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )
    chat_messages = relationship(
        "ChatMessage",
        back_populates="contract",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Contract(id={self.id}, filename={self.filename})>"
