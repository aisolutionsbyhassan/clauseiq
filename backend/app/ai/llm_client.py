"""
ClauseIQ — Groq Client (Formerly Gemini Client)

Wraps LangChain's ChatGroq for all LLM interactions
per the user's LangChain integration request.
"""

import json

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.core.exceptions import AIServiceError
from app.core.logging_config import get_logger

logger = get_logger("groq_client")


def _get_chat_model(model_name: str, temperature: float, **kwargs) -> ChatGroq:
    """Initialize the LangChain ChatGroq model."""
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your-groq-api-key-here":
        raise AIServiceError("Groq API key is not configured. Please add it to your .env file.")
    return ChatGroq(
        api_key=settings.GROQ_API_KEY, 
        model=model_name, 
        temperature=temperature, 
        **kwargs
    )


async def generate_text(
    prompt: str,
    system_instruction: str | None = None,
    model_name: str = "llama-3.3-70b-versatile",
    temperature: float = 0.1,
) -> str:
    """
    Generate a text response from Groq using LangChain.
    """
    try:
        chat = _get_chat_model(model_name, temperature)
        
        messages = []
        if system_instruction:
            messages.append(SystemMessage(content=system_instruction))
        messages.append(HumanMessage(content=prompt))

        response = await chat.ainvoke(messages)
        result = response.content
        
        logger.info(
            "LangChain ChatGroq text generated: model=%s, response_len=%d",
            model_name, len(result),
        )
        return result
    except Exception as e:
        logger.error("LangChain ChatGroq text generation failed: %s", str(e), exc_info=True)
        raise AIServiceError(f"LangChain ChatGroq text generation failed: {str(e)}")


async def generate_structured(
    prompt: str,
    system_instruction: str | None = None,
    model_name: str = "llama-3.3-70b-versatile",
    temperature: float = 0.1,
) -> dict:
    """
    Generate a structured JSON response from Groq using LangChain.
    """
    try:
        # LangChain allows passing model_kwargs for specific provider features like JSON mode
        chat = _get_chat_model(
            model_name, 
            temperature, 
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        
        sys_msg = system_instruction or "You are a helpful AI assistant."
        sys_msg += "\n\nYou MUST return a valid JSON object."
        
        messages = [
            SystemMessage(content=sys_msg),
            HumanMessage(content=prompt)
        ]

        response = await chat.ainvoke(messages)
        raw_text = response.content

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
        logger.info("LangChain ChatGroq structured output parsed successfully")
        return result
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse LangChain ChatGroq JSON response: %s\nRaw: %s",
            str(e), raw_text[:500] if raw_text else "empty",
        )
        raise AIServiceError(f"Failed to parse AI response as JSON: {str(e)}")
    except AIServiceError:
        raise
    except Exception as e:
        logger.error("LangChain ChatGroq structured generation failed: %s", str(e), exc_info=True)
        raise AIServiceError(f"LangChain ChatGroq structured generation failed: {str(e)}")
