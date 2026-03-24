"""LLM integration via LiteLLM — supports Gemini, OpenAI, Groq."""

import os

import structlog
from litellm import acompletion

from config import config

logger = structlog.get_logger(__name__)

# Set API keys once at module level
if config.openai_api_key:
    os.environ["OPENAI_API_KEY"] = config.openai_api_key.get_secret_value()
if config.groq_api_key:
    os.environ["GROQ_API_KEY"] = config.groq_api_key.get_secret_value()
if config.gemini_api_key:
    os.environ["GEMINI_API_KEY"] = config.gemini_api_key.get_secret_value()


async def generate_response(messages: list[dict[str, str]]) -> str:
    """Generate an LLM response from conversation history.

    Injects the system prompt if not already present, then calls the
    configured model via LiteLLM.

    Args:
        messages: Conversation history as list of {"role": ..., "content": ...}.

    Returns:
        Generated text response or a fallback error message.
    """
    system_prompt = {"role": "system", "content": config.system_prompt}

    if not messages or messages[0].get("role") != "system":
        messages = [system_prompt, *messages]

    try:
        response = await acompletion(
            model=config.llm_model,
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error("LLM generation failed", error=str(e), model=config.llm_model)
        return "Извините, произошла ошибка при генерации ответа. Попробуйте ещё раз."
