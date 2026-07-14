"""
ClauseIQ — DetectedRisk ORM Model

Per AGENT.md Section 8.1: id, contract_id (FK), risk_type (enum: 8 categories),
severity (low/medium/high), explanation, recommendation.
"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RiskType(str, enum.Enum):
    """The 8 predefined risk categories per AGENT.md Section 3.7."""
    UNLIMITED_LIABILITY = "unlimited_liability"
    AUTOMATIC_RENEWAL = "automatic_renewal"
    MISSING_TERMINATION = "missing_termination"
    MISSING_CONFIDENTIALITY = "missing_confidentiality"
    MISSING_INTELLECTUAL_PROPERTY = "missing_intellectual_property"
    VENDOR_FAVORABLE_JURISDICTION = "vendor_favorable_jurisdiction"
    VAGUE_PAYMENT_TERMS = "vague_payment_terms"
    MISSING_NOTICE_PERIOD = "missing_notice_period"


class Severity(str, enum.Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DetectedRisk(Base):
    __tablename__ = "detected_risks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    risk_type: Mapped[RiskType] = mapped_column(
        Enum(RiskType, name="risk_type_enum", create_constraint=True),
        nullable=False,
    )
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="severity_enum", create_constraint=True),
        nullable=False,
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    recommendation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Relationships
    contract = relationship("Contract", back_populates="risks")

    def __repr__(self) -> str:
        return f"<DetectedRisk(id={self.id}, type={self.risk_type}, severity={self.severity})>"
