"""
ClauseIQ — AI Output Schemas

Pydantic schemas for validating structured AI outputs from Groq.
These are distinct from API request/response schemas per AGENT.md Section 11.
"""

from pydantic import BaseModel, Field


# =============================================================================
# Clause Extraction Schemas
# =============================================================================

class ExtractedClauseOutput(BaseModel):
    """Schema for a single extracted clause from Groq."""
    clause_type: str = Field(description="The clause category identifier")
    is_present: bool = Field(description="Whether this clause type is present in the contract")
    clause_text: str | None = Field(
        default=None,
        description="The extracted clause text/summary, null if not present",
    )
    source_chunk_ids: list[int] | None = Field(
        default=None,
        description="Chunk indices the clause was derived from",
    )


class ClauseExtractionSchema(BaseModel):
    """Full clause extraction output from Groq."""
    clauses: list[ExtractedClauseOutput] = Field(
        description="List of all 11 clause categories with extraction results",
    )


# =============================================================================
# Risk Detection Schemas
# =============================================================================

class DetectedRiskOutput(BaseModel):
    """Schema for a single detected risk from Groq."""
    risk_type: str = Field(description="The risk category identifier")
    is_applicable: bool = Field(description="Whether this risk applies to the contract")
    severity: str | None = Field(
        default=None,
        description="Risk severity: low, medium, or high",
    )
    explanation: str | None = Field(
        default=None,
        description="Why this is a risk, referencing the relevant clause",
    )
    recommendation: str | None = Field(
        default=None,
        description="A concrete, actionable suggestion",
    )


class RiskDetectionSchema(BaseModel):
    """Full risk detection output from Groq."""
    risks: list[DetectedRiskOutput] = Field(
        description="List of all 8 risk categories with detection results",
    )


# =============================================================================
# Executive Summary Schemas
# =============================================================================

class ExecutiveSummarySchema(BaseModel):
    """Structured executive summary output from Groq."""
    important_dates: list[dict] = Field(
        default_factory=list,
        description="Key dates (e.g., start date, end date, renewal deadline)",
    )
    financial_terms: list[dict] = Field(
        default_factory=list,
        description="Financial terms (e.g., payment amounts, penalties)",
    )
    key_obligations: list[dict] = Field(
        default_factory=list,
        description="Main obligations for each party",
    )
    major_risks: list[dict] = Field(
        default_factory=list,
        description="Top risks with severity and recommendation",
    )


# =============================================================================
# Comparison Schemas
# =============================================================================

class ComparisonSchema(BaseModel):
    """Contract comparison output from Groq."""
    added_clauses: list[dict] = Field(
        default_factory=list,
        description="Clauses present in Contract B but not in Contract A",
    )
    removed_clauses: list[dict] = Field(
        default_factory=list,
        description="Clauses present in Contract A but not in Contract B",
    )
    modified_clauses: list[dict] = Field(
        default_factory=list,
        description="Clauses that changed between versions, with before/after",
    )
    changed_obligations: list[dict] = Field(
        default_factory=list,
        description="Obligations that differ between the two contracts",
    )


# =============================================================================
# Chat Schemas
# =============================================================================

class ChatCitation(BaseModel):
    """A source citation for a chat response."""
    chunk_index: int = Field(description="Index of the source chunk")
    page_number: int | None = Field(default=None, description="Page number in the original document")
    text_snippet: str = Field(description="Relevant text from the source chunk")


class ChatResponseSchema(BaseModel):
    """Chat response from Groq with citations."""
    answer: str = Field(description="The answer to the user's question")
    citations: list[ChatCitation] = Field(
        default_factory=list,
        description="Source citations supporting the answer",
    )
