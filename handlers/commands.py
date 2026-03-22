"""Bot command handlers: /start, /help, /clear, /status."""

import structlog
from aiogram import Router, types
from aiogram.filters import Command

from config import config
from memory.conversation import memory
from rag.vectorstore import vectorstore_manager

logger = structlog.get_logger(__name__)
router = Router(name="commands")


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    """Welcome message with feature overview."""
    await message.answer(
        "👋 Привет! Я SmartFlow AI — твой умный Telegram-ассистент.\n\n"
        "💬 Напиши мне что-нибудь — отвечу.\n"
        "🎙 Отправь голосовое — отвечу голосом.\n"
        "📄 Загрузи PDF/DOCX/TXT — проиндексирую и буду отвечать по документу.\n\n"
        "Команды:\n"
        "🧹 /clear — очистить память разговора\n"
        "📊 /status — показать состояние бота\n"
        "❓ /help — помощь"
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message) -> None:
    """Detailed help message."""
    await message.answer(
        "🤖 SmartFlow AI — Помощь\n\n"
        "💬 Текст — напиши любое сообщение, я отвечу.\n"
        "🗣 Голосовое — отправь голосовое сообщение, я распознаю речь, "
        "отвечу текстом и озвучу ответ.\n"
        "📄 Документ — загрузи PDF, DOCX или TXT файл. Я разобью его на части, "
        "проиндексирую, и ты сможешь задавать вопросы по содержимому.\n"
        "🧹 /clear — стереть историю разговора.\n"
        "📊 /status — текущая модель, количество проиндексированных документов."
    )


@router.message(Command("clear"))
async def cmd_clear(message: types.Message) -> None:
    """Clear conversation memory for the current user."""
    await memory.clear_memory(message.from_user.id)
    await message.answer("✅ Память диалога очищена.")


@router.message(Command("status"))
async def cmd_status(message: types.Message) -> None:
    """Show bot status: model, indexed documents, etc."""
    doc_count = await vectorstore_manager.get_doc_count()
    await message.answer(
        "📊 Статус SmartFlow AI\n\n"
        f"— Модель: {config.llm_model}\n"
        f"— Эмбеддинги: {config.embedding_model}\n"
        f"— Whisper: {config.whisper_model}\n"
        f"— Проиндексировано чанков: {doc_count}\n"
        f"— Память: последние {config.max_history} обменов"
    )
