"""
ClauseIQ — Risk Request/Response Schemas

Pydantic schemas for risk detection endpoints per AGENT.md Section 3.7.
"""

import uuid

from pydantic import BaseModel, Field


# =============================================================================
# Response Schemas
# =============================================================================

class RiskResponse(BaseModel):
    """A single detected risk."""
    id: uuid.UUID
    contract_id: uuid.UUID
    risk_type: str
    severity: str
    explanation: str
    recommendation: str

    model_config = {"from_attributes": True}


class RiskListResponse(BaseModel):
    """All detected risks for a contract."""
    risks: list[RiskResponse]
    total: int
