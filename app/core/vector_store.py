"""PostgreSQL vector store service."""

from functools import lru_cache

from async_lru import alru_cache
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.v2.async_vectorstore import AsyncPGVectorStore
from langchain_postgres.v2.engine import PGEngine
from pydantic import SecretStr

from app.config.settings import SETTINGS
from app.utils.database import get_asyncpg_engine


@lru_cache
def _get_embeddings():
    """Get embeddings instance."""
    return OpenAIEmbeddings(
        api_key=SecretStr(SETTINGS.openai_api_key),
        model=SETTINGS.openai_embed_model,
    )


@alru_cache
async def aget_vector_store() -> AsyncPGVectorStore:
    """Get vector store instance."""
    engine = PGEngine.from_engine(get_asyncpg_engine())
    return await AsyncPGVectorStore.create(
        engine=engine,
        table_name="embeddings",
        embedding_service=_get_embeddings(),
        schema_name=SETTINGS.database_schema,
    )


@alru_cache
async def aget_vector_retriever():
    vector_store = await aget_vector_store()
    return vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "score_threshold": SETTINGS.rag_score_threshold,
            "k": SETTINGS.rag_top_k,
        },
    )


@tool(response_format="content_and_artifact")
async def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    vector_store = await aget_vector_store()
    retrieved_docs = await vector_store.asimilarity_search_with_score(
        query=query,
        k=SETTINGS.rag_top_k,
        filter=None,
    )
    serialized = "\n\n".join(
        (
            f"Source: {document.metadata}\nContent: {document.page_content}\nScore: {score:.4f}"
        )
        for document, score in retrieved_docs
    )
    return serialized, retrieved_docs