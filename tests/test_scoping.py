"""Unit tests for user-scoped document helpers."""

import sys
import unittest
from pathlib import Path

from langchain_core.documents import Document

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.scoping import annotate_documents_for_scope, build_scope_filter


class ScopingHelpersTestCase(unittest.TestCase):
    def test_annotate_documents_for_scope_preserves_existing_metadata(self) -> None:
        docs = [Document(page_content="hello", metadata={"page": 2})]

        annotate_documents_for_scope(
            docs,
            user_id=42,
            chat_id=99,
            source_id="src-1",
            source_name="brief.pdf",
            telegram_file_id="file-1",
            telegram_file_unique_id="uniq-1",
        )

        self.assertEqual(docs[0].metadata["page"], 2)
        self.assertEqual(docs[0].metadata["user_id"], 42)
        self.assertEqual(docs[0].metadata["chat_id"], 99)
        self.assertEqual(docs[0].metadata["source_id"], "src-1")
        self.assertEqual(docs[0].metadata["source_name"], "brief.pdf")
        self.assertEqual(docs[0].metadata["telegram_file_id"], "file-1")
        self.assertEqual(docs[0].metadata["telegram_file_unique_id"], "uniq-1")

    def test_build_scope_filter_targets_user_chat_and_source(self) -> None:
        scope_filter = build_scope_filter(7, 1001, source_id="src-2")
        user_condition, chat_condition, source_condition = scope_filter.must

        self.assertEqual(user_condition.key, "metadata.user_id")
        self.assertEqual(user_condition.match.value, 7)
        self.assertEqual(chat_condition.key, "metadata.chat_id")
        self.assertEqual(chat_condition.match.value, 1001)
        self.assertEqual(source_condition.key, "metadata.source_id")
        self.assertEqual(source_condition.match.value, "src-2")


if __name__ == "__main__":
    unittest.main()
