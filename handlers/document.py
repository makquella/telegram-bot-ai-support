"""Document upload handler — indexes files into the RAG vector store."""

import uuid
from pathlib import Path

import structlog
from aiogram import Router, F, types

from config import config
from rag.loader import process_document, SUPPORTED_EXTENSIONS
from rag.scoping import annotate_documents_for_user
from rag.vectorstore import vectorstore_manager

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
    filename = Path(doc.file_name or "uploaded_file.txt").name
    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        await message.answer(f"❌ Неподдерживаемый формат. Поддерживаются: {supported}")
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

        annotate_documents_for_user(docs, user_id=user_id, source_name=filename)
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
