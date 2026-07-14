"""
ClauseIQ — Gemini Client

Thin wrapper around Google's Generative AI SDK for all LLM interactions.
All Gemini calls are isolated behind this module per AGENT.md Section 6.4.
"""

import json

import google.generativeai as genai

from app.config import settings
from app.core.exceptions import AIServiceError
from app.core.logging_config import get_logger

logger = get_logger("gemini_client")

# Module-level flag for initialization
_initialized = False


def _ensure_initialized() -> None:
    """Configure the Gemini API key (once)."""
    global _initialized
    if not _initialized:
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here":
            logger.info("Gemini API key not configured. Using mocked responses.")
            _initialized = True
            return
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _initialized = True
        logger.info("Gemini API configured")


def _get_model(model_name: str = "gemini-2.0-flash") -> genai.GenerativeModel:
    """Get a Gemini generative model instance."""
    _ensure_initialized()
    return genai.GenerativeModel(model_name)


async def generate_text(
    prompt: str,
    system_instruction: str | None = None,
    model_name: str = "gemini-2.0-flash",
    temperature: float = 0.1,
) -> str:
    """
    Generate a text response from Gemini.

    Args:
        prompt: The user prompt.
        system_instruction: Optional system instruction.
        model_name: Gemini model to use.
        temperature: Sampling temperature (low for structured outputs).

    Returns:
        The generated text response.

    Raises:
        AIServiceError: If the Gemini call fails.
    """
    try:
        _ensure_initialized()
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your-gemini-api-key-here":
            if "11 clause categories" in prompt:
                return '{"clauses": [{"clause_type": "payment_terms", "is_present": true, "clause_text": "Net 30 days", "source_chunk_ids": [0]}, {"clause_type": "termination", "is_present": true, "clause_text": "30 days notice", "source_chunk_ids": [0]}, {"clause_type": "confidentiality", "is_present": true, "clause_text": "Standard NDA", "source_chunk_ids": [0]}, {"clause_type": "intellectual_property", "is_present": true, "clause_text": "Vendor owns IP", "source_chunk_ids": [0]}, {"clause_type": "governing_law", "is_present": true, "clause_text": "California", "source_chunk_ids": [0]}, {"clause_type": "liability", "is_present": true, "clause_text": "Capped at fees", "source_chunk_ids": [0]}, {"clause_type": "indemnification", "is_present": true, "clause_text": "Mutual", "source_chunk_ids": [0]}, {"clause_type": "renewal", "is_present": true, "clause_text": "Auto renewal", "source_chunk_ids": [0]}, {"clause_type": "arbitration", "is_present": true, "clause_text": "AAA", "source_chunk_ids": [0]}, {"clause_type": "force_majeure", "is_present": true, "clause_text": "Standard", "source_chunk_ids": [0]}, {"clause_type": "non_compete", "is_present": false, "clause_text": null, "source_chunk_ids": null}]}'
            elif "contract risks" in prompt:
                return '{"risks": [{"risk_type": "unlimited_liability", "is_applicable": false, "severity": null, "explanation": null, "recommendation": null}, {"risk_type": "automatic_renewal", "is_applicable": true, "severity": "medium", "explanation": "Auto renews 30 days before", "recommendation": "Review 60 days before"}, {"risk_type": "missing_termination", "is_applicable": false, "severity": null, "explanation": null, "recommendation": null}, {"risk_type": "missing_confidentiality", "is_applicable": false, "severity": null, "explanation": null, "recommendation": null}, {"risk_type": "missing_intellectual_property", "is_applicable": false, "severity": null, "explanation": null, "recommendation": null}, {"risk_type": "vendor_favorable_jurisdiction", "is_applicable": true, "severity": "low", "explanation": "CA law applies", "recommendation": "Consult CA attorney"}, {"risk_type": "vague_payment_terms", "is_applicable": false, "severity": null, "explanation": null, "recommendation": null}, {"risk_type": "missing_notice_period", "is_applicable": false, "severity": null, "explanation": null, "recommendation": null}]}'
            elif "executive summary" in prompt:
                return '{"important_dates": [{"label": "Start", "date": "Jan 1, 2026", "significance": "Commencement"}], "financial_terms": [{"term": "Fees", "details": "$10k/mo", "impact": "Budget"}], "key_obligations": [{"party": "Vendor", "obligation": "Provide services", "deadline": "Monthly"}], "major_risks": [{"risk": "Auto renewal", "severity": "medium", "summary": "Renews without notice", "action": "Track date"}]}'
            elif "Compare the following two contracts" in prompt:
                return '{"added_clauses": [{"clause_type": "arbitration", "description": "Added AAA arbitration", "significance": "Dispute resolution"}], "removed_clauses": [], "modified_clauses": [{"clause_type": "payment_terms", "before": "Net 30", "after": "Net 45", "significance": "Worse cash flow"}], "changed_obligations": []}'
            elif "Answer the user's question" in prompt:
                return '{"answer": "This is a mocked answer. [Chunk 0, Page 1]", "citations": [{"chunk_index": 0, "page_number": 1, "text_snippet": "mocked snippet"}]}'
            else:
                return '{"mocked": true}'
        
        model = genai.GenerativeModel(
            model_name,
            system_instruction=system_instruction,
            generation_config=genai.GenerationConfig(temperature=temperature),
        )
        response = model.generate_content(prompt)
        result = response.text
        logger.info(
            "Gemini text generated: model=%s, prompt_len=%d, response_len=%d",
            model_name, len(prompt), len(result),
        )
        return result
    except Exception as e:
        logger.error("Gemini text generation failed: %s", str(e), exc_info=True)
        raise AIServiceError(f"Gemini text generation failed: {str(e)}")


async def generate_structured(
    prompt: str,
    system_instruction: str | None = None,
    model_name: str = "gemini-2.0-flash",
    temperature: float = 0.1,
) -> dict:
    """
    Generate a structured JSON response from Gemini.

    The prompt must instruct the model to return valid JSON.
    This function parses the response and returns a dict.

    Args:
        prompt: The user prompt (should request JSON output).
        system_instruction: Optional system instruction.
        model_name: Gemini model to use.
        temperature: Sampling temperature.

    Returns:
        Parsed JSON as a dict.

    Raises:
        AIServiceError: If the Gemini call or JSON parsing fails.
    """
    try:
        raw_text = await generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            model_name=model_name,
            temperature=temperature,
        )

        # Clean up markdown code fences if present
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        result = json.loads(cleaned)
        logger.info("Gemini structured output parsed successfully")
        return result
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse Gemini JSON response: %s\nRaw: %s",
            str(e), raw_text[:500] if raw_text else "empty",
        )
        raise AIServiceError(f"Failed to parse AI response as JSON: {str(e)}")
    except AIServiceError:
        raise
    except Exception as e:
        logger.error("Gemini structured generation failed: %s", str(e), exc_info=True)
        raise AIServiceError(f"Gemini structured generation failed: {str(e)}")
