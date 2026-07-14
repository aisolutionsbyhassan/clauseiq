"""
ClauseIQ — Executive Summary Request/Response Schemas

Pydantic schemas for executive summary endpoints per AGENT.md Section 3.8.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# =============================================================================
# Response Schemas
# =============================================================================

class SummaryResponse(BaseModel):
    """Executive summary for a contract."""
    id: uuid.UUID
    contract_id: uuid.UUID
    important_dates: list = Field(default_factory=list)
    financial_terms: list = Field(default_factory=list)
    key_obligations: list = Field(default_factory=list)
    major_risks: list = Field(default_factory=list)
    generated_at: datetime

    model_config = {"from_attributes": True}
