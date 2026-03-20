import json
import redis.asyncio as aioredis
from config import config

class ConversationMemory:
    def __init__(self):
        self.redis = aioredis.from_url(config.redis_url, decode_responses=True)
        self.max_history = 15

    def _get_key(self, user_id: int) -> str:
        return f"memory:user:{user_id}"

    async def add_message(self, user_id: int, role: str, content: str):
        key = self._get_key(user_id)
        message = json.dumps({"role": role, "content": content})
        await self.redis.rpush(key, message)
        # Keep last N messages. Since 1 exchange = 2 messages, let's keep max_history * 2
        await self.redis.ltrim(key, -self.max_history * 2, -1)

    async def get_messages(self, user_id: int) -> list:
        key = self._get_key(user_id)
        messages_json = await self.redis.lrange(key, 0, -1)
        return [json.loads(msg) for msg in messages_json]

    async def clear_memory(self, user_id: int):
        key = self._get_key(user_id)
        await self.redis.delete(key)

memory = ConversationMemory()
