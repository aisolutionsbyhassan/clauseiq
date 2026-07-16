"""
ClauseIQ — Search Request/Response Schemas

Pydantic schemas for semantic search endpoints per AGENT.md Section 3.11.
"""

import uuid

from pydantic import BaseModel, Field


# =============================================================================
# Request Schemas
# =============================================================================

class SearchRequest(BaseModel):
    """Semantic search query scoped to a project."""
    query: str = Field(min_length=1, max_length=2000)
    project_id: uuid.UUID


# =============================================================================
# Response Schemas
# =============================================================================

class SearchResultItem(BaseModel):
    """A single search result with relevance score."""
    contract_id: uuid.UUID
    contract_filename: str
    chunk_index: int
    page_number: int | None = None
    text_snippet: str
    similarity_score: float


class SearchResponse(BaseModel):
    """Semantic search results."""
    results: list[SearchResultItem]
    total: int
    query: str
    ai_summary: str | None = None
