"""
ClauseIQ — Contracts Router

Handles HTTP concerns for contract upload, listing, detail, search, and deletion.
Business logic is delegated to contract_service per AGENT.md Section 11.
"""

import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.contract import ContractDetailResponse, ContractListResponse, ContractResponse
from app.services import contract_service

router = APIRouter(prefix="/contracts", tags=["Contracts"])


@router.post("", response_model=ContractResponse, status_code=201)
async def upload_contract(
    project_id: uuid.UUID = Query(..., description="Project to upload the contract into"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContractResponse:
    """Upload a contract file (PDF or DOCX) to a project."""
    file_content = await file.read()
    return await contract_service.upload_contract(
        filename=file.filename or "unnamed",
        content_type=file.content_type,
        file_content=file_content,
        project_id=project_id,
        current_user=current_user,
        db=db,
    )


@router.get("", response_model=ContractListResponse)
async def list_contracts(
    project_id: uuid.UUID = Query(..., description="Project to list contracts for"),
    search: str | None = Query(default=None, description="Search by filename"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContractListResponse:
    """List all contracts within a project, optionally filtered by filename."""
    if search:
        return await contract_service.search_contracts_by_filename(
            project_id=project_id,
            query=search,
            current_user=current_user,
            db=db,
        )
    return await contract_service.list_contracts(
        project_id=project_id, current_user=current_user, db=db
    )


@router.get("/{contract_id}", response_model=ContractDetailResponse)
async def get_contract(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ContractDetailResponse:
    """Get a single contract's details."""
    return await contract_service.get_contract(
        contract_id=contract_id, current_user=current_user, db=db
    )


@router.get("/{contract_id}/download", response_class=FileResponse)
async def download_contract(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Download the original uploaded contract file."""
    file_path, filename, content_type = await contract_service.get_contract_file(
        contract_id=contract_id, current_user=current_user, db=db
    )
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=content_type,
    )


@router.delete("/{contract_id}", status_code=204)
async def delete_contract(
    contract_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a contract and all associated data."""
    await contract_service.delete_contract(
        contract_id=contract_id, current_user=current_user, db=db
    )
