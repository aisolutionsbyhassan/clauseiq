"""
ClauseIQ — Text Chunking Module

Splits cleaned text into overlapping chunks per AGENT.md Section 9.4:
- Target size: CHUNK_SIZE_TOKENS (~500 tokens, approximated as ~4 chars/token)
- Overlap: CHUNK_OVERLAP_TOKENS (50 tokens)
- Respects paragraph boundaries where possible
"""

from dataclasses import dataclass

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger("chunker")

# Approximate token-to-character ratio (conservative: 1 token ≈ 4 chars)
CHARS_PER_TOKEN = 4


@dataclass
class Chunk:
    """A single text chunk with metadata."""
    chunk_index: int
    text: str
    page_number: int | None  # Best-effort page assignment


def _estimate_tokens(text: str) -> int:
    """Rough token count estimate based on character count."""
    return len(text) // CHARS_PER_TOKEN


def chunk_text(
    text: str,
    page_number: int | None = None,
    chunk_size_tokens: int | None = None,
    chunk_overlap_tokens: int | None = None,
) -> list[Chunk]:
    """
    Split text into overlapping chunks, respecting paragraph boundaries.

    Args:
        text: The cleaned text to chunk.
        page_number: Page number to assign to chunks (for PDFs with page tracking).
        chunk_size_tokens: Target chunk size in tokens (defaults to config).
        chunk_overlap_tokens: Overlap between chunks in tokens (defaults to config).

    Returns:
        List of Chunk objects with index, text, and page reference.
    """
    if not text or not text.strip():
        return []

    chunk_size = (chunk_size_tokens or settings.CHUNK_SIZE_TOKENS) * CHARS_PER_TOKEN
    overlap = (chunk_overlap_tokens or settings.CHUNK_OVERLAP_TOKENS) * CHARS_PER_TOKEN

    # Split into paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[Chunk] = []
    current_chunk_parts: list[str] = []
    current_length = 0
    chunk_index = 0

    for paragraph in paragraphs:
        para_len = len(paragraph)

        # If a single paragraph exceeds chunk size, split it by sentences
        if para_len > chunk_size:
            # Flush current chunk first
            if current_chunk_parts:
                chunk_text_content = "\n\n".join(current_chunk_parts)
                chunks.append(Chunk(
                    chunk_index=chunk_index,
                    text=chunk_text_content,
                    page_number=page_number,
                ))
                chunk_index += 1
                # Keep overlap content
                current_chunk_parts = _get_overlap_parts(
                    current_chunk_parts, overlap
                )
                current_length = sum(len(p) for p in current_chunk_parts)

            # Split large paragraph by sentences
            sentences = _split_into_sentences(paragraph)
            for sentence in sentences:
                if current_length + len(sentence) > chunk_size and current_chunk_parts:
                    chunk_text_content = "\n\n".join(current_chunk_parts)
                    chunks.append(Chunk(
                        chunk_index=chunk_index,
                        text=chunk_text_content,
                        page_number=page_number,
                    ))
                    chunk_index += 1
                    current_chunk_parts = _get_overlap_parts(
                        current_chunk_parts, overlap
                    )
                    current_length = sum(len(p) for p in current_chunk_parts)

                current_chunk_parts.append(sentence)
                current_length += len(sentence)

        elif current_length + para_len > chunk_size and current_chunk_parts:
            # Current chunk is full — flush it
            chunk_text_content = "\n\n".join(current_chunk_parts)
            chunks.append(Chunk(
                chunk_index=chunk_index,
                text=chunk_text_content,
                page_number=page_number,
            ))
            chunk_index += 1
            # Keep overlap content
            current_chunk_parts = _get_overlap_parts(current_chunk_parts, overlap)
            current_length = sum(len(p) for p in current_chunk_parts)
            current_chunk_parts.append(paragraph)
            current_length += para_len
        else:
            current_chunk_parts.append(paragraph)
            current_length += para_len

    # Flush remaining content
    if current_chunk_parts:
        chunk_text_content = "\n\n".join(current_chunk_parts)
        chunks.append(Chunk(
            chunk_index=chunk_index,
            text=chunk_text_content,
            page_number=page_number,
        ))

    logger.info(
        "Text chunked: %d chunks from %d chars (page=%s)",
        len(chunks), len(text), page_number,
    )
    return chunks


def chunk_pages(
    pages: list[dict],
    chunk_size_tokens: int | None = None,
    chunk_overlap_tokens: int | None = None,
) -> list[Chunk]:
    """
    Chunk text from multiple pages, preserving page references.

    Args:
        pages: List of dicts with 'page_number' and 'text' keys.

    Returns:
        Flat list of all chunks with correct page assignments.
    """
    all_chunks: list[Chunk] = []
    global_index = 0

    for page in pages:
        page_chunks = chunk_text(
            text=page["text"],
            page_number=page["page_number"],
            chunk_size_tokens=chunk_size_tokens,
            chunk_overlap_tokens=chunk_overlap_tokens,
        )
        # Re-index to be globally sequential
        for chunk in page_chunks:
            chunk.chunk_index = global_index
            all_chunks.append(chunk)
            global_index += 1

    return all_chunks


def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences (rough heuristic for legal text)."""
    import re
    # Split on period followed by space and capital letter, or newline
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [s.strip() for s in sentences if s.strip()]


def _get_overlap_parts(parts: list[str], overlap_chars: int) -> list[str]:
    """Get the trailing parts that fit within the overlap size."""
    if not parts or overlap_chars <= 0:
        return []

    total = 0
    overlap_parts: list[str] = []
    for part in reversed(parts):
        total += len(part)
        if total > overlap_chars:
            break
        overlap_parts.insert(0, part)

    return overlap_parts
