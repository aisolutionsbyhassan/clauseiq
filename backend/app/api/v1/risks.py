"""
ClauseIQ — Risks Router

Handles HTTP concerns for risk detection endpoints.
Business logic is delegated to risk_service per AGENT.md Section 11.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.risk import RiskListResponse, RiskResponse
from app.services import risk_service

router = APIRouter(prefix="/contracts/{contract_id}/risks", tags=["Risks"])


@router.post("", response_model=RiskListResponse, status_code=201)
async def detect_risks(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskListResponse:
    """Trigger risk detection for a contract via AI."""
    risks = await risk_service.detect_risks_for_contract(
        contract_id=contract_id, db=db
    )
    return RiskListResponse(
        risks=[RiskResponse.model_validate(r) for r in risks],
        total=len(risks),
    )


@router.get("", response_model=RiskListResponse)
async def get_risks(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskListResponse:
    """Retrieve all detected risks for a contract."""
    risks = await risk_service.get_risks_for_contract(
        contract_id=contract_id, db=db
    )
    return RiskListResponse(
        risks=[RiskResponse.model_validate(r) for r in risks],
        total=len(risks),
    )
