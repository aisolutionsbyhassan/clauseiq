"""
ClauseIQ — ChromaDB Vector Retriever

Handles vector storage and similarity search using LangChain's Chroma wrapper
per the user's LangChain integration request.
"""

import uuid

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import settings
from app.core.logging_config import get_logger
from app.ai.embeddings import get_embedding_model

logger = get_logger("retriever")

# Module-level singleton for LangChain Chroma
_vectorstore: Chroma | None = None


def _get_vectorstore() -> Chroma:
    """Get or create the shared LangChain Chroma vectorstore (lazy init)."""
    global _vectorstore
    if _vectorstore is None:
        logger.info(
            "Initializing LangChain Chroma: persist_dir=%s, collection=%s",
            settings.CHROMA_PERSIST_DIRECTORY,
            settings.CHROMA_COLLECTION_NAME,
        )
        _vectorstore = Chroma(
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=get_embedding_model(),
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            collection_metadata={"hnsw:space": "cosine"},
        )
        logger.info("LangChain Chroma vectorstore ready")
    return _vectorstore


def store_embeddings(
    chroma_ids: list[str],
    embeddings: list[list[float]],  # Note: LangChain computes embeddings automatically if we pass documents, but we maintain signature. We'll bypass pre-computed embeddings and let LangChain compute them, or construct Documents.
    documents: list[str],
    metadatas: list[dict],
) -> None:
    """
    Store embedding vectors in the shared ChromaDB collection via LangChain.
    """
    vectorstore = _get_vectorstore()
    
    # Create LangChain Document objects
    langchain_docs = []
    for doc_text, meta, doc_id in zip(documents, metadatas, chroma_ids):
        langchain_docs.append(Document(page_content=doc_text, metadata=meta, id=doc_id))
    
    # Use LangChain's add_documents (it will compute embeddings internally using our HuggingFace model)
    vectorstore.add_documents(documents=langchain_docs, ids=chroma_ids)
    
    logger.info("Stored %d vectors in LangChain Chroma", len(chroma_ids))


def query_embeddings(
    query_embedding: list[float], # Maintained for signature compatibility, but LangChain's similarity_search takes text.
    n_results: int | None = None,
    where: dict | None = None,
    query_text: str = "", # Added to allow LangChain text search
) -> dict:
    """
    Query the shared ChromaDB collection via LangChain.
    """
    vectorstore = _get_vectorstore()
    k = n_results or settings.RETRIEVAL_TOP_K

    # LangChain's similarity_search takes a string query, so we use query_text or a dummy if not provided (though we really should search by vector if we have it). 
    # LangChain Chroma supports similarity_search_by_vector!
    docs_with_scores = vectorstore.similarity_search_by_vector_with_relevance_scores(
        embedding=query_embedding,
        k=k,
        filter=where,
    )
    
    # Convert LangChain results back to our expected dict format
    # format expected by chat_service: {"ids": [[...]], "documents": [[...]], "distances": [[...]], "metadatas": [[...]]}
    
    ids_batch = []
    docs_batch = []
    distances_batch = []
    metadatas_batch = []
    
    for doc, score in docs_with_scores:
        # doc is a LangChain Document
        # Langchain doesn't return ids directly in the Document object easily without private attributes, but we can return metadata and content.
        ids_batch.append(doc.metadata.get("chunk_id", str(uuid.uuid4()))) # Fallback ID
        docs_batch.append(doc.page_content)
        distances_batch.append(1.0 - score) # Convert relevance score back to distance
        metadatas_batch.append(doc.metadata)

    results = {
        "ids": [ids_batch],
        "documents": [docs_batch],
        "distances": [distances_batch],
        "metadatas": [metadatas_batch]
    }
    
    logger.debug("LangChain Chroma query returned %d results", len(docs_batch))
    return results


def delete_by_contract(contract_id: uuid.UUID) -> None:
    """Delete all vectors associated with a contract."""
    vectorstore = _get_vectorstore()
    # LangChain Chroma delete by filter requires the underlying client
    try:
        collection = vectorstore._collection
        results = collection.get(where={"contract_id": str(contract_id)}, include=[])
        if results and results["ids"]:
            collection.delete(ids=results["ids"])
            logger.info("Deleted %d vectors for contract_id=%s via LangChain", len(results["ids"]), contract_id)
    except Exception as e:
        logger.error("Failed to delete by contract: %s", e)


def delete_by_project(project_id: uuid.UUID) -> None:
    """Delete all vectors associated with a project."""
    vectorstore = _get_vectorstore()
    try:
        collection = vectorstore._collection
        results = collection.get(where={"project_id": str(project_id)}, include=[])
        if results and results["ids"]:
            collection.delete(ids=results["ids"])
            logger.info("Deleted %d vectors for project_id=%s via LangChain", len(results["ids"]), project_id)
    except Exception as e:
        logger.error("Failed to delete by project: %s", e)
