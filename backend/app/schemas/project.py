"""
ClauseIQ — Project Request/Response Schemas

Pydantic schemas for project CRUD operations.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# =============================================================================
# Request Schemas
# =============================================================================

class ProjectCreateRequest(BaseModel):
    """Create a new project."""
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class ProjectUpdateRequest(BaseModel):
    """Update an existing project."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


# =============================================================================
# Response Schemas
# =============================================================================

class ProjectResponse(BaseModel):
    """Project data returned by the API."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    contract_count: int = 0

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """List of projects."""
    projects: list[ProjectResponse]
    total: int
