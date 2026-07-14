"""
ClauseIQ — Chat Router

Handles HTTP concerns for AI chat with contracts.
Business logic is delegated to chat_service per AGENT.md Section 11.
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.chat import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
)
from app.services import chat_service

router = APIRouter(prefix="/contracts/{contract_id}/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def send_message(
    contract_id: uuid.UUID,
    data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Send a chat question about a contract and receive an AI-generated answer."""
    result = await chat_service.chat_with_contract(
        contract_id=contract_id,
        question=data.question,
        db=db,
    )
    return ChatResponse(**result)


@router.get("", response_model=ChatHistoryResponse)
async def get_chat_history(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatHistoryResponse:
    """Retrieve the full chat history for a contract."""
    messages = await chat_service.get_chat_history(
        contract_id=contract_id, db=db
    )
    return ChatHistoryResponse(
        messages=[ChatMessageResponse.model_validate(m) for m in messages],
        total=len(messages),
    )


@router.delete("", status_code=204)
async def clear_chat_history(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Clear all chat messages for a contract."""
    await chat_service.clear_chat_history(
        contract_id=contract_id, db=db
    )
