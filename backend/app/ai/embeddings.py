"""
ClauseIQ — Embedding Generation Module

Wraps LangChain's HuggingFaceEmbeddings for local embedding generation
per the user's LangChain integration request.
"""

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger("embeddings")

# Module-level singleton to avoid reloading the model on every call
_model: HuggingFaceEmbeddings | None = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    """Load the LangChain embedding model lazily (singleton)."""
    global _model
    if _model is None:
        logger.info("Loading LangChain HuggingFaceEmbeddings model: %s", settings.EMBEDDING_MODEL_NAME)
        _model = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
        logger.info("LangChain Embedding model loaded successfully")
    return _model


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embedding vectors for a list of text strings using LangChain.
    """
    if not texts:
        return []

    model = get_embedding_model()
    embeddings = model.embed_documents(texts)

    logger.info("Generated %d embeddings via LangChain", len(texts))
    return embeddings


def generate_single_embedding(text: str) -> list[float]:
    """Generate an embedding for a single text string using LangChain."""
    model = get_embedding_model()
    return model.embed_query(text)
