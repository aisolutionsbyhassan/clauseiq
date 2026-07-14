"""
ClauseIQ — Project Service

Business logic for project CRUD operations.
Services raise domain exceptions; they never raise HTTPException.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthorizationError, ResourceNotFoundError
from app.core.logging_config import get_logger
from app.models.contract import Contract
from app.models.project import Project
from app.models.user import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.storage.file_storage import delete_project_files

logger = get_logger("project_service")


def _project_to_response(project: Project, contract_count: int = 0) -> ProjectResponse:
    """Convert a Project ORM object to a response schema."""
    return ProjectResponse(
        id=project.id,
        user_id=project.user_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        contract_count=contract_count,
    )


async def create_project(
    data: ProjectCreateRequest,
    current_user: User,
    db: AsyncSession,
) -> ProjectResponse:
    """Create a new project for the authenticated user."""
    project = Project(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)

    logger.info("Project created: project_id=%s, user_id=%s", project.id, current_user.id)
    return _project_to_response(project, contract_count=0)


async def list_projects(
    current_user: User,
    db: AsyncSession,
) -> ProjectListResponse:
    """List all projects owned by the authenticated user with contract counts."""
    # Subquery for contract counts
    count_subq = (
        select(
            Contract.project_id,
            func.count(Contract.id).label("contract_count"),
        )
        .group_by(Contract.project_id)
        .subquery()
    )

    # Main query joining with count
    stmt = (
        select(Project, func.coalesce(count_subq.c.contract_count, 0))
        .outerjoin(count_subq, Project.id == count_subq.c.project_id)
        .where(Project.user_id == current_user.id)
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    projects = [
        _project_to_response(project, contract_count=count)
        for project, count in rows
    ]

    return ProjectListResponse(projects=projects, total=len(projects))


async def get_project(
    project_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> ProjectResponse:
    """Get a single project by ID, verifying ownership."""
    project = await _get_project_with_ownership_check(project_id, current_user, db)

    # Count contracts
    count_result = await db.execute(
        select(func.count(Contract.id)).where(Contract.project_id == project.id)
    )
    contract_count = count_result.scalar_one()

    return _project_to_response(project, contract_count=contract_count)


async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdateRequest,
    current_user: User,
    db: AsyncSession,
) -> ProjectResponse:
    """Update a project's name and/or description."""
    project = await _get_project_with_ownership_check(project_id, current_user, db)

    if data.name is not None:
        project.name = data.name
    if data.description is not None:
        project.description = data.description

    await db.flush()
    await db.refresh(project)

    logger.info("Project updated: project_id=%s", project.id)

    count_result = await db.execute(
        select(func.count(Contract.id)).where(Contract.project_id == project.id)
    )
    contract_count = count_result.scalar_one()

    return _project_to_response(project, contract_count=contract_count)


async def delete_project(
    project_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    """Delete a project and cascade to all its contracts and files."""
    project = await _get_project_with_ownership_check(project_id, current_user, db)

    # Delete files from filesystem
    await delete_project_files(user_id=current_user.id, project_id=project.id)

    # Delete from DB (cascades to contracts, chunks, etc.)
    await db.delete(project)
    await db.flush()

    logger.info("Project deleted: project_id=%s, user_id=%s", project_id, current_user.id)


async def _get_project_with_ownership_check(
    project_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Project:
    """Load a project and verify the current user owns it."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if project is None:
        raise ResourceNotFoundError("Project", str(project_id))

    if project.user_id != current_user.id:
        raise AuthorizationError("You do not have permission to access this project")

    return project
