from litellm import acompletion
import structlog
from config import config

logger = structlog.get_logger(__name__)

async def generate_response(messages: list) -> str:
    """
    Generate an LLM response using LiteLLM.
    """
    system_prompt = {
        "role": "system", 
        "content": "You are SmartFlow AI, a helpful, intelligent Telegram assistant. Be concise and helpful in your answers."
    }
    
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, system_prompt)

    try:
        import os
        if config.openai_api_key:
            os.environ["OPENAI_API_KEY"] = config.openai_api_key.get_secret_value()
        if config.groq_api_key:
            os.environ["GROQ_API_KEY"] = config.groq_api_key.get_secret_value()
        if config.gemini_api_key:
            os.environ["GEMINI_API_KEY"] = config.gemini_api_key.get_secret_value()

        response = await acompletion(
            model="gpt-4o-mini", # Could also easily be groq/llama-3.1-70b or gemini/gemini-1.5-pro
            messages=messages,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error("LLM Generation Error", error=str(e))
        return "Sorry, I am having trouble processing your request right now."
