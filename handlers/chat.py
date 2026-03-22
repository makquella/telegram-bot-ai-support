"""Text message handler with RAG-augmented responses."""

import structlog
from aiogram import Router, types

from memory.conversation import memory
from services.conversation import build_inference_messages, build_user_message_content
from utils.llm import generate_response

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
    chat_id = message.chat.id
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    history_messages = await memory.get_messages(user_id, chat_id)
    user_content = await build_user_message_content(
        message.text,
        user_id=user_id,
        chat_id=chat_id,
    )
    messages = build_inference_messages(history_messages, user_content)

    response_text = await generate_response(messages)
    await memory.add_message(user_id, chat_id, "user", message.text)
    await memory.add_message(user_id, chat_id, "assistant", response_text)

    await message.answer(response_text)
