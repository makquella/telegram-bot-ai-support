"""Document loader and text splitter for RAG pipeline."""

import os
import asyncio
import structlog
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import config

logger = structlog.get_logger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".docx"}

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=config.rag_chunk_size,
    chunk_overlap=config.rag_chunk_overlap,
    length_function=len,
)

_LOADERS = {
    ".pdf": PyPDFLoader,
    ".txt": TextLoader,
    ".docx": Docx2txtLoader,
}


async def process_document(file_path: str, filename: str) -> list:
    """Load a document and split it into chunks for indexing.

    Args:
        file_path: Path to the downloaded file on disk.
        filename: Original filename (used to detect extension).

    Returns:
        List of LangChain Document chunks, or empty list on failure.
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext not in _LOADERS:
        logger.warning("Unsupported file format", extension=ext)
        return []

    loop = asyncio.get_running_loop()

    def _load_and_split():
        loader_cls = _LOADERS[ext]
        documents = loader_cls(file_path).load()
        return _splitter.split_documents(documents)

    try:
        return await loop.run_in_executor(None, _load_and_split)
    except Exception as e:
        logger.error("Document loading failed", error=str(e), filename=filename)
        return []
