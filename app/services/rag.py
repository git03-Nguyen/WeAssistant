"""Optimized RAG service for document ingestion and retrieval."""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, List, Optional

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import FieldCondition, Filter, MatchValue

from app.config.settings import get_settings
from app.core.exceptions import RAGServiceError
from app.utils.file_processor import SmartSplitter


class RAGService:
    """Optimized service for RAG operations with caching and cost reduction."""

    def __init__(self):
        self.settings = get_settings()
        self.qdrant_client = QdrantClient(url=self.settings.qdrant_url)
        self.embeddings = OpenAIEmbeddings(
            model=self.settings.openai_embed_model,
        )
        self.collection_name = self.settings.qdrant_collection
        self.text_splitter = SmartSplitter(
            lang="en",
            chunk_size=800,
            chunk_overlap=400,
        )

        # In-memory cache for recent queries
        self._query_cache = {}
        self._cache_ttl = timedelta(minutes=10)

        # Get embedding dimensions based on model
        if "large" in self.settings.openai_embed_model:
            self.embedding_dimension = 3072
        else:
            self.embedding_dimension = 1536

        # Initialize vector store (assumes collection exists)
        self.vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )

    def _get_cache_key(self, query: str, metadata_filter: Optional[dict] = None) -> str:
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

    async def ingest_document(
        self, content: str, content_type: str, metadata: dict[str, Any]
    ) -> str:
        """
        Optimized document ingestion with reduced storage.

        Args:
            content: Document content
            content_type: Content type (e.g., "text/plain", "text/markdown")
            metadata: Document metadata

        Returns:
            Document ID
        """
        try:
            # Generate unique document ID
            doc_id = str(uuid.uuid4())

            # Split into optimized documents
            docs = self.text_splitter.split_text(content, content_type)

            # Get the title from metadata to append to chunks
            title = metadata.get("title", "").strip()

            # Create documents with title and part info prepended to content
            documents = []
            for i, doc in enumerate(docs):
                # Build title prefix with part information
                if title:
                    if len(docs) > 1:
                        title_prefix = (
                            f"[Title: {title}\nPart {i + 1} of {len(docs)}]\n\n"
                        )
                    else:
                        title_prefix = f"[Title: {title}]\n\n"
                else:
                    title_prefix = (
                        f"[Part {i + 1} of {len(docs)}]\n\n" if len(docs) > 1 else ""
                    )

                # Prepend title and part info to chunk content for better retrieval
                doc.page_content = title_prefix + doc.page_content

                # Merge metadata efficiently, prioritizing explicit keys
                doc.metadata = {
                    "document_id": doc_id,
                    "chunk_index": i,
                    "user_id": metadata.get("user_id", "unknown"),
                    "length": len(doc.page_content),
                    **{**doc.metadata, **metadata},
                }
                documents.append(doc)

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
            # Build filter conditions - target the nested metadata structure
            conditions = [
                FieldCondition(
                    key="metadata.document_id", match=MatchValue(value=document_id)
                )
            ]

            if user_id is not None:
                conditions.append(
                    FieldCondition(
                        key="metadata.user_id", match=MatchValue(value=str(user_id))
                    )
                )

            # Create filter - cast to proper type to satisfy type checker
            filter_query = Filter(
                must=[c for c in conditions if isinstance(c, FieldCondition)]
            )

            # Scroll through all matching points to get their IDs
            scroll_result = self.qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_query,
                limit=10000,
                with_payload=True,
                with_vectors=False,
            )

            all_points = scroll_result[0]

            if not all_points:
                return True  # No points to delete

            # Extract point IDs and convert to strings
            point_ids = [str(point.id) for point in all_points]

            # Delete using the actual point IDs
            await self.vector_store.adelete(ids=point_ids)

            return True

        except Exception as e:
            raise RAGServiceError(f"Failed to remove document: {str(e)}")

    async def search_documents(
        self,
        query: str,
        user_id: Optional[int] = None,
        limit: int = 5,
        min_score: float = 0.5,
    ) -> List[dict[str, Any]]:
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
        metadata_filter: Optional[dict[str, Any]] = None,
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
                        FieldCondition(
                            key=f"metadata.{key}", match=MatchValue(value=value)
                        )
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

            llm = ChatOpenAI()

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
