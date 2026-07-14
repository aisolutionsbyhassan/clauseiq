"""
ClauseIQ — Contract Request/Response Schemas

Pydantic schemas for contract upload, listing, and detail responses.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# =============================================================================
# Response Schemas
# =============================================================================

class ContractResponse(BaseModel):
    """Contract data returned by the API."""
    id: uuid.UUID
    project_id: uuid.UUID
    filename: str
    file_type: str
    page_count: int | None
    processing_status: str
    overall_risk_level: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class ContractListResponse(BaseModel):
    """List of contracts within a project."""
    contracts: list[ContractResponse]
    total: int


class ContractDetailResponse(ContractResponse):
    """Detailed contract response (extended later with clauses/risks/summary)."""
    pass
