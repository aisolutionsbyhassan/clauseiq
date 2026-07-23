"""
ClauseIQ — Text Chunking Module

Splits cleaned text into overlapping chunks using LangChain's
RecursiveCharacterTextSplitter per the user's LangChain integration request.
"""

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

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


def chunk_pages(
    pages: list[dict],
    chunk_size_tokens: int | None = None,
    chunk_overlap_tokens: int | None = None,
) -> list[Chunk]:
    """
    Chunk text from multiple pages using LangChain, preserving page references.
    """
    chunk_size = (chunk_size_tokens or settings.CHUNK_SIZE_TOKENS) * CHARS_PER_TOKEN
    overlap = (chunk_overlap_tokens or settings.CHUNK_OVERLAP_TOKENS) * CHARS_PER_TOKEN

    # Initialize LangChain's splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    all_chunks: list[Chunk] = []
    global_index = 0

    for page in pages:
        text = page.get("text", "")
        if not text.strip():
            continue
            
        # Use LangChain to split the text
        split_texts = splitter.split_text(text)
        
        for chunk_text_content in split_texts:
            all_chunks.append(
                Chunk(
                    chunk_index=global_index,
                    text=chunk_text_content,
                    page_number=page.get("page_number"),
                )
            )
            global_index += 1

    logger.info("Text chunked via LangChain: %d chunks total", len(all_chunks))
    return all_chunks
