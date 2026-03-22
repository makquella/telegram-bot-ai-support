"""Unit tests for configuration validation."""

import os
import sys
import unittest
from pathlib import Path

from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

from config import Settings


class SettingsValidationTestCase(unittest.TestCase):
    def test_webhook_path_is_normalized(self) -> None:
        settings = Settings(
            bot_token="123456:TEST_TOKEN",
            gemini_api_key="test-gemini-key",
            webhook_path="telegram-hook",
        )

        self.assertEqual(settings.webhook_path, "/telegram-hook")

    def test_webhook_mode_requires_public_url(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(
                bot_token="123456:TEST_TOKEN",
                gemini_api_key="test-gemini-key",
                use_webhook=True,
                webhook_url=None,
            )

    def test_openai_model_requires_openai_api_key(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(
                bot_token="123456:TEST_TOKEN",
                gemini_api_key="test-gemini-key",
                llm_model="openai/gpt-4o-mini",
                openai_api_key=None,
            )


if __name__ == "__main__":
    unittest.main()
