from langchain_openai import OpenAIEmbeddings
from config import config

def get_embeddings():
    # Uses OpenAI embeddings by default
    import os
    if config.openai_api_key:
        os.environ["OPENAI_API_KEY"] = config.openai_api_key.get_secret_value()
    return OpenAIEmbeddings()
