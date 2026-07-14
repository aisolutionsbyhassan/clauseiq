"""
ClauseIQ — Clause Request/Response Schemas

Pydantic schemas for clause extraction endpoints per AGENT.md Section 3.6.
"""

import uuid

from pydantic import BaseModel, Field


# =============================================================================
# Response Schemas
# =============================================================================

class ClauseResponse(BaseModel):
    """A single extracted clause."""
    id: uuid.UUID
    contract_id: uuid.UUID
    clause_type: str
    is_present: bool
    clause_text: str | None = None
    source_chunk_ids: list | None = None

    model_config = {"from_attributes": True}


class ClauseListResponse(BaseModel):
    """All extracted clauses for a contract."""
    clauses: list[ClauseResponse]
    total: int
