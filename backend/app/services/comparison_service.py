"""
ClauseIQ — Comparison Service

Orchestrates contract comparison per AGENT.md Section 10.5.
Consumes extracted clauses from both contracts, calls Gemini for semantic diff.
"""

import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gemini_client import generate_structured
from app.ai.prompts.templates import COMPARISON_PROMPT, COMPARISON_SYSTEM
from app.ai.schemas import ComparisonSchema
from app.core.exceptions import (
    AIServiceError,
    AuthorizationError,
    ProcessingFailedError,
    ResourceNotFoundError,
)
from app.core.logging_config import get_logger
from app.models.comparison import Comparison
from app.models.contract import Contract
from app.models.extracted_clause import ExtractedClause
from app.models.project import Project
from app.models.user import User

logger = get_logger("comparison_service")


async def compare_contracts(
    project_id: uuid.UUID,
    contract_a_id: uuid.UUID,
    contract_b_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Comparison:
    """
    Compare two contracts within a project via Gemini.

    Both contracts must belong to the same project and have
    completed clause extraction.
    """
    # Verify project ownership
    project = await _get_project_with_ownership(project_id, current_user, db)

    # Load both contracts and verify they belong to this project
    contract_a = await db.get(Contract, contract_a_id)
    contract_b = await db.get(Contract, contract_b_id)

    if contract_a is None:
        raise ResourceNotFoundError("Contract A", str(contract_a_id))
    if contract_b is None:
        raise ResourceNotFoundError("Contract B", str(contract_b_id))

    if contract_a.project_id != project.id:
        raise ProcessingFailedError(
            f"Contract A ({contract_a_id}) does not belong to project {project_id}"
        )
    if contract_b.project_id != project.id:
        raise ProcessingFailedError(
            f"Contract B ({contract_b_id}) does not belong to project {project_id}"
        )

    # Load clauses for both contracts
    clauses_a = await _get_clauses(contract_a_id, db)
    clauses_b = await _get_clauses(contract_b_id, db)

    if not clauses_a:
        raise ProcessingFailedError(
            f"No clauses extracted for Contract A ({contract_a.filename}). "
            "Run clause extraction first."
        )
    if not clauses_b:
        raise ProcessingFailedError(
            f"No clauses extracted for Contract B ({contract_b.filename}). "
            "Run clause extraction first."
        )

    # Build clause JSONs for the prompt
    clauses_a_json = json.dumps(_clauses_to_dicts(clauses_a), indent=2)
    clauses_b_json = json.dumps(_clauses_to_dicts(clauses_b), indent=2)

    # Call Gemini
    prompt = COMPARISON_PROMPT.format(
        filename_a=contract_a.filename,
        filename_b=contract_b.filename,
        clauses_a_json=clauses_a_json,
        clauses_b_json=clauses_b_json,
    )
    raw_result = await generate_structured(
        prompt=prompt,
        system_instruction=COMPARISON_SYSTEM,
    )

    # Validate
    try:
        validated = ComparisonSchema(**raw_result)
    except Exception as e:
        logger.error("Comparison schema validation failed: %s", str(e))
        raise AIServiceError(f"Comparison output validation failed: {str(e)}")

    # Persist comparison
    comparison = Comparison(
        project_id=project.id,
        contract_a_id=contract_a_id,
        contract_b_id=contract_b_id,
        added_clauses=validated.added_clauses,
        removed_clauses=validated.removed_clauses,
        modified_clauses=validated.modified_clauses,
        changed_obligations=validated.changed_obligations,
    )
    db.add(comparison)
    await db.flush()
    await db.refresh(comparison)

    logger.info(
        "Comparison completed: project_id=%s, a=%s, b=%s",
        project_id, contract_a_id, contract_b_id,
    )
    return comparison


async def get_comparison(
    comparison_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Comparison:
    """Retrieve a single comparison by ID."""
    comparison = await db.get(Comparison, comparison_id)
    if comparison is None:
        raise ResourceNotFoundError("Comparison", str(comparison_id))

    # Verify ownership via project
    await _get_project_with_ownership(comparison.project_id, current_user, db)
    return comparison


async def list_comparisons(
    project_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> list[Comparison]:
    """List all comparisons within a project."""
    await _get_project_with_ownership(project_id, current_user, db)

    result = await db.execute(
        select(Comparison)
        .where(Comparison.project_id == project_id)
        .order_by(Comparison.created_at.desc())
    )
    return list(result.scalars().all())


# =============================================================================
# Internal Helpers
# =============================================================================

async def _get_project_with_ownership(
    project_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Project:
    """Load a project and verify ownership."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project", str(project_id))
    if project.user_id != current_user.id:
        raise AuthorizationError("You do not have permission to access this project")
    return project


async def _get_clauses(
    contract_id: uuid.UUID,
    db: AsyncSession,
) -> list[ExtractedClause]:
    """Load extracted clauses for a contract."""
    result = await db.execute(
        select(ExtractedClause).where(ExtractedClause.contract_id == contract_id)
    )
    return list(result.scalars().all())


def _clauses_to_dicts(clauses: list[ExtractedClause]) -> list[dict]:
    """Convert clause models to dicts for the prompt."""
    return [
        {
            "clause_type": c.clause_type.value,
            "is_present": c.is_present,
            "clause_text": c.clause_text,
        }
        for c in clauses
    ]
