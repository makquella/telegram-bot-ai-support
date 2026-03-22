"""Qdrant vector store management for document indexing."""

import asyncio
from collections.abc import Iterable

import structlog
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config import config
from rag.embedder import get_embeddings
from rag.scoping import SOURCE_ID_METADATA_KEY, build_scope_filter

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

    def _collection_exists(self, client: QdrantClient) -> bool:
        existing = [c.name for c in client.get_collections().collections]
        return self.collection_name in existing

    def _iter_source_ids(self, client: QdrantClient, user_id: int, chat_id: int) -> Iterable[str]:
        offset = None
        while True:
            records, offset = client.scroll(
                collection_name=self.collection_name,
                scroll_filter=build_scope_filter(user_id, chat_id),
                limit=100,
                with_payload=True,
                with_vectors=False,
                offset=offset,
            )
            for record in records:
                metadata = (record.payload or {}).get("metadata", {})
                source_id = metadata.get(SOURCE_ID_METADATA_KEY)
                if source_id:
                    yield source_id
            if offset is None:
                break

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

    async def get_doc_count(
        self,
        user_id: int | None = None,
        chat_id: int | None = None,
        source_id: str | None = None,
    ) -> int:
        """Return the number of indexed vectors in the collection."""
        loop = asyncio.get_running_loop()

        def _count():
            client = self._get_client()
            if not self._collection_exists(client):
                return 0
            if user_id is None or chat_id is None:
                info = client.get_collection(self.collection_name)
                return info.points_count or 0

            result = client.count(
                collection_name=self.collection_name,
                count_filter=build_scope_filter(user_id, chat_id, source_id=source_id),
                exact=True,
            )
            return result.count

        try:
            return await loop.run_in_executor(None, _count)
        except Exception as e:
            logger.error(
                "VectorStore count failed",
                error=str(e),
                user_id=user_id,
                chat_id=chat_id,
                source_id=source_id,
            )
            return 0

    async def get_source_count(self, user_id: int, chat_id: int) -> int:
        """Return the number of indexed document sources for a user-chat scope."""
        loop = asyncio.get_running_loop()

        def _count_sources() -> int:
            client = self._get_client()
            if not self._collection_exists(client):
                return 0
            return len(set(self._iter_source_ids(client, user_id, chat_id)))

        try:
            return await loop.run_in_executor(None, _count_sources)
        except Exception as e:
            logger.error("VectorStore source count failed", error=str(e), user_id=user_id, chat_id=chat_id)
            return 0

    async def clear_documents(
        self,
        user_id: int,
        chat_id: int,
        source_id: str | None = None,
    ) -> int:
        """Delete indexed documents for a specific scope and return deleted chunks."""
        loop = asyncio.get_running_loop()

        def _clear() -> int:
            client = self._get_client()
            if not self._collection_exists(client):
                return 0

            scope_filter = build_scope_filter(user_id, chat_id, source_id=source_id)
            count_result = client.count(
                collection_name=self.collection_name,
                count_filter=scope_filter,
                exact=True,
            )
            if not count_result.count:
                return 0

            client.delete(
                collection_name=self.collection_name,
                points_selector=scope_filter,
                wait=True,
            )
            return count_result.count

        try:
            return await loop.run_in_executor(None, _clear)
        except Exception as e:
            logger.error(
                "VectorStore clear failed",
                error=str(e),
                user_id=user_id,
                chat_id=chat_id,
                source_id=source_id,
            )
            return 0


vectorstore_manager = QdrantStore()
