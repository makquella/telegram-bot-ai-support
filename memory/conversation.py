"""Redis-backed conversation memory with TTL auto-cleanup."""

import json

import redis.asyncio as aioredis
import structlog

from config import config

logger = structlog.get_logger(__name__)


class ConversationMemory:
    """Stores per-user-per-chat conversation history in Redis.

    Messages are stored as JSON-encoded lists with a configurable TTL
    and maximum history length.
    """

    def __init__(self) -> None:
        self.redis = aioredis.from_url(config.redis_url, decode_responses=True)
        self.max_history = config.max_history
        self.ttl = config.memory_ttl

    def _key(self, user_id: int, chat_id: int) -> str:
        return f"smartflow:memory:{user_id}:{chat_id}"

    async def add_message(self, user_id: int, chat_id: int, role: str, content: str) -> None:
        """Append a message to the user's conversation history.

        Args:
            user_id: Telegram user ID.
            chat_id: Telegram chat ID.
            role: Message role — "user" or "assistant".
            content: Message text.
        """
        key = self._key(user_id, chat_id)
        message = json.dumps({"role": role, "content": content})
        try:
            await self.redis.rpush(key, message)
            await self.redis.ltrim(key, -(self.max_history * 2), -1)
            await self.redis.expire(key, self.ttl)
        except Exception as e:
            logger.error("Memory write failed", error=str(e), user_id=user_id, chat_id=chat_id)

    async def get_messages(self, user_id: int, chat_id: int) -> list[dict[str, str]]:
        """Retrieve the user's conversation history.

        Args:
            user_id: Telegram user ID.
            chat_id: Telegram chat ID.

        Returns:
            List of message dicts with "role" and "content" keys.
        """
        key = self._key(user_id, chat_id)
        try:
            raw = await self.redis.lrange(key, 0, -1)
            return [json.loads(msg) for msg in raw]
        except Exception as e:
            logger.error("Memory read failed", error=str(e), user_id=user_id, chat_id=chat_id)
            return []

    async def clear_memory(self, user_id: int, chat_id: int) -> None:
        """Delete the user's conversation history.

        Args:
            user_id: Telegram user ID.
            chat_id: Telegram chat ID.
        """
        key = self._key(user_id, chat_id)
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error("Memory clear failed", error=str(e), user_id=user_id, chat_id=chat_id)


memory = ConversationMemory()
