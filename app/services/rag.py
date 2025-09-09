"""Optimized RAG service for document ingestion and retrieval."""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import FieldCondition, Filter, MatchValue

from app.config.settings import get_settings
from app.core.exceptions import RAGServiceError


class RAGService:
    """Optimized service for RAG operations with caching and cost reduction."""

    def __init__(self):
        self.settings = get_settings()
        self.qdrant_client = QdrantClient(url=self.settings.qdrant_url)
        self.embeddings = OpenAIEmbeddings(
            model=self.settings.openai_embed_model,
        )
        self.collection_name = self.settings.qdrant_collection
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Smaller chunks for better precision
            chunk_overlap=100,  # Reduced overlap to save storage
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
        )

        # In-memory cache for recent queries
        self._query_cache = {}
        self._cache_ttl = timedelta(minutes=10)

        # Initialize vector store
        self.vector_store = Qdrant(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embeddings=self.embeddings,
        )

        # Ensure collection exists
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Ensure the Qdrant collection exists."""
        try:
            collections = self.qdrant_client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=1536,  # OpenAI embedding dimension
                        distance=models.Distance.COSINE,
                    ),
                )
        except Exception as e:
            print(f"Warning: Could not ensure collection exists: {e}")

    def _get_cache_key(self, query: str, metadata_filter: Optional[Dict] = None) -> str:
        """Generate cache key for query."""
        cache_data = {"query": query, "filter": metadata_filter or {}}
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()

    def _get_cached_result(self, cache_key: str) -> Optional[List[Document]]:
        """Get cached result if valid."""
        if cache_key in self._query_cache:
            cached_item = self._query_cache[cache_key]
            if datetime.now() - cached_item["timestamp"] < self._cache_ttl:
                return cached_item["result"]
            else:
                del self._query_cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, result: List[Document]) -> None:
        """Cache query result."""
        if len(self._query_cache) > 100:  # Limit cache size
            oldest_key = min(
                self._query_cache.keys(),
                key=lambda k: self._query_cache[k]["timestamp"],
            )
            del self._query_cache[oldest_key]

        self._query_cache[cache_key] = {"result": result, "timestamp": datetime.now()}

    async def ingest_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """
        Optimized document ingestion with reduced storage.

        Args:
            content: Document content
            metadata: Document metadata

        Returns:
            Document ID
        """
        try:
            # Generate unique document ID
            doc_id = str(uuid.uuid4())

            # Split into optimized chunks
            chunks = self.text_splitter.split_text(content)

            # Create documents with minimal metadata
            documents = []
            for i, chunk in enumerate(chunks):
                doc_metadata = {
                    "document_id": doc_id,
                    "chunk_index": i,
                    "user_id": metadata.get("user_id", "unknown"),
                    **metadata,
                }
                documents.append(Document(page_content=chunk, metadata=doc_metadata))

            # Add to vector store
            await self.vector_store.aadd_documents(documents)

            return doc_id

        except Exception as e:
            raise RAGServiceError(f"Failed to ingest document: {str(e)}")

    async def remove_document(
        self, document_id: str, user_id: Optional[int] = None
    ) -> bool:
        """
        Remove document by ID.

        Args:
            document_id: Document ID to remove
            user_id: Optional user ID for filtering

        Returns:
            Success status
        """
        try:
            # Use vector store delete method which handles the complexity
            await self.vector_store.adelete(
                ids=[document_id] if document_id else [],
                filter={"document_id": document_id, "user_id": user_id}
                if user_id
                else {"document_id": document_id},
            )

            return True

        except Exception:
            # If that fails, try a simple approach
            try:
                # Get all points and filter client-side (less efficient but works)
                all_points = self.qdrant_client.scroll(
                    collection_name=self.collection_name,
                    limit=10000,
                    with_payload=True,
                    with_vectors=False,
                )[0]

                points_to_delete = []
                for point in all_points:
                    payload = point.payload or {}
                    if payload.get("document_id") == document_id and (
                        user_id is None or payload.get("user_id") == user_id
                    ):
                        points_to_delete.append(point.id)

                if points_to_delete:
                    from qdrant_client.models import PointIdsList

                    self.qdrant_client.delete(
                        collection_name=self.collection_name,
                        points_selector=PointIdsList(points=points_to_delete),
                    )

                return True
            except Exception as e2:
                raise RAGServiceError(f"Failed to remove document: {str(e2)}")

    async def search_documents(
        self,
        query: str,
        user_id: Optional[int] = None,
        limit: int = 5,
        min_score: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Search documents with caching and optimization.

        Args:
            query: Search query
            user_id: Optional user ID for filtering
            limit: Maximum results
            min_score: Minimum similarity score

        Returns:
            List of search results
        """
        try:
            # Check cache first
            metadata_filter = {"user_id": str(user_id)} if user_id else None
            cache_key = self._get_cache_key(query, metadata_filter)

            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": doc.metadata.get("relevance_score", 0.8),
                    }
                    for doc in cached_result[:limit]
                ]

            # Perform search
            documents = await self.get_relevant_documents(
                query=query,
                k=limit,
                metadata_filter=metadata_filter,
                relevance_threshold=min_score,
            )

            # Cache result
            self._cache_result(cache_key, documents)

            # Return formatted results
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": doc.metadata.get("relevance_score", 0.8),
                }
                for doc in documents
            ]

        except Exception as e:
            raise RAGServiceError(f"Failed to search documents: {str(e)}")

    async def get_relevant_documents(
        self,
        query: str,
        k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        relevance_threshold: float = 0.7,
    ) -> List[Document]:
        """
        Optimized document retrieval with smart filtering.
        """
        try:
            k = k or 5

            # Quick relevance check for very short queries
            query_keywords = set(query.lower().split())
            if len(query_keywords) < 2:
                return []

            # Build metadata filter
            filter_query = None
            if metadata_filter:
                filter_conditions = []
                for key, value in metadata_filter.items():
                    filter_conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                filter_query = Filter(must=filter_conditions)

            # Retrieve more initially for better filtering
            search_k = min(k * 2, 15)

            # Perform similarity search
            if filter_query:
                results = await self.vector_store.asimilarity_search_with_score(
                    query=query, k=search_k, filter=filter_query
                )
            else:
                results = await self.vector_store.asimilarity_search_with_score(
                    query=query, k=search_k
                )

            # Filter and score documents
            relevant_documents = []
            for doc, score in results:
                similarity = 1 - score if score <= 1 else 1 / (1 + score)

                if similarity >= relevance_threshold:
                    doc.metadata["relevance_score"] = similarity
                    relevant_documents.append(doc)

            return relevant_documents[:k]

        except Exception as e:
            raise RAGServiceError(f"Failed to retrieve documents: {str(e)}")

    async def check_document_relevance(
        self, query: str, documents: List[Document], threshold: float = 0.5
    ) -> bool:
        """
        Optimized relevance check using lightweight scoring.
        """
        if not documents:
            return False

        try:
            # Use keyword overlap as lightweight alternative to LLM calls
            query_keywords = set(query.lower().split())
            relevance_scores = []

            for doc in documents:
                doc_keywords = set(doc.page_content.lower().split())
                overlap = len(query_keywords.intersection(doc_keywords))
                total_keywords = len(query_keywords.union(doc_keywords))

                # Jaccard similarity with content length bonus
                jaccard_score = overlap / total_keywords if total_keywords > 0 else 0
                length_bonus = min(len(doc.page_content) / 500, 1.0)

                relevance_score = (jaccard_score * 0.7) + (length_bonus * 0.3)
                relevance_scores.append(relevance_score)

            avg_relevance = sum(relevance_scores) / len(relevance_scores)

            # Only use LLM for borderline cases
            if avg_relevance < threshold - 0.2:
                return False
            elif avg_relevance > threshold + 0.2:
                return True
            else:
                return await self._llm_relevance_check(query, [documents[0]], threshold)

        except Exception:
            return True  # Assume relevant if check fails

    async def _llm_relevance_check(
        self, query: str, documents: List[Document], threshold: float = 0.5
    ) -> bool:
        """Lightweight LLM-based relevance check."""
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

            # Truncate context to save tokens
            context = documents[0].page_content[:300]
            if len(documents[0].page_content) > 300:
                context += "..."

            # Minimal prompt
            relevance_prompt = (
                f"Rate relevance 0-10:\nQ: {query[:100]}\nContext: {context}\nRating:"
            )

            response = await llm.ainvoke(relevance_prompt)

            try:
                rating = float(str(response.content).strip().split()[0])
                return (rating / 10.0) >= threshold
            except (ValueError, IndexError):
                return True

        except Exception:
            return True
