"""Health checks for infrastructure dependencies."""

import asyncio
from dataclasses import dataclass

import redis.asyncio as aioredis
import structlog
from qdrant_client import QdrantClient

from config import config

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ServiceHealth:
    """Runtime health snapshot for infrastructure services."""

    redis: bool
    qdrant: bool

    @property
    def ok(self) -> bool:
        """Return True when all required services are reachable."""
        return self.redis and self.qdrant

    def to_dict(self) -> dict[str, bool]:
        """Serialize health information for API responses."""
        return {
            "ok": self.ok,
            "redis": self.redis,
            "qdrant": self.qdrant,
        }


async def check_redis(log_failures: bool = False) -> bool:
    """Return True when Redis is reachable."""
    client = aioredis.from_url(config.redis_url, decode_responses=True)
    try:
        await client.ping()
        return True
    except Exception as e:
        if log_failures:
            logger.warning("Redis health check failed", error=str(e), url=config.redis_url)
        return False
    finally:
        await client.aclose()


async def check_qdrant(log_failures: bool = False) -> bool:
    """Return True when Qdrant is reachable."""
    loop = asyncio.get_running_loop()

    def _probe() -> None:
        client = QdrantClient(url=config.qdrant_url)
        try:
            client.get_collections()
        finally:
            close = getattr(client, "close", None)
            if callable(close):
                close()

    try:
        await loop.run_in_executor(None, _probe)
        return True
    except Exception as e:
        if log_failures:
            logger.warning("Qdrant health check failed", error=str(e), url=config.qdrant_url)
        return False


async def collect_health(log_failures: bool = False) -> ServiceHealth:
    """Run all dependency checks in parallel."""
    redis_ok, qdrant_ok = await asyncio.gather(
        check_redis(log_failures=log_failures),
        check_qdrant(log_failures=log_failures),
    )
    return ServiceHealth(redis=redis_ok, qdrant=qdrant_ok)
