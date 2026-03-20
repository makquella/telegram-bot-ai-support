import asyncio
import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config
from handlers.commands import router as commands_router
# from handlers.chat import router as chat_router
# from handlers.voice import router as voice_router
# from handlers.document import router as document_router

logger = structlog.get_logger(__name__)

async def main():
    logger.info("Starting bot in polling mode...")
    
    bot = Bot(
        token=config.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()
    
    dp.include_router(commands_router)
    # dp.include_router(chat_router)
    # dp.include_router(voice_router)
    # dp.include_router(document_router)
    
    # Drop pending updates and start polling
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
