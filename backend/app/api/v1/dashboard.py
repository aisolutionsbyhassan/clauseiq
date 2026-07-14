"""
ClauseIQ — Dashboard Router

Handles HTTP concerns for dashboard aggregate endpoints.
Business logic is delegated to dashboard_service per AGENT.md Section 11.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """Get aggregate dashboard data for the authenticated user."""
    return await dashboard_service.get_dashboard(
        user_id=current_user.id, db=db
    )
