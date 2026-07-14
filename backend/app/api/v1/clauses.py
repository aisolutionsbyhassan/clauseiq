"""
ClauseIQ — Clauses Router

Handles HTTP concerns for clause extraction endpoints.
Business logic is delegated to clause_service per AGENT.md Section 11.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.clause import ClauseListResponse, ClauseResponse
from app.services import clause_service

router = APIRouter(prefix="/contracts/{contract_id}/clauses", tags=["Clauses"])


@router.post("", response_model=ClauseListResponse, status_code=201)
async def extract_clauses(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClauseListResponse:
    """Trigger clause extraction for a contract via AI."""
    clauses = await clause_service.extract_clauses_for_contract(
        contract_id=contract_id, db=db
    )
    return ClauseListResponse(
        clauses=[ClauseResponse.model_validate(c) for c in clauses],
        total=len(clauses),
    )


@router.get("", response_model=ClauseListResponse)
async def get_clauses(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ClauseListResponse:
    """Retrieve all extracted clauses for a contract."""
    clauses = await clause_service.get_clauses_for_contract(
        contract_id=contract_id, db=db
    )
    return ClauseListResponse(
        clauses=[ClauseResponse.model_validate(c) for c in clauses],
        total=len(clauses),
    )
