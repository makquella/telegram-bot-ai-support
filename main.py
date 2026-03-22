"""Polling entrypoint — run with `python main.py`."""

import asyncio
import structlog
from aiogram import Bot, Dispatcher

from config import config
from handlers.commands import router as commands_router
from handlers.document import router as document_router
from handlers.voice import router as voice_router
from handlers.chat import router as chat_router

logger = structlog.get_logger(__name__)


async def main() -> None:
    """Start the bot in long-polling mode."""
    logger.info("Starting bot in polling mode...", model=config.llm_model)

    bot = Bot(token=config.bot_token.get_secret_value())
    dp = Dispatcher()

    # Order matters: specific handlers first, catch-all chat last
    dp.include_router(commands_router)
    dp.include_router(document_router)
    dp.include_router(voice_router)
    dp.include_router(chat_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )
    if not config.use_webhook:
        asyncio.run(main())
