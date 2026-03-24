"""Document validation and policy helpers."""

from pathlib import Path

from config import config
from rag.loader import SUPPORTED_EXTENSIONS

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


def validate_document_upload(
    filename: str,
    mime_type: str | None,
    file_size: int | None,
) -> str | None:
    """Validate a Telegram document before downloading and indexing it."""
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        return f"❌ Неподдерживаемый формат. Поддерживаются: {supported}"

    if mime_type and mime_type not in SUPPORTED_MIME_TYPES:
        supported = ", ".join(sorted(SUPPORTED_MIME_TYPES))
        return f"❌ Неподдерживаемый MIME-тип. Допустимы: {supported}"

    if file_size and file_size > config.max_document_size_bytes:
        return f"❌ Файл слишком большой. Лимит: {config.max_document_size_mb} MB."

    return None


def validate_chunk_count(chunk_count: int) -> str | None:
    """Validate the number of chunks produced from a document."""
    if chunk_count > config.max_chunks_per_document:
        return (
            "❌ Документ слишком объёмный после разбиения. "
            f"Лимит: {config.max_chunks_per_document} чанков."
        )
    return None
