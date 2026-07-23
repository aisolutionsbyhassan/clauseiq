"""
ClauseIQ — Contract Service

Business logic for contract upload, listing, detail, search, and deletion.
This is the pipeline entry point referenced in AGENT.md Section 18.
On upload, the full document processing pipeline (extract → clean → chunk →
embed → store) runs synchronously per AGENT.md Section 3.3 MVP design.
Services raise domain exceptions; they never raise HTTPException.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import generate_embeddings
from app.ai.retriever import delete_by_contract, store_embeddings
from app.config import settings
from app.core.exceptions import (
    AuthorizationError,
    FileValidationError,
    ProcessingFailedError,
    ResourceNotFoundError,
)
from app.core.logging_config import get_logger
from app.document_processing.chunker import chunk_pages
from app.document_processing.cleaner import clean_text
from app.document_processing.extractor import extract_text
from app.models.contract import Contract, FileType, ProcessingStatus
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.models.user import User
from app.schemas.contract import ContractDetailResponse, ContractListResponse, ContractResponse
from app.storage.file_storage import delete_contract_files, save_upload

logger = get_logger("contract_service")

# Allowed MIME types and their corresponding FileType enum values
ALLOWED_MIME_TYPES = {
    "application/pdf": FileType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCX,
}

ALLOWED_EXTENSIONS = {".pdf": FileType.PDF, ".docx": FileType.DOCX}


def _validate_file(filename: str, content_type: str | None, file_size: int) -> FileType:
    """
    Validate the uploaded file's extension, MIME type, and size.

    Returns:
        The detected FileType enum value.

    Raises:
        FileValidationError: If validation fails.
    """
    # Extension check
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file type '{ext}'. Only PDF and DOCX files are accepted."
        )

    # MIME type check (if provided by the upload)
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise FileValidationError(
            f"Invalid MIME type '{content_type}'. Expected application/pdf or DOCX MIME type."
        )

    # Size check
    if file_size > settings.max_upload_size_bytes:
        raise FileValidationError(
            f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit "
            f"({file_size / (1024 * 1024):.1f}MB uploaded)."
        )

    return ALLOWED_EXTENSIONS[ext]


async def upload_contract(
    filename: str,
    content_type: str | None,
    file_content: bytes,
    project_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> ContractResponse:
    """
    Upload a contract file, validate it, persist to storage, and create a DB record.

    The document processing pipeline (text extraction, chunking, embedding) runs
    synchronously in Phase 3. For now, the contract is created with status=pending.
    """
    # Verify project exists and belongs to the user
    project = await _get_project_with_ownership_check(project_id, current_user, db)

    # Validate file
    file_type = _validate_file(filename, content_type, len(file_content))

    # Create contract record first (to get the ID for file path)
    contract = Contract(
        project_id=project.id,
        filename=filename,
        file_path="",  # Will be updated after file save
        file_type=file_type,
        processing_status=ProcessingStatus.PENDING,
    )
    db.add(contract)
    await db.flush()
    await db.refresh(contract)

    # Save file to storage
    file_path = await save_upload(
        file_content=file_content,
        filename=filename,
        user_id=current_user.id,
        project_id=project.id,
        contract_id=contract.id,
    )
    contract.file_path = file_path
    await db.flush()

    logger.info(
        "Contract uploaded: contract_id=%s, project_id=%s, filename=%s",
        contract.id, project.id, filename,
    )

    # Run the document processing pipeline synchronously (AGENT.md Section 3.3)
    await process_contract(
        contract=contract,
        user_id=current_user.id,
        project_id=project.id,
        db=db,
    )

    return ContractResponse.model_validate(contract)


async def list_contracts(
    project_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> ContractListResponse:
    """List all contracts within a project."""
    await _get_project_with_ownership_check(project_id, current_user, db)

    result = await db.execute(
        select(Contract)
        .where(Contract.project_id == project_id)
        .order_by(Contract.uploaded_at.desc())
    )
    contracts = result.scalars().all()

    return ContractListResponse(
        contracts=[ContractResponse.model_validate(c) for c in contracts],
        total=len(contracts),
    )


async def get_contract(
    contract_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> ContractDetailResponse:
    """Get a single contract's details."""
    contract = await _get_contract_with_ownership_check(contract_id, current_user, db)
    return ContractDetailResponse.model_validate(contract)


