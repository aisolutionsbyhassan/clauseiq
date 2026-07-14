"""
ClauseIQ — Dashboard Response Schemas

Pydantic schemas for dashboard endpoints per AGENT.md Section 3.10.
"""

from datetime import datetime

from pydantic import BaseModel, Field


# =============================================================================
# Response Schemas
# =============================================================================

class RecentContractItem(BaseModel):
    """A contract in the recent uploads list."""
    id: str
    filename: str
    project_name: str
    processing_status: str
    overall_risk_level: str
    uploaded_at: datetime


class DashboardResponse(BaseModel):
    """Aggregate dashboard data."""
    total_contracts: int = 0
    total_projects: int = 0
    high_risk_contracts: int = 0
    completed_contracts: int = 0
    recent_uploads: list[RecentContractItem] = Field(default_factory=list)
