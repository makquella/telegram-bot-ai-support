import os
import aiofiles
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
import structlog

logger = structlog.get_logger(__name__)

async def process_document(file_path: str, filename: str) -> list:
    """Load a document and return its content as chunks/documents."""
    ext = os.path.splitext(filename)[1].lower()
    
    try:
        # Langchain loaders are synchronous, we run them in an executor.
        import asyncio
        loop = asyncio.get_running_loop()
        
        def load():
            if ext == '.pdf':
                return PyPDFLoader(file_path).load_and_split()
            elif ext == '.txt':
                return TextLoader(file_path).load_and_split()
            elif ext == '.docx':
                return Docx2txtLoader(file_path).load_and_split()
            else:
                raise ValueError("Unsupported format")

        docs = await loop.run_in_executor(None, load)
        return docs
    except Exception as e:
        logger.error("Document Loading Error", error=str(e))
        return []
