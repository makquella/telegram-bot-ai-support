from rag.embedder import get_embeddings
from langchain_community.vectorstores import Qdrant
from config import config
import structlog

logger = structlog.get_logger(__name__)

async def retrieve_context(query: str, top_k: int = 3) -> str:
    """Retrieve relevant context for a given query."""
    try:
        import qdrant_client
        import asyncio
        loop = asyncio.get_running_loop()
        
        def search():
            sync_client = qdrant_client.QdrantClient(url=config.qdrant_url)
            store = Qdrant(
                client=sync_client,
                collection_name="smartflow_docs",
                embeddings=get_embeddings()
            )
            return store.similarity_search(query, k=top_k)

        docs = await loop.run_in_executor(None, search)
        
        if docs:
            return "\n\n".join([doc.page_content for doc in docs])
        return ""
    except Exception as e:
        logger.error("Context Retrieval Error", error=str(e))
        return ""
