"""
ClauseIQ — Text Cleaning Module

Normalizes extracted text per AGENT.md Section 9.3:
- Removes page-break artifacts and decorative separators
- Normalizes whitespace
- Strips repeated headers/footers where detectable
- Preserves legal formatting (numbered clauses, section headers)
"""

import re

from app.core.logging_config import get_logger

logger = get_logger("cleaner")


def clean_text(text: str) -> str:
    """
    Clean extracted text while preserving legal formatting structure.

    Applied transformations:
    1. Remove form feed / page break characters
    2. Normalize line endings
    3. Remove decorative separators (e.g., "======", "------", "****")
    4. Collapse excessive whitespace while preserving paragraph breaks
    5. Strip page number artifacts (standalone numbers on lines)
    6. Remove leading/trailing whitespace from each line
    """
    if not text or not text.strip():
        return ""

    # Remove form feed and vertical tab characters
    text = text.replace("\f", "\n").replace("\v", "\n")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove decorative separators (lines of repeated symbols)
    text = re.sub(r"^[=\-*_~]{3,}\s*$", "", text, flags=re.MULTILINE)

    # Remove standalone page numbers (a line that's just a number)
    text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)

    # Remove common header/footer patterns
    # (e.g., "Page X of Y", "Confidential", repeated company names at top/bottom)
    text = re.sub(
        r"(?i)^\s*page\s+\d+\s*(of\s+\d+)?\s*$", "", text, flags=re.MULTILINE
    )

    # Strip leading/trailing whitespace from each line
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Collapse 3+ consecutive newlines into 2 (preserve paragraph breaks)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces into single space (within lines)
    text = re.sub(r"[ \t]{2,}", " ", text)

    # Final trim
    text = text.strip()

    logger.debug("Text cleaned: %d chars", len(text))
    return text
