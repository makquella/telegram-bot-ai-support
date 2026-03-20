from aiogram import Router, types
from aiogram.filters import Command
import structlog

from memory.conversation import memory
from utils.llm import generate_response

logger = structlog.get_logger(__name__)
router = Router(name="chat")

@router.message()
async def handle_text_message(message: types.Message):
    if not message.text or message.text.startswith('/'):
        # Ignore commands or non-text messages here
        return
        
    user_id = message.from_user.id
    
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Store user message
    await memory.add_message(user_id, "user", message.text)
    
    # Get conversational history
    messages = await memory.get_messages(user_id)
    
    # Generate response
    response_text = await generate_response(messages)
    
    # Store assistant response
    await memory.add_message(user_id, "assistant", response_text)
    
    await message.answer(response_text)
