"""Smoke tests for scoped vector store deletion behavior."""

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

from rag.vectorstore import QdrantStore


class _FakeQdrantClient:
    def __init__(self) -> None:
        self.count_filter = None
        self.points_selector = None

    def count(self, *, collection_name, count_filter, exact):
        self.count_filter = count_filter
        return SimpleNamespace(count=3)

    def delete(self, *, collection_name, points_selector, wait):
        self.points_selector = points_selector


class QdrantStoreSmokeTestCase(IsolatedAsyncioTestCase):
    async def test_clear_documents_uses_source_scoped_filter_for_count_and_delete(self) -> None:
        client = _FakeQdrantClient()
        store = QdrantStore()
        store._get_client = lambda: client
        store._collection_exists = lambda _: True

        deleted = await store.clear_documents(user_id=7, chat_id=1001, source_id="src-2")

        self.assertEqual(deleted, 3)
        self.assertIsNotNone(client.count_filter)
        self.assertIsNotNone(client.points_selector)
        self.assertEqual(
            [condition.key for condition in client.count_filter.must],
            ["metadata.user_id", "metadata.chat_id", "metadata.source_id"],
        )
        self.assertEqual(client.count_filter.must[0].match.value, 7)
        self.assertEqual(client.count_filter.must[1].match.value, 1001)
        self.assertEqual(client.count_filter.must[2].match.value, "src-2")
        self.assertEqual(client.points_selector.must[2].match.value, "src-2")
