"""
ClauseIQ — Clause Extraction Service

Orchestrates AI clause extraction per AGENT.md Section 10.2.
Consumes document chunks, calls Gemini, validates output, persists results.
"""

import json
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gemini_client import generate_structured
from app.ai.prompts.templates import CLAUSE_EXTRACTION_PROMPT, CLAUSE_EXTRACTION_SYSTEM
from app.ai.schemas import ClauseExtractionSchema
from app.core.exceptions import AIServiceError, ProcessingFailedError, ResourceNotFoundError
from app.core.logging_config import get_logger
from app.models.contract import Contract
from app.models.document_chunk import DocumentChunk
from app.models.extracted_clause import ClauseType, ExtractedClause

logger = get_logger("clause_service")


async def extract_clauses_for_contract(
    contract_id: uuid.UUID,
    db: AsyncSession,
) -> list[ExtractedClause]:
    """
    Run clause extraction on a contract's chunks via Gemini.

    Triggered during the document processing pipeline after
    chunking/embedding is complete.
    """
    # Load contract and chunks
    contract = await db.get(Contract, contract_id)
    if contract is None:
        raise ResourceNotFoundError("Contract", str(contract_id))

    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.contract_id == contract_id)
        .order_by(DocumentChunk.chunk_index)
    )
    chunks = result.scalars().all()

    if not chunks:
        raise ProcessingFailedError(
            f"No chunks found for contract {contract_id}. Cannot extract clauses."
        )

    # Build chunks text for the prompt
    chunks_text = "\n\n".join(
        f"[Chunk {c.chunk_index}, Page {c.page_number or 'N/A'}]:\n{c.text}"
        for c in chunks
    )

    # Call Gemini
    prompt = CLAUSE_EXTRACTION_PROMPT.format(chunks_text=chunks_text)
    raw_result = await generate_structured(
        prompt=prompt,
        system_instruction=CLAUSE_EXTRACTION_SYSTEM,
    )

    # Validate against schema
    try:
        validated = ClauseExtractionSchema(**raw_result)
    except Exception as e:
        logger.error("Clause extraction schema validation failed: %s", str(e))
        raise AIServiceError(f"Clause extraction output validation failed: {str(e)}")

    # Delete existing clauses for this contract (idempotent re-run)
    await db.execute(
        delete(ExtractedClause).where(ExtractedClause.contract_id == contract_id)
    )

    # Persist extracted clauses
    clause_models: list[ExtractedClause] = []
    for clause_data in validated.clauses:
        # Map string to enum, skip invalid types
        try:
            clause_type = ClauseType(clause_data.clause_type)
        except ValueError:
            logger.warning("Unknown clause type from AI: %s", clause_data.clause_type)
            continue

        clause = ExtractedClause(
            contract_id=contract_id,
            clause_type=clause_type,
            is_present=clause_data.is_present,
            clause_text=clause_data.clause_text,
            source_chunk_ids=clause_data.source_chunk_ids,
        )
        db.add(clause)
        clause_models.append(clause)

    await db.flush()

    logger.info(
        "Clauses extracted: contract_id=%s, count=%d",
        contract_id, len(clause_models),
    )
    return clause_models


async def get_clauses_for_contract(
    contract_id: uuid.UUID,
    db: AsyncSession,
) -> list[ExtractedClause]:
    """Retrieve all extracted clauses for a contract."""
    result = await db.execute(
        select(ExtractedClause)
        .where(ExtractedClause.contract_id == contract_id)
        .order_by(ExtractedClause.clause_type)
    )
    return list(result.scalars().all())
