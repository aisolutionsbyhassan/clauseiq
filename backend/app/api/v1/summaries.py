"""
ClauseIQ — Summaries Router

Handles HTTP concerns for executive summary endpoints.
Business logic is delegated to summary_service per AGENT.md Section 11.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.summary import SummaryResponse
from app.services import summary_service

router = APIRouter(prefix="/contracts/{contract_id}/summary", tags=["Summaries"])


@router.post("", response_model=SummaryResponse, status_code=201)
async def generate_summary(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    """Generate an executive summary for a contract via AI."""
    summary = await summary_service.generate_summary_for_contract(
        contract_id=contract_id, db=db
    )
    return SummaryResponse.model_validate(summary)


@router.get("", response_model=SummaryResponse)
async def get_summary(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    """Retrieve the executive summary for a contract."""
    summary = await summary_service.get_summary_for_contract(
        contract_id=contract_id, db=db
    )
    if summary is None:
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("Executive Summary", str(contract_id))
    return SummaryResponse.model_validate(summary)
