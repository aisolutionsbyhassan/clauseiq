"""
ClauseIQ — Comparison Request/Response Schemas

Pydantic schemas for contract comparison endpoints per AGENT.md Section 3.9.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# =============================================================================
# Request Schemas
# =============================================================================

class ComparisonRequest(BaseModel):
    """Request to compare two contracts within a project."""
    contract_a_id: uuid.UUID
    contract_b_id: uuid.UUID


# =============================================================================
# Response Schemas
# =============================================================================

class ComparisonResponse(BaseModel):
    """Contract comparison result."""
    id: uuid.UUID
    project_id: uuid.UUID
    contract_a_id: uuid.UUID
    contract_b_id: uuid.UUID
    added_clauses: list = Field(default_factory=list)
    removed_clauses: list = Field(default_factory=list)
    modified_clauses: list = Field(default_factory=list)
    changed_obligations: list = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class ComparisonListResponse(BaseModel):
    """List of comparisons within a project."""
    comparisons: list[ComparisonResponse]
    total: int
