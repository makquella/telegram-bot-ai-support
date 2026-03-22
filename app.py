"""Webhook entrypoint — run with `uvicorn app:app --host 0.0.0.0 --port 8000`."""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update

from config import config
from handlers.commands import router as commands_router
from handlers.document import router as document_router
from handlers.voice import router as voice_router
from handlers.chat import router as chat_router

logger = structlog.get_logger(__name__)

bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()

# Order matters: specific handlers first, catch-all chat last
dp.include_router(commands_router)
dp.include_router(document_router)
dp.include_router(voice_router)
dp.include_router(chat_router)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Set up and tear down webhook on startup/shutdown."""
    if config.use_webhook and config.webhook_url:
        webhook_info = await bot.get_webhook_info()
        full_url = config.webhook_url + config.webhook_path
        if webhook_info.url != full_url:
            logger.info("Setting webhook", url=full_url)
            await bot.set_webhook(url=full_url)
    yield
    if config.use_webhook:
        logger.info("Deleting webhook")
        await bot.delete_webhook()
    await bot.session.close()


app = FastAPI(lifespan=lifespan, title="SmartFlow AI Bot")


@app.post(config.webhook_path)
async def bot_webhook(request: Request):
    """Process incoming Telegram webhook updates."""
    try:
        data = await request.json()
        update = Update(**data)
        await dp.feed_update(bot=bot, update=update)
        return {"ok": True}
    except Exception as e:
        logger.error("Webhook processing error", error=str(e))
        return {"ok": False}


@app.get("/")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "SmartFlow AI Bot"}


if __name__ == "__main__":
    import uvicorn

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )
    uvicorn.run("app:app", host="0.0.0.0", port=config.port)
