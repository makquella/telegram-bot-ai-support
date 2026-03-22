"""Text message handler with RAG-augmented responses."""

import structlog
from aiogram import Router, types

from memory.conversation import memory
from utils.llm import generate_response
from rag.chain import retrieve_context

logger = structlog.get_logger(__name__)
router = Router(name="chat")


@router.message()
async def handle_text_message(message: types.Message) -> None:
    """Handle incoming text messages.

    Retrieves relevant context from indexed documents (if any),
    prepends it to the user message, and generates an LLM response.
    """
    if not message.text or message.text.startswith("/"):
        return

    user_id = message.from_user.id
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Retrieve RAG context (silent on failure)
    context = ""
    try:
        context = await retrieve_context(message.text, user_id=user_id)
    except Exception:
        pass

    # Build user content with optional context
    user_content = message.text
    if context:
        user_content = (
            f"Контекст из документов:\n{context}\n\n"
            f"Вопрос пользователя: {message.text}"
        )

    await memory.add_message(user_id, "user", user_content)
    messages = await memory.get_messages(user_id)

    response_text = await generate_response(messages)
    await memory.add_message(user_id, "assistant", response_text)

    await message.answer(response_text)
