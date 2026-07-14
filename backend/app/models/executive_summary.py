"""
ClauseIQ — ExecutiveSummary ORM Model

Per AGENT.md Section 8.1: id, contract_id (FK, unique), important_dates (JSON),
financial_terms (JSON), key_obligations (JSON), major_risks (JSON), generated_at.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExecutiveSummary(Base):
    __tablename__ = "executive_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    important_dates: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )
    financial_terms: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )
    key_obligations: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )
    major_risks: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    contract = relationship("Contract", back_populates="executive_summary")

    def __repr__(self) -> str:
        return f"<ExecutiveSummary(id={self.id}, contract_id={self.contract_id})>"
