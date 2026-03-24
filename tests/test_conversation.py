"""Unit tests for shared conversation helpers."""

import sys
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.conversation import build_inference_messages, build_user_message_content


class ConversationHelpersTestCase(IsolatedAsyncioTestCase):
    async def test_returns_raw_text_when_rag_is_disabled(self) -> None:
        async def retriever(query: str, user_id: int, chat_id: int) -> str:
            return "ignored"

        content = await build_user_message_content(
            "Что по срокам?",
            user_id=1,
            chat_id=101,
            use_rag=False,
            retriever=retriever,
        )

        self.assertEqual(content, "Что по срокам?")

    async def test_returns_augmented_text_when_context_exists(self) -> None:
        async def retriever(query: str, user_id: int, chat_id: int) -> str:
            return "Срок выполнения — 5 рабочих дней."

        content = await build_user_message_content(
            "Что по срокам?",
            user_id=42,
            chat_id=1001,
            retriever=retriever,
        )

        self.assertIn("Контекст из документов:", content)
        self.assertIn("Срок выполнения — 5 рабочих дней.", content)
        self.assertIn("Вопрос пользователя: Что по срокам?", content)

    async def test_returns_raw_text_when_context_is_empty(self) -> None:
        async def retriever(query: str, user_id: int, chat_id: int) -> str:
            return ""

        content = await build_user_message_content(
            "Что по срокам?",
            user_id=7,
            chat_id=5,
            retriever=retriever,
        )

        self.assertEqual(content, "Что по срокам?")

    async def test_builds_inference_messages_without_mutating_history(self) -> None:
        history = [
            {"role": "user", "content": "Привет"},
            {"role": "assistant", "content": "Здравствуйте"},
        ]

        messages = build_inference_messages(
            history,
            "Контекст из документов:\n...\n\nВопрос пользователя: Что по срокам?",
        )

        self.assertEqual(len(messages), 3)
        self.assertEqual(history[-1]["content"], "Здравствуйте")
        self.assertEqual(messages[-1]["role"], "user")
        self.assertIn("Контекст из документов:", messages[-1]["content"])
