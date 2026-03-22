"""Helpers for user-scoped document storage and retrieval."""

from qdrant_client import models as qdrant_models

USER_ID_METADATA_KEY = "user_id"
SOURCE_NAME_METADATA_KEY = "source_name"
METADATA_PREFIX = "metadata"


def annotate_documents_for_user(docs: list, user_id: int, source_name: str | None = None) -> list:
    """Attach user-scoping metadata to LangChain documents."""
    for doc in docs:
        metadata = dict(getattr(doc, "metadata", {}) or {})
        metadata[USER_ID_METADATA_KEY] = user_id
        if source_name:
            metadata.setdefault(SOURCE_NAME_METADATA_KEY, source_name)
        doc.metadata = metadata
    return docs


def build_user_filter(user_id: int) -> qdrant_models.Filter:
    """Build a Qdrant filter that limits queries to a single user."""
    return qdrant_models.Filter(
        must=[
            qdrant_models.FieldCondition(
                key=f"{METADATA_PREFIX}.{USER_ID_METADATA_KEY}",
                match=qdrant_models.MatchValue(value=user_id),
            )
        ]
    )
