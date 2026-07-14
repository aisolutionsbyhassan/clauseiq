"""
ClauseIQ — Comparison ORM Model

Per AGENT.md Section 8.1: id, project_id (FK), contract_a_id (FK),
contract_b_id (FK), added_clauses (JSON), removed_clauses (JSON),
modified_clauses (JSON), changed_obligations (JSON), created_at.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Comparison(Base):
    __tablename__ = "comparisons"

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
    contract_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    contract_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contracts.id", ondelete="CASCADE"),
        nullable=False,
    )
    added_clauses: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )
    removed_clauses: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )
    modified_clauses: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )
    changed_obligations: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project = relationship("Project", back_populates="comparisons")
    contract_a = relationship("Contract", foreign_keys=[contract_a_id])
    contract_b = relationship("Contract", foreign_keys=[contract_b_id])

    def __repr__(self) -> str:
        return f"<Comparison(id={self.id}, a={self.contract_a_id}, b={self.contract_b_id})>"
