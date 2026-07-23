"""
ClauseIQ — Text Extraction Module

Extracts raw text from PDF and DOCX files using LangChain's Document Loaders
(PyMuPDFLoader and Docx2txtLoader) per the user's LangChain integration request.
"""

from dataclasses import dataclass, field
from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader

from app.core.logging_config import get_logger

logger = get_logger("extractor")


@dataclass
class PageContent:
    """Represents extracted text from a single page."""
    page_number: int
    text: str


@dataclass
class ExtractionResult:
    """Result of text extraction from a document."""
    pages: list[PageContent] = field(default_factory=list)
    page_count: int = 0
    full_text: str = ""


def extract_from_pdf(file_path: str) -> ExtractionResult:
    """
    Extract text from a PDF file using LangChain's PyMuPDFLoader.
    """
    loader = PyMuPDFLoader(file_path)
    langchain_docs = loader.load()
    
    pages: list[PageContent] = []
    for doc in langchain_docs:
        text = doc.page_content
        # PyMuPDFLoader usually stores page in metadata as 0-indexed, but we'll use 1-indexed
        page_num = doc.metadata.get("page", len(pages)) + 1
        if text.strip():
            pages.append(PageContent(page_number=page_num, text=text))

    full_text = "\n\n".join(p.text for p in pages)
    result = ExtractionResult(
        pages=pages,
        page_count=len(langchain_docs),
        full_text=full_text,
    )

    logger.info(
        "PDF extracted via LangChain: path=%s, pages=%d, chars=%d",
        file_path, len(pages), len(full_text),
    )
    return result


def extract_from_docx(file_path: str) -> ExtractionResult:
    """
    Extract text from a DOCX file using LangChain's Docx2txtLoader.
    """
    loader = Docx2txtLoader(file_path)
    langchain_docs = loader.load()
    
    # Docx2txtLoader loads the entire document into a single Document object
    full_text = langchain_docs[0].page_content if langchain_docs else ""
    pages = [PageContent(page_number=1, text=full_text)] if full_text.strip() else []

    result = ExtractionResult(
        pages=pages,
        page_count=1,
        full_text=full_text,
    )

    logger.info(
        "DOCX extracted via LangChain: path=%s, chars=%d",
        file_path, len(full_text),
    )
    return result


def extract_text(file_path: str, file_type: str) -> ExtractionResult:
    """
    Dispatch extraction based on file type.
    """
    if file_type == "pdf":
        return extract_from_pdf(file_path)
    elif file_type == "docx":
        return extract_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
