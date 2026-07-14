"""
ClauseIQ — ExtractedClause ORM Model

Per AGENT.md Section 8.1: id, contract_id (FK), clause_type (enum: 11 categories),
is_present (bool), clause_text, source_chunk_ids (JSON array).
"""

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ClauseType(str, enum.Enum):
    """The 11 predefined clause categories per AGENT.md Section 3.6."""
    PAYMENT_TERMS = "payment_terms"
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    GOVERNING_LAW = "governing_law"
    LIABILITY = "liability"
    INDEMNIFICATION = "indemnification"
    RENEWAL = "renewal"
    ARBITRATION = "arbitration"
    FORCE_MAJEURE = "force_majeure"
    NON_COMPETE = "non_compete"


class ExtractedClause(Base):
    __tablename__ = "extracted_clauses"

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
    clause_type: Mapped[ClauseType] = mapped_column(
        Enum(ClauseType, name="clause_type_enum", create_constraint=True),
        nullable=False,
    )
    is_present: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    clause_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    # JSON array of chunk IDs that this clause was extracted from
    source_chunk_ids: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Relationships
    contract = relationship("Contract", back_populates="clauses")

    def __repr__(self) -> str:
        return f"<ExtractedClause(id={self.id}, type={self.clause_type}, present={self.is_present})>"
