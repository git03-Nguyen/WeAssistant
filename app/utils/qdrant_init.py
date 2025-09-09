"""Qdrant collection initialization utilities."""

from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config.settings import get_settings


def get_embedding_dimension(model_name: str) -> int:
    """Get embedding dimensions based on model name."""
    return 3072 if "large" in model_name else 1536


async def ensure_qdrant_collection(
    collection_name: Optional[str] = None,
    qdrant_url: Optional[str] = None,
    embedding_model: Optional[str] = None,
) -> bool:
    """
    Ensure Qdrant collection exists with proper configuration.

    Args:
        collection_name: Name of the collection to create
        qdrant_url: Qdrant server URL
        embedding_model: OpenAI embedding model name

    Returns:
        True if collection exists or was created successfully
    """
    try:
        settings = get_settings()

        # Use provided values or fall back to settings
        collection_name = collection_name or settings.qdrant_collection
        qdrant_url = qdrant_url or settings.qdrant_url
        embedding_model = embedding_model or settings.openai_embed_model

        if not qdrant_url:
            print("⚠️ Qdrant URL not configured, skipping collection initialization")
            return False

        # Initialize Qdrant client
        client = QdrantClient(url=qdrant_url)

        # Get embedding dimensions
        embedding_dimension = get_embedding_dimension(embedding_model)

        # Check if collection exists
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]

        if collection_name not in collection_names:
            print(f"📊 Creating Qdrant collection '{collection_name}'...")
            client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=embedding_dimension,
                    distance=models.Distance.COSINE,
                ),
            )
            print(f"✅ Qdrant collection '{collection_name}' created successfully")
        else:
            print(f"✅ Qdrant collection '{collection_name}' already exists")

        return True

    except Exception as e:
        print(f"⚠️ Failed to ensure Qdrant collection: {e}")
        return False


async def drop_qdrant_collection(
    collection_name: Optional[str] = None,
    qdrant_url: Optional[str] = None,
) -> bool:
    """
    Drop Qdrant collection.

    Args:
        collection_name: Name of the collection to drop
        qdrant_url: Qdrant server URL

    Returns:
        True if collection was dropped successfully
    """
    try:
        settings = get_settings()

        collection_name = collection_name or settings.qdrant_collection
        qdrant_url = qdrant_url or settings.qdrant_url

        if not qdrant_url:
            print("⚠️ Qdrant URL not configured")
            return False

        client = QdrantClient(url=qdrant_url)

        # Check if collection exists
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]

        if collection_name in collection_names:
            client.delete_collection(collection_name)
            print(f"✅ Qdrant collection '{collection_name}' dropped successfully")
        else:
            print(f"⚠️ Qdrant collection '{collection_name}' does not exist")

        return True

    except Exception as e:
        print(f"⚠️ Failed to drop Qdrant collection: {e}")
        return False


async def recreate_qdrant_collection(
    collection_name: Optional[str] = None,
    qdrant_url: Optional[str] = None,
    embedding_model: Optional[str] = None,
) -> bool:
    """
    Recreate Qdrant collection (drop and create).

    Args:
        collection_name: Name of the collection to recreate
        qdrant_url: Qdrant server URL
        embedding_model: OpenAI embedding model name

    Returns:
        True if collection was recreated successfully
    """
    try:
        # Drop existing collection
        await drop_qdrant_collection(collection_name, qdrant_url)

        # Create new collection
        return await ensure_qdrant_collection(
            collection_name, qdrant_url, embedding_model
        )

    except Exception as e:
        print(f"⚠️ Failed to recreate Qdrant collection: {e}")
        return False
