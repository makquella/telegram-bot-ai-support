"""Qdrant vector store management for document indexing."""

import asyncio
import structlog
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config import config
from rag.embedder import get_embeddings
from rag.scoping import build_user_filter

logger = structlog.get_logger(__name__)


class QdrantStore:
    """Manages document storage and retrieval in Qdrant."""

    def __init__(self) -> None:
        self.collection_name = config.rag_collection
        self.vector_size = config.rag_vector_size

    def _get_client(self) -> QdrantClient:
        return QdrantClient(url=config.qdrant_url)

    def _ensure_collection(self, client: QdrantClient) -> None:
        """Create the collection if it doesn't exist."""
        existing = [c.name for c in client.get_collections().collections]
        if self.collection_name not in existing:
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )

    async def add_documents(self, docs: list) -> int:
        """Index documents into the vector store.

        Args:
            docs: List of LangChain Document objects to index.

        Returns:
            Number of documents indexed.
        """
        loop = asyncio.get_running_loop()

        def _add():
            client = self._get_client()
            self._ensure_collection(client)
            store = QdrantVectorStore(
                client=client,
                collection_name=self.collection_name,
                embedding=get_embeddings(),
            )
            store.add_documents(docs)
            return len(docs)

        try:
            return await loop.run_in_executor(None, _add)
        except Exception as e:
            logger.error("VectorStore add failed", error=str(e))
            return 0

    async def get_doc_count(self, user_id: int | None = None) -> int:
        """Return the number of indexed vectors in the collection."""
        loop = asyncio.get_running_loop()

        def _count():
            client = self._get_client()
            existing = [c.name for c in client.get_collections().collections]
            if self.collection_name not in existing:
                return 0
            if user_id is None:
                info = client.get_collection(self.collection_name)
                return info.points_count or 0

            result = client.count(
                collection_name=self.collection_name,
                count_filter=build_user_filter(user_id),
                exact=True,
            )
            return result.count

        try:
            return await loop.run_in_executor(None, _count)
        except Exception:
            return 0

    async def clear_user_documents(self, user_id: int) -> int:
        """Delete indexed documents for a specific user and return deleted count."""
        loop = asyncio.get_running_loop()

        def _clear() -> int:
            client = self._get_client()
            existing = [c.name for c in client.get_collections().collections]
            if self.collection_name not in existing:
                return 0

            user_filter = build_user_filter(user_id)
            count_result = client.count(
                collection_name=self.collection_name,
                count_filter=user_filter,
                exact=True,
            )
            if not count_result.count:
                return 0

            client.delete(
                collection_name=self.collection_name,
                points_selector=user_filter,
                wait=True,
            )
            return count_result.count

        try:
            return await loop.run_in_executor(None, _clear)
        except Exception as e:
            logger.error("VectorStore clear failed", error=str(e), user_id=user_id)
            return 0


vectorstore_manager = QdrantStore()
