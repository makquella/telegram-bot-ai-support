"""Qdrant vector store management for document indexing."""

import asyncio
import structlog
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config import config
from rag.embedder import get_embeddings

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

    async def get_doc_count(self) -> int:
        """Return the number of indexed vectors in the collection."""
        loop = asyncio.get_running_loop()

        def _count():
            client = self._get_client()
            existing = [c.name for c in client.get_collections().collections]
            if self.collection_name not in existing:
                return 0
            info = client.get_collection(self.collection_name)
            return info.points_count or 0

        try:
            return await loop.run_in_executor(None, _count)
        except Exception:
            return 0


vectorstore_manager = QdrantStore()
