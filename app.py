"""Webhook entrypoint — run with `uvicorn app:app --host 0.0.0.0 --port 8000`."""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from aiogram.types import Update

from bootstrap import bot, configure_logging, dp, initialize_bot, shutdown_bot
from config import config
from services.health import collect_health

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Set up and tear down webhook on startup/shutdown."""
    if not config.use_webhook:
        raise RuntimeError("app.py supports only webhook mode. Set USE_WEBHOOK=true.")

    await initialize_bot(bot)
    webhook_info = await bot.get_webhook_info()
    full_url = config.webhook_url + config.webhook_path
    if webhook_info.url != full_url:
        logger.info("Setting webhook", url=full_url)
        await bot.set_webhook(url=full_url)
    yield
    logger.info("Deleting webhook")
    await bot.delete_webhook()
    await shutdown_bot(bot)


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
@app.get("/health")
async def health_check(response: Response):
    """Health check endpoint with dependency readiness."""
    health = await collect_health()
    response.status_code = 200 if health.ok else 503
    return {
        "status": "ok" if health.ok else "degraded",
        "service": "SmartFlow AI Bot",
        "mode": "webhook",
        "checks": health.to_dict(),
    }


if __name__ == "__main__":
    import uvicorn

    configure_logging()
    uvicorn.run("app:app", host="0.0.0.0", port=config.port)
