from aiogram import Router, types
from aiogram.filters import Command
import structlog

logger = structlog.get_logger(__name__)
router = Router(name="commands")

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Hello! I am SmartFlow AI, your advanced Telegram assistant.\n"
        "You can chat with me, send voice messages, or upload documents for indexing!\n"
        "Use /help to see what I can do."
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🤖 **SmartFlow AI Help**\n\n"
        "🗣️ Send a voice message to get a voice reply.\n"
        "📄 Upload a PDF/DOCX/TXT file and I will index it so you can ask questions.\n"
        "🧹 Use /clear to clear our conversation memory."
    )

@router.message(Command("clear"))
async def cmd_clear(message: types.Message):
    # Memory clearing logic will be connected here later.
    await message.answer("Conversation memory has been cleared.")
