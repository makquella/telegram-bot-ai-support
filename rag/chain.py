"""RAG retrieval chain — searches indexed documents for relevant context."""

import asyncio
import structlog
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from config import config
from rag.embedder import get_embeddings
from rag.scoping import build_user_filter

logger = structlog.get_logger(__name__)


async def retrieve_context(query: str, user_id: int, top_k: int | None = None) -> str:
    """Retrieve relevant document context for a user query.

    Args:
        query: The user's question or message.
        user_id: Telegram user ID used to isolate document search.
        top_k: Number of results to return (defaults to config.rag_top_k).

    Returns:
        Concatenated text from the most relevant document chunks,
        or an empty string if no documents are indexed.
    """
    if top_k is None:
        top_k = config.rag_top_k

    loop = asyncio.get_running_loop()

    def _search() -> str:
        client = QdrantClient(url=config.qdrant_url)
        existing = [c.name for c in client.get_collections().collections]
        if config.rag_collection not in existing:
            return ""

        store = QdrantVectorStore(
            client=client,
            collection_name=config.rag_collection,
            embedding=get_embeddings(),
        )
        docs = store.similarity_search(query, k=top_k, filter=build_user_filter(user_id))
        return "\n\n".join(doc.page_content for doc in docs) if docs else ""

    try:
        return await loop.run_in_executor(None, _search)
    except Exception as e:
        logger.error("Context retrieval failed", error=str(e))
        return ""
