"""
ClauseIQ — Chat Request/Response Schemas

Pydantic schemas for chat endpoints per AGENT.md Section 3.5.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# =============================================================================
# Request Schemas
# =============================================================================

class ChatRequest(BaseModel):
    """Send a chat message about a contract."""
    question: str = Field(min_length=1, max_length=5000)


# =============================================================================
# Response Schemas
# =============================================================================

class ChatCitationResponse(BaseModel):
    """A source citation in a chat response."""
    chunk_index: int
    page_number: int | None = None
    text_snippet: str


class ChatResponse(BaseModel):
    """Response from the AI chat endpoint."""
    answer: str
    citations: list[ChatCitationResponse] = []


class ChatMessageResponse(BaseModel):
    """A single chat message in conversation history."""
    id: uuid.UUID
    contract_id: uuid.UUID
    role: str
    content: str
    citations: list | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    """Full chat history for a contract."""
    messages: list[ChatMessageResponse]
    total: int
