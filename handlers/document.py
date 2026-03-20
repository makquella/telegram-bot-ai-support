import os
from aiogram import Router, F, types
import structlog
import uuid
import aiofiles
from rag.loader import process_document
from rag.vectorstore import vectorstore_manager

logger = structlog.get_logger(__name__)
router = Router(name="document")

@router.message(F.document)
async def handle_document(message: types.Message):
    doc = message.document
    filename = doc.file_name or "uploaded_file.txt"
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in ['.txt', '.pdf', '.docx']:
        await message.answer("Please upload a .txt, .pdf, or .docx file.")
        return

    msg = await message.answer("📥 Received. Downloading and indexing...")

    data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)
    temp_path = os.path.join(data_dir, f"{uuid.uuid4()}_{filename}")

    try:
        await message.bot.download(doc, destination=temp_path)
        
        # Process and chunk
        docs = await process_document(temp_path, filename)
        if not docs:
            await msg.edit_text("❌ Failed to process the document.")
            return

        # Embed & Store
        await vectorstore_manager.add_documents(docs)
        
        await msg.edit_text(f"✅ File indexed successfully! You can now ask questions about `{filename}`.")
    except Exception as e:
        logger.error("Document Indexing Error", error=str(e))
        await msg.edit_text("❌ An error occurred while indexing the file.")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
