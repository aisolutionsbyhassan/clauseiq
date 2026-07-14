"""
ClauseIQ — Search Router

Handles HTTP concerns for semantic search endpoints.
Business logic is delegated to search_service per AGENT.md Section 11.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse
from app.services import search_service

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def semantic_search(
    data: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Perform semantic search across contracts within a project."""
    return await search_service.semantic_search(
        query=data.query,
        project_id=data.project_id,
        current_user=current_user,
        db=db,
    )
