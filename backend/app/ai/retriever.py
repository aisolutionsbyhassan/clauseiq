"""
ClauseIQ — ChromaDB Vector Retriever

Handles vector storage and similarity search using a single shared
ChromaDB collection with metadata filtering per AGENT.md Section 6.5.
"""

import uuid

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger("retriever")

# Module-level singleton for ChromaDB client
_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None


def _get_collection() -> chromadb.Collection:
    """Get or create the shared ChromaDB collection (lazy init)."""
    global _client, _collection
    if _collection is None:
        logger.info(
            "Initializing ChromaDB: persist_dir=%s, collection=%s",
            settings.CHROMA_PERSIST_DIRECTORY,
            settings.CHROMA_COLLECTION_NAME,
        )
        _client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection ready: %d vectors", _collection.count())
    return _collection


def store_embeddings(
    chroma_ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict],
) -> None:
    """
    Store embedding vectors in the shared ChromaDB collection.

    Args:
        chroma_ids: Unique IDs for each vector.
        embeddings: Embedding vectors.
        documents: The text content of each chunk.
        metadatas: Metadata dicts (user_id, project_id, contract_id, page_number, chunk_index).
    """
    collection = _get_collection()
    collection.add(
        ids=chroma_ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    logger.info("Stored %d vectors in ChromaDB", len(chroma_ids))


def query_embeddings(
    query_embedding: list[float],
    n_results: int | None = None,
    where: dict | None = None,
) -> dict:
    """
    Query the shared ChromaDB collection by vector similarity.

    Args:
        query_embedding: The query vector.
        n_results: Number of results to return (defaults to RETRIEVAL_TOP_K).
        where: Metadata filter dict (e.g., {"contract_id": "..."}).

    Returns:
        ChromaDB query result dict with ids, documents, distances, metadatas.
    """
    collection = _get_collection()
    k = n_results or settings.RETRIEVAL_TOP_K

    query_kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        query_kwargs["where"] = where

    results = collection.query(**query_kwargs)
    logger.debug("ChromaDB query returned %d results", len(results["ids"][0]) if results["ids"] else 0)
    return results


def delete_by_contract(contract_id: uuid.UUID) -> None:
    """Delete all vectors associated with a contract."""
    collection = _get_collection()
    # Get all IDs for this contract
    results = collection.get(
        where={"contract_id": str(contract_id)},
        include=[],
    )
    if results["ids"]:
        collection.delete(ids=results["ids"])
        logger.info(
            "Deleted %d vectors for contract_id=%s",
            len(results["ids"]), contract_id,
        )


def delete_by_project(project_id: uuid.UUID) -> None:
    """Delete all vectors associated with a project."""
    collection = _get_collection()
    results = collection.get(
        where={"project_id": str(project_id)},
        include=[],
    )
    if results["ids"]:
        collection.delete(ids=results["ids"])
        logger.info(
            "Deleted %d vectors for project_id=%s",
            len(results["ids"]), project_id,
        )
