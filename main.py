"""Polling entrypoint — run with `python main.py`."""

import asyncio
import structlog

from bootstrap import bot, configure_logging, dp, initialize_bot, shutdown_bot
from config import config

logger = structlog.get_logger(__name__)


async def main() -> None:
    """Start the bot in long-polling mode."""
    if config.use_webhook:
        raise RuntimeError("main.py supports only polling mode. Set USE_WEBHOOK=false.")

    logger.info("Starting bot in polling mode...", model=config.llm_model)

    await bot.delete_webhook(drop_pending_updates=True)
    await initialize_bot(bot)
    try:
        await dp.start_polling(bot)
    finally:
        await shutdown_bot(bot)


if __name__ == "__main__":
    configure_logging()
    asyncio.run(main())
