"""Shared bootstrap helpers for bot startup, logging, and command registration."""

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
import structlog

from config import config
from handlers.chat import router as chat_router
from handlers.commands import router as commands_router
from handlers.document import router as document_router
from handlers.voice import router as voice_router
from services.health import collect_health

BOT_COMMANDS = [
    BotCommand(command="start", description="Запустить и показать возможности"),
    BotCommand(command="help", description="Показать справку"),
    BotCommand(command="status", description="Проверить модель и сервисы"),
    BotCommand(command="clear", description="Очистить память диалога"),
    BotCommand(command="clear_docs", description="Удалить загруженные документы"),
]


def configure_logging() -> None:
    """Configure structured JSON logging."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        cache_logger_on_first_use=True,
    )


configure_logging()
logger = structlog.get_logger(__name__)


def create_bot() -> Bot:
    """Create a Telegram bot instance from configuration."""
    return Bot(token=config.bot_token.get_secret_value())


def create_dispatcher() -> Dispatcher:
    """Create and configure the dispatcher with all routers."""
    dispatcher = Dispatcher()

    # Order matters: specific handlers first, catch-all chat last.
    dispatcher.include_router(commands_router)
    dispatcher.include_router(document_router)
    dispatcher.include_router(voice_router)
    dispatcher.include_router(chat_router)
    return dispatcher


async def initialize_bot(bot: Bot) -> None:
    """Run startup tasks shared by polling and webhook modes."""
    config.data_dir.mkdir(parents=True, exist_ok=True)
    await bot.set_my_commands(BOT_COMMANDS)

    health = await collect_health(log_failures=True)
    logger.info(
        "Startup checks completed",
        mode="webhook" if config.use_webhook else "polling",
        redis=health.redis,
        qdrant=health.qdrant,
        data_dir=str(config.data_dir),
        model=config.llm_model,
    )


async def shutdown_bot(bot: Bot) -> None:
    """Close bot resources gracefully."""
    await bot.session.close()


bot = create_bot()
dp = create_dispatcher()
