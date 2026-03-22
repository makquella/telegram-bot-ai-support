"""Unit tests for document validation policy."""

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

from config import config
from services.documents import validate_chunk_count, validate_document_upload


class DocumentPolicyTestCase(unittest.TestCase):
    def test_rejects_large_document(self) -> None:
        error = validate_document_upload(
            "brief.pdf",
            "application/pdf",
            config.max_document_size_bytes + 1,
        )

        self.assertIn("Файл слишком большой", error)

    def test_rejects_unsupported_mime_type(self) -> None:
        error = validate_document_upload(
            "brief.pdf",
            "application/zip",
            1024,
        )

        self.assertIn("Неподдерживаемый MIME-тип", error)

    def test_rejects_excessive_chunk_count(self) -> None:
        error = validate_chunk_count(config.max_chunks_per_document + 1)

        self.assertIn("слишком объёмный", error)
