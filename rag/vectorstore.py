from langchain_community.vectorstores import Qdrant
from rag.embedder import get_embeddings
from config import config
import structlog

logger = structlog.get_logger(__name__)

class QdrantStore:
    def __init__(self):
        self.collection_name = "smartflow_docs"

    async def add_documents(self, docs):
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            
            def add_sync():
                import qdrant_client
                sync_client = qdrant_client.QdrantClient(url=config.qdrant_url)
                Qdrant.from_documents(
                    docs, 
                    get_embeddings(), 
                    url=config.qdrant_url, 
                    collection_name=self.collection_name,
                    client=sync_client
                )
            
            await loop.run_in_executor(None, add_sync)
        except Exception as e:
            logger.error("VectorStore Add Error", error=str(e))

vectorstore_manager = QdrantStore()
