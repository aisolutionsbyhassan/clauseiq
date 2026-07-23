"""
ClauseIQ — Risk Detection Service

Orchestrates AI risk detection per AGENT.md Section 10.3.
Consumes extracted clauses (not raw chunks), calls Groq, validates output,
persists results, and updates the contract's overall risk level.
"""

import json
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_client import generate_structured
from app.ai.prompts.templates import RISK_DETECTION_PROMPT, RISK_DETECTION_SYSTEM
from app.ai.schemas import RiskDetectionSchema
from app.core.exceptions import AIServiceError, ProcessingFailedError, ResourceNotFoundError
from app.core.logging_config import get_logger
from app.models.contract import Contract, RiskLevel
from app.models.detected_risk import DetectedRisk, RiskType, Severity
from app.models.extracted_clause import ExtractedClause

logger = get_logger("risk_service")

# Severity hierarchy for determining overall contract risk level
_SEVERITY_ORDER = {Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3}


async def detect_risks_for_contract(
    contract_id: uuid.UUID,
    db: AsyncSession,
) -> list[DetectedRisk]:
    """
    Run risk detection on a contract's extracted clauses via Groq.

    Triggered immediately after clause extraction completes.
    Risk detection consumes clause data, not raw chunks.
    """
    # Load contract
    contract = await db.get(Contract, contract_id)
    if contract is None:
        raise ResourceNotFoundError("Contract", str(contract_id))

    # Load extracted clauses
    result = await db.execute(
        select(ExtractedClause).where(ExtractedClause.contract_id == contract_id)
    )
    clauses = result.scalars().all()

    if not clauses:
        raise ProcessingFailedError(
            f"No extracted clauses found for contract {contract_id}. Run clause extraction first."
        )

    # Build clauses JSON for the prompt
    clauses_json = json.dumps([
        {
            "clause_type": c.clause_type.value,
            "is_present": c.is_present,
            "clause_text": c.clause_text,
        }
        for c in clauses
    ], indent=2)

    # Call Groq
    prompt = RISK_DETECTION_PROMPT.format(clauses_json=clauses_json)
    raw_result = await generate_structured(
        prompt=prompt,
        system_instruction=RISK_DETECTION_SYSTEM,
    )

    # Validate against schema
    try:
        validated = RiskDetectionSchema(**raw_result)
    except Exception as e:
        logger.error("Risk detection schema validation failed: %s", str(e))
        raise AIServiceError(f"Risk detection output validation failed: {str(e)}")

    # Delete existing risks for this contract (idempotent re-run)
    await db.execute(
        delete(DetectedRisk).where(DetectedRisk.contract_id == contract_id)
    )

    # Persist detected risks
    risk_models: list[DetectedRisk] = []
    max_severity = RiskLevel.NONE

    for risk_data in validated.risks:
        if not risk_data.is_applicable:
            continue

        # Map string to enum
        try:
            risk_type = RiskType(risk_data.risk_type)
        except ValueError:
            logger.warning("Unknown risk type from AI: %s", risk_data.risk_type)
            continue

        try:
            severity = Severity(risk_data.severity) if risk_data.severity else Severity.LOW
        except ValueError:
            severity = Severity.LOW

        risk = DetectedRisk(
            contract_id=contract_id,
            risk_type=risk_type,
            severity=severity,
            explanation=risk_data.explanation or "No explanation provided",
            recommendation=risk_data.recommendation or "Review this clause with legal counsel",
        )
        db.add(risk)
        risk_models.append(risk)

        # Track highest severity for overall risk level
        severity_val = _SEVERITY_ORDER.get(severity, 0)
        current_max_val = _SEVERITY_ORDER.get(
            Severity(max_severity.value) if max_severity != RiskLevel.NONE else Severity.LOW, 0
        )
        if max_severity == RiskLevel.NONE or severity_val > current_max_val:
            max_severity = RiskLevel(severity.value)

    # Update contract's overall risk level
    if not risk_models:
        contract.overall_risk_level = RiskLevel.NONE
    else:
        contract.overall_risk_level = max_severity

    await db.flush()

    logger.info(
        "Risks detected: contract_id=%s, count=%d, overall_level=%s",
        contract_id, len(risk_models), contract.overall_risk_level.value,
    )
    return risk_models


async def get_risks_for_contract(
    contract_id: uuid.UUID,
    db: AsyncSession,
) -> list[DetectedRisk]:
    """Retrieve all detected risks for a contract."""
    result = await db.execute(
        select(DetectedRisk)
        .where(DetectedRisk.contract_id == contract_id)
        .order_by(DetectedRisk.severity.desc())
    )
    return list(result.scalars().all())
