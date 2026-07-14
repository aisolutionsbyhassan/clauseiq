"""
ClauseIQ — Chat Service

Orchestrates AI chat per AGENT.md Section 10.1.
Retrieves relevant chunks, constructs prompt, calls Gemini,
persists conversation history.
"""

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import generate_single_embedding
from app.ai.gemini_client import generate_structured
from app.ai.prompts.templates import CHAT_PROMPT, CHAT_SYSTEM
from app.ai.retriever import query_embeddings
from app.ai.schemas import ChatResponseSchema
from app.config import settings
from app.core.exceptions import AIServiceError, ResourceNotFoundError
from app.core.logging_config import get_logger
from app.models.chat_message import ChatMessage, ChatRole
from app.models.contract import Contract

logger = get_logger("chat_service")


async def chat_with_contract(
    contract_id: uuid.UUID,
    question: str,
    db: AsyncSession,
) -> dict:
    """
    Process a chat question about a contract.

    Pipeline: embed question → retrieve chunks → build prompt → Gemini → persist messages → return.
    """
    # Verify contract exists
    contract = await db.get(Contract, contract_id)
    if contract is None:
        raise ResourceNotFoundError("Contract", str(contract_id))

    # Step 1: Embed the question
    query_embedding = generate_single_embedding(question)

    # Step 2: Retrieve relevant chunks via ChromaDB
    results = query_embeddings(
        query_embedding=query_embedding,
        n_results=settings.RETRIEVAL_TOP_K,
        where={"contract_id": str(contract_id)},
    )

    # Build context from retrieved chunks
    context_chunks = ""
    if results["documents"] and results["documents"][0]:
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
            chunk_idx = meta.get("chunk_index", i)
            page_num = meta.get("page_number", "N/A")
            context_chunks += f"[Chunk {chunk_idx}, Page {page_num}]:\n{doc}\n\n"
    else:
        context_chunks = "No relevant context found in the contract."

    # Step 3: Load conversation history (last 10 messages for context)
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.contract_id == contract_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(10)
    )
    history_messages = list(reversed(history_result.scalars().all()))

    conversation_history = ""
    if history_messages:
        for msg in history_messages:
            role = "User" if msg.role == ChatRole.USER else "Assistant"
            conversation_history += f"{role}: {msg.content}\n"
    else:
        conversation_history = "No previous conversation."

    # Step 4: Call Gemini
    prompt = CHAT_PROMPT.format(
        context_chunks=context_chunks,
        conversation_history=conversation_history,
        question=question,
    )

    raw_result = await generate_structured(
        prompt=prompt,
        system_instruction=CHAT_SYSTEM,
        temperature=0.3,
    )

    # Validate
    try:
        validated = ChatResponseSchema(**raw_result)
    except Exception as e:
        logger.error("Chat response validation failed: %s", str(e))
        raise AIServiceError(f"Chat response validation failed: {str(e)}")

    # Step 5: Persist messages
    user_message = ChatMessage(
        contract_id=contract_id,
        role=ChatRole.USER,
        content=question,
    )
    db.add(user_message)

    assistant_message = ChatMessage(
        contract_id=contract_id,
        role=ChatRole.ASSISTANT,
        content=validated.answer,
        citations=[c.model_dump() for c in validated.citations],
    )
    db.add(assistant_message)
    await db.flush()

    logger.info("Chat response generated: contract_id=%s", contract_id)

    return {
        "answer": validated.answer,
        "citations": [c.model_dump() for c in validated.citations],
    }


async def get_chat_history(
    contract_id: uuid.UUID,
    db: AsyncSession,
) -> list[ChatMessage]:
    """Retrieve full chat history for a contract."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.contract_id == contract_id)
        .order_by(ChatMessage.created_at)
    )
    return list(result.scalars().all())


async def clear_chat_history(
    contract_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """Clear all chat messages for a contract."""
    from sqlalchemy import delete
    await db.execute(
        delete(ChatMessage).where(ChatMessage.contract_id == contract_id)
    )
    await db.flush()
    logger.info("Chat history cleared: contract_id=%s", contract_id)
