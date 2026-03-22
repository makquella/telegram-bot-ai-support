"""Unit tests for user-scoped document helpers."""

import sys
import unittest
from pathlib import Path

from langchain_core.documents import Document

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.scoping import annotate_documents_for_user, build_user_filter


class ScopingHelpersTestCase(unittest.TestCase):
    def test_annotate_documents_for_user_preserves_existing_metadata(self) -> None:
        docs = [Document(page_content="hello", metadata={"page": 2})]

        annotate_documents_for_user(docs, user_id=42, source_name="brief.pdf")

        self.assertEqual(docs[0].metadata["page"], 2)
        self.assertEqual(docs[0].metadata["user_id"], 42)
        self.assertEqual(docs[0].metadata["source_name"], "brief.pdf")

    def test_build_user_filter_targets_metadata_namespace(self) -> None:
        user_filter = build_user_filter(7)
        condition = user_filter.must[0]

        self.assertEqual(condition.key, "metadata.user_id")
        self.assertEqual(condition.match.value, 7)


if __name__ == "__main__":
    unittest.main()
