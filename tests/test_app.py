"""Smoke tests for webhook and health routes."""

import os
import sys
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

import app as app_module
from config import config
from services.health import ServiceHealth


class AppRoutesSmokeTestCase(IsolatedAsyncioTestCase):
    async def test_health_endpoint_returns_503_when_dependencies_are_degraded(self) -> None:
        transport = ASGITransport(app=app_module.app)

        with patch.object(
            app_module,
            "collect_health",
            new=AsyncMock(return_value=ServiceHealth(redis=False, qdrant=True)),
        ):
            async with AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                response = await client.get("/health")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "degraded")
        self.assertEqual(response.json()["checks"], {"ok": False, "redis": False, "qdrant": True})

    async def test_webhook_returns_500_when_update_processing_fails(self) -> None:
        transport = ASGITransport(app=app_module.app)

        with patch.object(
            app_module.dp,
            "feed_update",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ):
            async with AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                response = await client.post(config.webhook_path, json={"update_id": 1})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            {"ok": False, "error": "webhook_processing_failed"},
        )
