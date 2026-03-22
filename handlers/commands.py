"""Bot command handlers: /start, /help, /clear, /clear_docs, /status."""

import structlog
from aiogram import Router, types
from aiogram.filters import Command

from config import config
from memory.conversation import memory
from rag.vectorstore import vectorstore_manager
from services.health import collect_health

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
        "🗑 /clear_docs — удалить свои загруженные документы\n"
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
        "отвечу текстом и озвучу ответ. Если у тебя есть документы в этом чате, "
        "голосовой запрос тоже сможет использовать их контекст.\n"
        "📄 Документ — загрузи PDF, DOCX или TXT файл. Я разобью его на части, "
        "проиндексирую только для твоего текущего чата, и ты сможешь задавать вопросы по содержимому.\n"
        "🧹 /clear — стереть историю разговора в текущем чате.\n"
        "🗑 /clear_docs — удалить все загруженные тобой документы из текущего чата.\n"
        "📊 /status — текущая модель, здоровье сервисов и статистика документов по текущему чату."
    )


@router.message(Command("clear"))
async def cmd_clear(message: types.Message) -> None:
    """Clear conversation memory for the current user."""
    await memory.clear_memory(message.from_user.id, message.chat.id)
    await message.answer("✅ Память диалога в текущем чате очищена.")


@router.message(Command("clear_docs"))
async def cmd_clear_docs(message: types.Message) -> None:
    """Delete all indexed documents for the current user."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    source_count = await vectorstore_manager.get_source_count(user_id, chat_id)
    deleted_count = await vectorstore_manager.clear_documents(user_id, chat_id)
    if deleted_count:
        await message.answer(
            "✅ Документы текущего чата удалены.\n"
            f"— Документов: {source_count}\n"
            f"— Чанков: {deleted_count}"
        )
        return

    await message.answer("ℹ️ В текущем чате у вас пока нет проиндексированных документов.")


@router.message(Command("status"))
async def cmd_status(message: types.Message) -> None:
    """Show bot status: model, indexed documents, etc."""
    user_id = message.from_user.id
    chat_id = message.chat.id
    health = await collect_health()
    chunk_count = await vectorstore_manager.get_doc_count(user_id, chat_id)
    source_count = await vectorstore_manager.get_source_count(user_id, chat_id)
    await message.answer(
        "📊 Статус SmartFlow AI\n\n"
        f"— Режим: {'webhook' if config.use_webhook else 'polling'}\n"
        f"— Модель: {config.llm_model}\n"
        f"— Эмбеддинги: {config.embedding_model}\n"
        f"— Whisper: {config.whisper_model}\n"
        f"— Redis: {'ok' if health.redis else 'down'}\n"
        f"— Qdrant: {'ok' if health.qdrant else 'down'}\n"
        f"— Документов в этом чате: {source_count}\n"
        f"— Чанков в этом чате: {chunk_count}\n"
        f"— Память: последние {config.max_history} обменов"
    )
