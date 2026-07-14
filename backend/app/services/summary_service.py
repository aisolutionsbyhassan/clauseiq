"""
ClauseIQ — Executive Summary Service

Orchestrates summary generation per AGENT.md Section 10.4.
Consumes clause extraction and risk detection outputs.
"""

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gemini_client import generate_structured
from app.ai.prompts.templates import EXECUTIVE_SUMMARY_PROMPT, EXECUTIVE_SUMMARY_SYSTEM
from app.ai.schemas import ExecutiveSummarySchema
from app.core.exceptions import AIServiceError, ProcessingFailedError, ResourceNotFoundError
from app.core.logging_config import get_logger
from app.models.contract import Contract
from app.models.detected_risk import DetectedRisk
from app.models.executive_summary import ExecutiveSummary
from app.models.extracted_clause import ExtractedClause

logger = get_logger("summary_service")


async def generate_summary_for_contract(
    contract_id: uuid.UUID,
    db: AsyncSession,
) -> ExecutiveSummary:
    """
    Generate an executive summary for a contract via Gemini.

    Triggered after clause extraction and risk detection complete.
    """
    # Load contract
    contract = await db.get(Contract, contract_id)
    if contract is None:
        raise ResourceNotFoundError("Contract", str(contract_id))

    # Load clauses
    clause_result = await db.execute(
        select(ExtractedClause).where(ExtractedClause.contract_id == contract_id)
    )
    clauses = clause_result.scalars().all()

    # Load risks
    risk_result = await db.execute(
        select(DetectedRisk).where(DetectedRisk.contract_id == contract_id)
    )
    risks = risk_result.scalars().all()

    clauses_json = json.dumps([
        {
            "clause_type": c.clause_type.value,
            "is_present": c.is_present,
            "clause_text": c.clause_text,
        }
        for c in clauses
    ], indent=2)

    risks_json = json.dumps([
        {
            "risk_type": r.risk_type.value,
            "severity": r.severity.value,
            "explanation": r.explanation,
            "recommendation": r.recommendation,
        }
        for r in risks
    ], indent=2)

    # Call Gemini
    prompt = EXECUTIVE_SUMMARY_PROMPT.format(
        clauses_json=clauses_json,
        risks_json=risks_json,
        filename=contract.filename,
    )
    raw_result = await generate_structured(
        prompt=prompt,
        system_instruction=EXECUTIVE_SUMMARY_SYSTEM,
    )

    # Validate
    try:
        validated = ExecutiveSummarySchema(**raw_result)
    except Exception as e:
        logger.error("Summary schema validation failed: %s", str(e))
        raise AIServiceError(f"Summary output validation failed: {str(e)}")

    # Upsert summary (one per contract)
    existing_result = await db.execute(
        select(ExecutiveSummary).where(ExecutiveSummary.contract_id == contract_id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        existing.important_dates = validated.important_dates
        existing.financial_terms = validated.financial_terms
        existing.key_obligations = validated.key_obligations
        existing.major_risks = validated.major_risks
        summary = existing
    else:
        summary = ExecutiveSummary(
            contract_id=contract_id,
            important_dates=validated.important_dates,
            financial_terms=validated.financial_terms,
            key_obligations=validated.key_obligations,
            major_risks=validated.major_risks,
        )
        db.add(summary)

    await db.flush()
    await db.refresh(summary)

    logger.info("Executive summary generated: contract_id=%s", contract_id)
    return summary


async def get_summary_for_contract(
    contract_id: uuid.UUID,
    db: AsyncSession,
) -> ExecutiveSummary | None:
    """Retrieve the executive summary for a contract."""
    result = await db.execute(
        select(ExecutiveSummary).where(ExecutiveSummary.contract_id == contract_id)
    )
    return result.scalar_one_or_none()
