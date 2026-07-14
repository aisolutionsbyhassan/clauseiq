"""
ClauseIQ — Embedding Generation Module

Wraps Sentence Transformers for local embedding generation
per AGENT.md Section 9.5. No external API dependency for embeddings.
"""

from sentence_transformers import SentenceTransformer

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger("embeddings")

# Module-level singleton to avoid reloading the model on every call
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Load the embedding model lazily (singleton)."""
    global _model
    if _model is None:
        logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL_NAME)
        _model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        logger.info("Embedding model loaded successfully")
    return _model


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate embedding vectors for a list of text strings.

    Args:
        texts: List of text strings to embed.

    Returns:
        List of embedding vectors (each a list of floats).
    """
    if not texts:
        return []

    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False)

    logger.info("Generated %d embeddings (dim=%d)", len(texts), len(embeddings[0]))
    return [emb.tolist() for emb in embeddings]


def generate_single_embedding(text: str) -> list[float]:
    """Generate an embedding for a single text string."""
    result = generate_embeddings([text])
    return result[0] if result else []
