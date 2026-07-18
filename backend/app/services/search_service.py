"""
ClauseIQ — Semantic Search Service

Implements vector-based semantic search per AGENT.md Section 10.6.
Pure vector-retrieval feature — no Gemini call required.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import generate_single_embedding
from app.ai.llm_client import generate_text
from app.ai.retriever import query_embeddings
from app.config import settings
from app.core.exceptions import AuthorizationError, ResourceNotFoundError
from app.core.logging_config import get_logger
from app.models.contract import Contract
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.models.user import User
from app.schemas.search import SearchResponse, SearchResultItem

logger = get_logger("search_service")


async def semantic_search(
    query: str,
    project_id: uuid.UUID,
    current_user: User,
    db: AsyncSession,
) -> SearchResponse:
    """
    Perform semantic search across all contracts in a project.

    Pipeline per AGENT.md Section 10.6:
    1. Embed the query
    2. Similarity search in ChromaDB filtered by project_id
    3. Join results back to Contract rows for display metadata
    """
    # Verify project ownership
    project_result = await db.execute(select(Project).where(Project.id == project_id))
    project = project_result.scalar_one_or_none()
    if project is None:
        raise ResourceNotFoundError("Project", str(project_id))
    if project.user_id != current_user.id:
        raise AuthorizationError("You do not have permission to access this project")

    # Step 1: Query Expansion (HyDE)
    # Expand short keyword queries into rich semantic sentences for better dense retrieval
    expansion_system = (
        "You are an expert legal assistant. Your task is to take a user's search query and "
        "rewrite it into a rich, descriptive hypothetical legal clause or sentence that answers the query. "
        "This helps with semantic vector search. "
        "Rule 1: Output ONLY the expanded sentence. No conversational filler. "
        "Rule 2: If the query is already a long, descriptive sentence, return it as is."
    )
    
    try:
        # Use low temperature for deterministic expansion
        expanded_query = await generate_text(
            prompt=f"User Query: {query}", 
            system_instruction=expansion_system, 
            temperature=0.1
        )
        logger.info("Query expansion: '%s' -> '%s'", query, expanded_query)
    except Exception as e:
        logger.error(f"Query expansion failed, falling back to original query: {e}")
        expanded_query = query

    # Step 2: Embed the expanded query
    query_embedding = generate_single_embedding(expanded_query)

    # Step 3: Similarity search in ChromaDB
    results = query_embeddings(
        query_embedding=query_embedding,
        n_results=settings.RETRIEVAL_TOP_K,
        where={"project_id": str(project_id)},
    )

    # Step 3: Build response with contract metadata
    search_items: list[SearchResultItem] = []
    # Store full text mapping for accurate AI synthesis (fixes truncation bug)
    synthesis_context_items: list[tuple[SearchResultItem, str]] = []

    if results["ids"] and results["ids"][0]:
        for i, chroma_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            document = results["documents"][0][i] if results["documents"] else ""
            distance = results["distances"][0][i] if results["distances"] else 0.0

            # Convert distance to similarity (ChromaDB cosine distance: lower = more similar)
            similarity = 1.0 - distance

            contract_id_str = metadata.get("contract_id", "")
            if not contract_id_str:
                continue

            # Look up contract filename
            contract_result = await db.execute(
                select(Contract.filename)
                .where(Contract.id == uuid.UUID(contract_id_str))
            )
            row = contract_result.first()
            contract_filename = row[0] if row else "Unknown"

            # Truncate text snippet for display
            snippet = document[:300] + "..." if len(document) > 300 else document

            item = SearchResultItem(
                contract_id=uuid.UUID(contract_id_str),
                contract_filename=contract_filename,
                chunk_index=metadata.get("chunk_index", 0),
                page_number=metadata.get("page_number"),
                text_snippet=snippet,
                similarity_score=round(similarity, 4),
            )
            search_items.append(item)
            synthesis_context_items.append((item, document))

    # Sort by similarity descending
    search_items.sort(key=lambda x: x.similarity_score, reverse=True)
    synthesis_context_items.sort(key=lambda x: x[0].similarity_score, reverse=True)

    # Step 4: AI Synthesis
    ai_summary = None
    if synthesis_context_items:
        # Build context for the LLM using FULL chunks, not truncated snippets
        context_text = "\n\n".join([
            f"Document: {item.contract_filename}\nFull Text Context:\n{full_text}" 
            for item, full_text in synthesis_context_items[:5]
        ])
        
        system_prompt = (
            "You are a legal search assistant. Summarize the retrieved evidence to answer the user's query.\n"
            "Rules:\n"
            "1. Be concise (1-3 sentences).\n"
            "2. Remain factual based ONLY on the evidence.\n"
            "3. Avoid speculation.\n"
            "4. Do NOT use conversational filler (e.g., 'Based on the context').\n"
            "5. Do NOT mention chunk IDs or similarity scores."
        )
        
        user_prompt = f"Query: {query}\n\nEvidence:\n{context_text}"
        
        try:
            ai_summary = await generate_text(prompt=user_prompt, system_instruction=system_prompt, temperature=0.1)
        except Exception as e:
            logger.error(f"Search synthesis failed: {e}")
            ai_summary = "Failed to generate AI summary for these results."

    return SearchResponse(
        results=search_items,
        total=len(search_items),
        query=query,
        ai_summary=ai_summary,
    )
