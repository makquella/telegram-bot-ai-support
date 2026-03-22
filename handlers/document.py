"""Document upload handler — indexes files into the RAG vector store."""

import uuid
from pathlib import Path

import structlog
from aiogram import Router, F, types

from config import config
from rag.loader import process_document
from rag.scoping import annotate_documents_for_scope
from rag.vectorstore import vectorstore_manager
from services.documents import validate_chunk_count, validate_document_upload

logger = structlog.get_logger(__name__)
router = Router(name="document")


@router.message(F.document)
async def handle_document(message: types.Message) -> None:
    """Handle uploaded documents: download, chunk, embed, and index.

    Supports PDF, DOCX, and TXT files. After indexing, the user
    can ask questions about the document content via regular chat.
    """
    doc = message.document
    user_id = message.from_user.id
    chat_id = message.chat.id
    filename = Path(doc.file_name or "uploaded_file.txt").name
    source_id = str(uuid.uuid4())

    validation_error = validate_document_upload(filename, doc.mime_type, doc.file_size)
    if validation_error:
        await message.answer(validation_error)
        return

    source_count = await vectorstore_manager.get_source_count(user_id, chat_id)
    if source_count >= config.max_documents_per_chat:
        await message.answer(
            "❌ Достигнут лимит загруженных документов в этом чате. "
            f"Лимит: {config.max_documents_per_chat}."
        )
        return

    msg = await message.answer("📥 Получен файл. Скачиваю и индексирую...")

    config.data_dir.mkdir(parents=True, exist_ok=True)
    temp_path = config.data_dir / f"{uuid.uuid4()}_{filename}"

    try:
        await message.bot.download(doc, destination=str(temp_path))

        docs = await process_document(str(temp_path), filename)
        if not docs:
            await msg.edit_text("❌ Не удалось обработать документ.")
            return

        chunk_validation_error = validate_chunk_count(len(docs))
        if chunk_validation_error:
            await msg.edit_text(chunk_validation_error)
            return

        annotate_documents_for_scope(
            docs,
            user_id=user_id,
            chat_id=chat_id,
            source_id=source_id,
            source_name=filename,
            telegram_file_id=doc.file_id,
            telegram_file_unique_id=doc.file_unique_id,
        )
        count = await vectorstore_manager.add_documents(docs)

        await msg.edit_text(
            f"✅ Файл «{filename}» проиндексирован!\n"
            f"📊 Создано чанков: {count}\n\n"
            "Теперь можете задавать вопросы по содержимому."
        )
    except Exception as e:
        logger.error("Document indexing failed", error=str(e), filename=filename)
        try:
            await msg.edit_text("❌ Ошибка при индексации файла.")
        except Exception:
            await message.answer("❌ Ошибка при индексации файла.")
    finally:
        if temp_path.exists():
            temp_path.unlink()
