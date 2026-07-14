"""
ClauseIQ — Comparisons Router

Handles HTTP concerns for contract comparison endpoints.
Business logic is delegated to comparison_service per AGENT.md Section 11.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.comparison import (
    ComparisonListResponse,
    ComparisonRequest,
    ComparisonResponse,
)
from app.services import comparison_service

router = APIRouter(prefix="/comparisons", tags=["Comparisons"])


@router.post("", response_model=ComparisonResponse, status_code=201)
async def create_comparison(
    project_id: uuid.UUID = Query(..., description="Project containing both contracts"),
    data: ComparisonRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComparisonResponse:
    """Compare two contracts within a project via AI."""
    comparison = await comparison_service.compare_contracts(
        project_id=project_id,
        contract_a_id=data.contract_a_id,
        contract_b_id=data.contract_b_id,
        current_user=current_user,
        db=db,
    )
    return ComparisonResponse.model_validate(comparison)


@router.get("", response_model=ComparisonListResponse)
async def list_comparisons(
    project_id: uuid.UUID = Query(..., description="Project to list comparisons for"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComparisonListResponse:
    """List all comparisons within a project."""
    comparisons = await comparison_service.list_comparisons(
        project_id=project_id, current_user=current_user, db=db
    )
    return ComparisonListResponse(
        comparisons=[ComparisonResponse.model_validate(c) for c in comparisons],
        total=len(comparisons),
    )


@router.get("/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison(
    comparison_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComparisonResponse:
    """Retrieve a single comparison by ID."""
    comparison = await comparison_service.get_comparison(
        comparison_id=comparison_id, current_user=current_user, db=db
    )
    return ComparisonResponse.model_validate(comparison)
