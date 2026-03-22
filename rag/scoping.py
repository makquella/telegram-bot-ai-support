"""Helpers for user-scoped document storage and retrieval."""

from qdrant_client import models as qdrant_models

USER_ID_METADATA_KEY = "user_id"
CHAT_ID_METADATA_KEY = "chat_id"
SOURCE_ID_METADATA_KEY = "source_id"
SOURCE_NAME_METADATA_KEY = "source_name"
TELEGRAM_FILE_ID_METADATA_KEY = "telegram_file_id"
TELEGRAM_FILE_UNIQUE_ID_METADATA_KEY = "telegram_file_unique_id"
METADATA_PREFIX = "metadata"


def annotate_documents_for_scope(
    docs: list,
    user_id: int,
    chat_id: int,
    source_id: str,
    source_name: str | None = None,
    telegram_file_id: str | None = None,
    telegram_file_unique_id: str | None = None,
) -> list:
    """Attach user-scoping metadata to LangChain documents."""
    for doc in docs:
        metadata = dict(getattr(doc, "metadata", {}) or {})
        metadata[USER_ID_METADATA_KEY] = user_id
        metadata[CHAT_ID_METADATA_KEY] = chat_id
        metadata[SOURCE_ID_METADATA_KEY] = source_id
        if source_name:
            metadata.setdefault(SOURCE_NAME_METADATA_KEY, source_name)
        if telegram_file_id:
            metadata.setdefault(TELEGRAM_FILE_ID_METADATA_KEY, telegram_file_id)
        if telegram_file_unique_id:
            metadata.setdefault(TELEGRAM_FILE_UNIQUE_ID_METADATA_KEY, telegram_file_unique_id)
        doc.metadata = metadata
    return docs


def _match_condition(key: str, value: int | str) -> qdrant_models.FieldCondition:
    return qdrant_models.FieldCondition(
        key=f"{METADATA_PREFIX}.{key}",
        match=qdrant_models.MatchValue(value=value),
    )


def build_scope_filter(
    user_id: int,
    chat_id: int,
    source_id: str | None = None,
) -> qdrant_models.Filter:
    """Build a Qdrant filter that limits queries to one user-chat scope."""
    conditions = [
        _match_condition(USER_ID_METADATA_KEY, user_id),
        _match_condition(CHAT_ID_METADATA_KEY, chat_id),
    ]
    if source_id:
        conditions.append(_match_condition(SOURCE_ID_METADATA_KEY, source_id))

    return qdrant_models.Filter(must=conditions)