async def get_contract_file(
    contract_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> tuple[str, str, str]:
    """Get the physical file path, filename, and content type for downloading."""
    contract = await _get_contract_with_ownership_check(contract_id, current_user, db)
    
    # Determine MIME type based on the stored file_type
    content_type = "application/octet-stream"
    if contract.file_type.value == "pdf":
        content_type = "application/pdf"
    elif contract.file_type.value == "docx":
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
    return contract.file_path, contract.filename, content_type


async def delete_contract(
    contract_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> None:
    """Delete a contract, its associated files, and ChromaDB vectors."""
    contract = await _get_contract_with_ownership_check(contract_id, current_user, db)

    # Delete vectors from ChromaDB (must happen before DB row deletion)
    delete_by_contract(contract.id)

    # Delete files from filesystem
    await delete_contract_files(
        user_id=current_user.id,
        project_id=contract.project_id,
        contract_id=contract.id,
    )

    # Delete from DB (cascades to chunks, clauses, risks, etc.)
    await db.delete(contract)
    await db.flush()

    logger.info(
        "Contract deleted: contract_id=%s, project_id=%s",
        contract_id, contract.project_id,
    )


async def search_contracts_by_filename(
    project_id: uuid.UUID,
    query: str,
    current_user: User,
    db: AsyncSession,
) -> ContractListResponse:
    """Search contracts by filename within a project (SQL ILIKE)."""
    await _get_project_with_ownership_check(project_id, current_user, db)

    result = await db.execute(
        select(Contract)
        .where(
            Contract.project_id == project_id,
            Contract.filename.ilike(f"%{query}%"),
        )
        .order_by(Contract.uploaded_at.desc())
    )
    contracts = result.scalars().all()

    return ContractListResponse(
        contracts=[ContractResponse.model_validate(c) for c in contracts],
        total=len(contracts),
    )


# =============================================================================
# Document Processing Pipeline
# =============================================================================

async def process_contract(
    contract: Contract,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    db: AsyncSession,
) -> None:
    """
    Run the full document processing pipeline for a contract.

    Pipeline per AGENT.md Section 9:
    1. Extract raw text (LangChain Loaders)
    2. Clean text (normalize whitespace, strip artifacts)
    3. Chunk text (overlapping, paragraph-respecting)
    4. Generate embeddings (Sentence Transformers, local)
    5. Store vectors in ChromaDB + persist DocumentChunk rows in PostgreSQL
    6. Update contract page_count and processing_status

    On failure, contract is marked with processing_status=failed.
    """
    contract.processing_status = ProcessingStatus.PROCESSING
    await db.flush()

    try:
        # Step 1: Text extraction
        logger.info("Processing pipeline started: contract_id=%s", contract.id)
        extraction = extract_text(contract.file_path, contract.file_type.value)
        contract.page_count = extraction.page_count

        # Step 2: Clean text per page
        cleaned_pages = []
        for page in extraction.pages:
            cleaned = clean_text(page.text)
            if cleaned:
                cleaned_pages.append({
                    "page_number": page.page_number,
                    "text": cleaned,
                })

        if not cleaned_pages:
            raise ProcessingFailedError(
                f"No text content extracted from '{contract.filename}'. "
                "The file may be empty or image-based (OCR not supported)."
            )

        # Step 3: Chunk text
        chunks = chunk_pages(cleaned_pages)

        if not chunks:
            raise ProcessingFailedError(
                f"Text chunking produced no chunks for '{contract.filename}'."
            )

        # Step 4: Generate embeddings
        chunk_texts = [c.text for c in chunks]
        embeddings = generate_embeddings(chunk_texts)

        # Step 5: Store in ChromaDB + persist DocumentChunk rows
        chroma_ids: list[str] = []
        chroma_metadatas: list[dict] = []
        db_chunks: list[DocumentChunk] = []

        for chunk, embedding in zip(chunks, embeddings):
            chroma_id = str(uuid.uuid4())
            chroma_ids.append(chroma_id)
            chroma_metadatas.append({
                "user_id": str(user_id),
                "project_id": str(project_id),
                "contract_id": str(contract.id),
                "page_number": chunk.page_number or 0,
                "chunk_index": chunk.chunk_index,
                "document_type": contract.file_type.value,
            })

            db_chunk = DocumentChunk(
                contract_id=contract.id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                page_number=chunk.page_number,
                chroma_id=chroma_id,
            )
            db_chunks.append(db_chunk)

        # Store vectors in ChromaDB
        store_embeddings(
            chroma_ids=chroma_ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=chroma_metadatas,
        )

        # Persist chunk rows in PostgreSQL
        db.add_all(db_chunks)

        # Step 6: Mark processing as completed
        contract.processing_status = ProcessingStatus.COMPLETED
        await db.flush()

        logger.info(
            "Processing pipeline completed: contract_id=%s, chunks=%d, pages=%d",
            contract.id, len(chunks), contract.page_count,
        )

    except ProcessingFailedError:
        contract.processing_status = ProcessingStatus.FAILED
        await db.flush()
        raise
    except Exception as e:
        contract.processing_status = ProcessingStatus.FAILED
        await db.flush()
        logger.error(
            "Processing pipeline failed: contract_id=%s, error=%s",
            contract.id, str(e), exc_info=True,
        )
        raise ProcessingFailedError(
            f"Document processing failed for '{contract.filename}': {str(e)}"
        )


# =============================================================================
# Internal Helpers
# =============================================================================

async def _get_project_with_ownership_check(
    project_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Project:
    """Load a project and verify the current user owns it."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if project is None:
        raise ResourceNotFoundError("Project", str(project_id))

    if project.user_id != current_user.id:
        raise AuthorizationError("You do not have permission to access this project")

    return project


async def _get_contract_with_ownership_check(
    contract_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> Contract:
    """Load a contract and verify the current user owns its parent project."""
    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()

    if contract is None:
        raise ResourceNotFoundError("Contract", str(contract_id))

    # Verify ownership via the project
    project_result = await db.execute(
        select(Project).where(Project.id == contract.project_id)
    )
    project = project_result.scalar_one_or_none()

    if project is None or project.user_id != current_user.id:
        raise AuthorizationError("You do not have permission to access this contract")

    return contract
