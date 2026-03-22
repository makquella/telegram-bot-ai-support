"""Embedding model configuration for RAG pipeline."""

import os
from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import config


@lru_cache(maxsize=1)
def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Return a cached instance of the configured embedding model.

    Uses Google Generative AI embeddings via the Gemini API key.
    The instance is created once and reused for all subsequent calls.
    """
    if config.gemini_api_key:
        os.environ["GOOGLE_API_KEY"] = config.gemini_api_key.get_secret_value()
    return GoogleGenerativeAIEmbeddings(model=config.embedding_model)
