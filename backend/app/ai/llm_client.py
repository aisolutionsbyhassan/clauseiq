"""
ClauseIQ — Groq Client (Formerly Gemini Client)

Thin wrapper around Groq SDK for all LLM interactions.
Replaced Gemini with Groq to avoid 429 API limits while keeping function signatures identical.
"""

import json
from groq import AsyncGroq

from app.config import settings
from app.core.exceptions import AIServiceError
from app.core.logging_config import get_logger

logger = get_logger("groq_client")

_client = None


def _get_client() -> AsyncGroq:
    """Get or initialize the AsyncGroq client."""
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your-groq-api-key-here":
            raise AIServiceError("Groq API key is not configured. Please add it to your .env file.")
        _client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _client


async def generate_text(
    prompt: str,
    system_instruction: str | None = None,
    model_name: str = "llama-3.3-70b-versatile",
    temperature: float = 0.1,
) -> str:
    """
    Generate a text response from Groq.
    Maintains exact same signature as original Gemini implementation.
    """
    try:
        client = _get_client()
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
        )
        
        result = response.choices[0].message.content or ""
        logger.info(
            "Groq text generated: model=%s, prompt_len=%d, response_len=%d",
            model_name, len(prompt), len(result),
        )
        return result
    except Exception as e:
        logger.error("Groq text generation failed: %s", str(e), exc_info=True)
        raise AIServiceError(f"Groq text generation failed: {str(e)}")


async def generate_structured(
    prompt: str,
    system_instruction: str | None = None,
    model_name: str = "llama-3.3-70b-versatile",
    temperature: float = 0.1,
) -> dict:
    """
    Generate a structured JSON response from Groq.
    Maintains exact same signature as original Gemini implementation.
    """
    try:
        client = _get_client()
        
        messages = []
        # Groq JSON mode requires the word 'json' in the prompt/system instruction.
        # We enforce it here just in case the template doesn't explicitly have it.
        sys_msg = system_instruction or "You are a helpful AI assistant."
        sys_msg += "\n\nYou MUST return a valid JSON object."
        
        messages.append({"role": "system", "content": sys_msg})
        messages.append({"role": "user", "content": prompt})

        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        
        raw_text = response.choices[0].message.content or ""

        # Clean up markdown code fences if present (sometimes returned even in JSON mode)
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        result = json.loads(cleaned)
        logger.info("Groq structured output parsed successfully")
        return result
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse Groq JSON response: %s\nRaw: %s",
            str(e), raw_text[:500] if raw_text else "empty",
        )
        raise AIServiceError(f"Failed to parse AI response as JSON: {str(e)}")
    except AIServiceError:
        raise
    except Exception as e:
        logger.error("Groq structured generation failed: %s", str(e), exc_info=True)
        raise AIServiceError(f"Groq structured generation failed: {str(e)}")
