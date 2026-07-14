"""
ClauseIQ — Dashboard Service

Aggregate queries for the dashboard per AGENT.md Section 3.10.
Computed via lightweight SQL aggregate queries at request time.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging_config import get_logger
from app.models.contract import Contract, ProcessingStatus, RiskLevel
from app.models.project import Project
from app.schemas.dashboard import DashboardResponse, RecentContractItem

logger = get_logger("dashboard_service")


async def get_dashboard(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> DashboardResponse:
    """
    Compute dashboard aggregates for a user.

    Uses indexed columns (user_id, project_id, created_at) per AGENT.md Section 4.5.
    """
    # Get all project IDs for this user
    project_result = await db.execute(
        select(Project.id).where(Project.user_id == user_id)
    )
    project_ids = [row[0] for row in project_result.all()]

    if not project_ids:
        return DashboardResponse(
            total_contracts=0,
            total_projects=0,
            high_risk_contracts=0,
            completed_contracts=0,
            recent_uploads=[],
        )

    # Total projects
    total_projects = len(project_ids)

    # Total contracts
    total_result = await db.execute(
        select(func.count(Contract.id))
        .where(Contract.project_id.in_(project_ids))
    )
    total_contracts = total_result.scalar() or 0

    # High-risk contracts
    high_risk_result = await db.execute(
        select(func.count(Contract.id))
        .where(
            Contract.project_id.in_(project_ids),
            Contract.overall_risk_level == RiskLevel.HIGH,
        )
    )
    high_risk_contracts = high_risk_result.scalar() or 0

    # Completed contracts
    completed_result = await db.execute(
        select(func.count(Contract.id))
        .where(
            Contract.project_id.in_(project_ids),
            Contract.processing_status == ProcessingStatus.COMPLETED,
        )
    )
    completed_contracts = completed_result.scalar() or 0

    # Recent uploads (joined with project for name)
    recent_result = await db.execute(
        select(Contract, Project.name)
        .join(Project, Contract.project_id == Project.id)
        .where(Contract.project_id.in_(project_ids))
        .order_by(Contract.uploaded_at.desc())
        .limit(settings.DASHBOARD_RECENT_UPLOADS_LIMIT)
    )
    recent_rows = recent_result.all()

    recent_uploads = [
        RecentContractItem(
            id=str(contract.id),
            filename=contract.filename,
            project_name=project_name,
            processing_status=contract.processing_status.value,
            overall_risk_level=contract.overall_risk_level.value,
            uploaded_at=contract.uploaded_at,
        )
        for contract, project_name in recent_rows
    ]

    logger.info(
        "Dashboard loaded: user_id=%s, contracts=%d, high_risk=%d",
        user_id, total_contracts, high_risk_contracts,
    )

    return DashboardResponse(
        total_contracts=total_contracts,
        total_projects=total_projects,
        high_risk_contracts=high_risk_contracts,
        completed_contracts=completed_contracts,
        recent_uploads=recent_uploads,
    )
