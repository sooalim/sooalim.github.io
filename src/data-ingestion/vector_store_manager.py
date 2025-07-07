"""
Vector Store Manager for RAG Agent

This module manages vector embeddings storage and retrieval using
Azure Cognitive Search with vector search capabilities.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import openai
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class VectorDocument:
    """Document structure for vector storage."""
    id: str
    content: str
    content_vector: List[float]
    title: Optional[str] = None
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    chunk_id: Optional[str] = None
    document_id: Optional[str] = None
    chunk_index: Optional[int] = None
    token_count: Optional[int] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None


@dataclass
class SearchResult:
    """Search result with relevance score."""
    document: VectorDocument
    score: float
    highlights: Optional[Dict[str, List[str]]] = None


@dataclass
class SearchQuery:
    """Search query configuration."""
    query_text: str
    query_vector: Optional[List[float]] = None
    filters: Optional[str] = None
    top_k: int = 10
    score_threshold: Optional[float] = None
    include_highlights: bool = True
    hybrid_search: bool = True


class OpenAIEmbeddingService:
    """Service for generating embeddings using OpenAI."""
    
    def __init__(self, api_key: str, api_base: str = None, model: str = "text-embedding-ada-002"):
        """Initialize OpenAI embedding service."""
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        
        # Configure OpenAI client
        openai.api_key = api_key
        if api_base:
            openai.api_base = api_base
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            logger.debug(f"Generating embedding for text (length: {len(text)})")
            
            response = await openai.Embedding.acreate(
                model=self.model,
                input=text
            )
            
            embedding = response['data'][0]['embedding']
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches."""
        try:
            logger.info(f"Generating embeddings for {len(texts)} texts in batches of {batch_size}")
            
            embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                response = await openai.Embedding.acreate(
                    model=self.model,
                    input=batch
                )
                
                batch_embeddings = [item['embedding'] for item in response['data']]
                embeddings.extend(batch_embeddings)
                
                logger.debug(f"Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise


class AzureSearchVectorStore:
    """Vector store implementation using Azure Cognitive Search."""
    
    def __init__(self, 
                 search_service_endpoint: str,
                 search_api_key: str,
                 index_name: str = "documents",
                 embedding_service: Optional[OpenAIEmbeddingService] = None):
        """Initialize Azure Search vector store."""
        
        self.search_service_endpoint = search_service_endpoint
        self.search_api_key = search_api_key
        self.index_name = index_name
        self.embedding_service = embedding_service
        
        # Initialize Azure Search clients
        self.credential = AzureKeyCredential(search_api_key)
        self.search_client = SearchClient(
            endpoint=search_service_endpoint,
            index_name=index_name,
            credential=self.credential
        )
        self.index_client = SearchIndexClient(
            endpoint=search_service_endpoint,
            credential=self.credential
        )
    
    def create_index(self, vector_dimensions: int = 1536, delete_if_exists: bool = False) -> None:
        """Create or update the search index with vector search capabilities."""
        try:
            logger.info(f"Creating search index: {self.index_name}")
            
            # Delete existing index if requested
            if delete_if_exists:
                try:
                    self.index_client.delete_index(self.index_name)
                    logger.info(f"Deleted existing index: {self.index_name}")
                except Exception:
                    pass  # Index might not exist
            
            # Define the search index schema
            fields = [
                SimpleField(
                    name="id",
                    type=SearchFieldDataType.String,
                    key=True,
                    filterable=True,
                    retrievable=True
                ),
                SearchableField(
                    name="content",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    retrievable=True,
                    analyzer_name="standard.lucene"
                ),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=vector_dimensions,
                    vector_search_profile_name="vector-profile"
                ),
                SearchableField(
                    name="title",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    filterable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="source",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="metadata",
                    type=SearchFieldDataType.String,
                    retrievable=True
                ),
                SimpleField(
                    name="chunk_id",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="document_id",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="chunk_index",
                    type=SearchFieldDataType.Int32,
                    filterable=True,
                    sortable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="token_count",
                    type=SearchFieldDataType.Int32,
                    filterable=True,
                    sortable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="created_date",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="modified_date",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    sortable=True,
                    retrievable=True
                )
            ]
            
            # Configure vector search
            vector_search = VectorSearch(
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="hnsw-algorithm",
                        parameters={
                            "m": 4,
                            "efConstruction": 400,
                            "efSearch": 500,
                            "metric": "cosine"
                        }
                    )
                ],
                profiles=[
                    VectorSearchProfile(
                        name="vector-profile",
                        algorithm_configuration_name="hnsw-algorithm"
                    )
                ]
            )
            
            # Create the index
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search
            )
            
            result = self.index_client.create_or_update_index(index)
            logger.info(f"Search index created/updated: {result.name}")
            
        except Exception as e:
            logger.error(f"Error creating search index: {str(e)}")
            raise
    
    async def add_documents(self, documents: List[VectorDocument]) -> None:
        """Add documents to the vector store."""
        try:
            logger.info(f"Adding {len(documents)} documents to vector store")
            
            # Convert documents to search format
            search_documents = []
            for doc in documents:
                search_doc = {
                    "id": doc.id,
                    "content": doc.content,
                    "content_vector": doc.content_vector,
                    "title": doc.title,
                    "source": doc.source,
                    "metadata": json.dumps(doc.metadata) if doc.metadata else None,
                    "chunk_id": doc.chunk_id,
                    "document_id": doc.document_id,
                    "chunk_index": doc.chunk_index,
                    "token_count": doc.token_count,
                    "created_date": doc.created_date,
                    "modified_date": doc.modified_date
                }
                search_documents.append(search_doc)
            
            # Upload documents in batches
            batch_size = 100
            for i in range(0, len(search_documents), batch_size):
                batch = search_documents[i:i + batch_size]
                result = self.search_client.upload_documents(documents=batch)
                
                # Check for errors
                for item in result:
                    if not item.succeeded:
                        logger.error(f"Failed to upload document {item.key}: {item.error_message}")
                
                logger.debug(f"Uploaded batch {i//batch_size + 1}/{(len(search_documents) + batch_size - 1)//batch_size}")
            
            logger.info(f"Successfully added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """Search the vector store using hybrid search."""
        try:
            logger.info(f"Searching vector store: '{query.query_text[:50]}...' (top_k: {query.top_k})")
            
            search_params = {
                "search_text": query.query_text if query.hybrid_search else None,
                "top": query.top_k,
                "select": ["id", "content", "title", "source", "metadata", "chunk_id", 
                          "document_id", "chunk_index", "token_count", "created_date", "modified_date"],
                "highlight_fields": ["content", "title"] if query.include_highlights else None
            }
            
            # Add vector query if available
            if query.query_vector:
                vector_query = VectorizedQuery(
                    vector=query.query_vector,
                    k_nearest_neighbors=query.top_k,
                    fields="content_vector"
                )
                search_params["vector_queries"] = [vector_query]
            
            # Add filters if specified
            if query.filters:
                search_params["filter"] = query.filters
            
            # Perform search
            results = self.search_client.search(**search_params)
            
            # Convert results to SearchResult objects
            search_results = []
            for result in results:
                # Parse metadata
                metadata = None
                if result.get("metadata"):
                    try:
                        metadata = json.loads(result["metadata"])
                    except json.JSONDecodeError:
                        metadata = {"raw": result["metadata"]}
                
                # Create VectorDocument
                vector_doc = VectorDocument(
                    id=result["id"],
                    content=result["content"],
                    content_vector=[],  # Don't return vectors in search results
                    title=result.get("title"),
                    source=result.get("source"),
                    metadata=metadata,
                    chunk_id=result.get("chunk_id"),
                    document_id=result.get("document_id"),
                    chunk_index=result.get("chunk_index"),
                    token_count=result.get("token_count"),
                    created_date=result.get("created_date"),
                    modified_date=result.get("modified_date")
                )
                
                # Get highlights
                highlights = None
                if query.include_highlights and hasattr(result, '@search.highlights'):
                    highlights = getattr(result, '@search.highlights')
                
                # Apply score threshold if specified
                score = getattr(result, '@search.score', 0.0)
                if query.score_threshold is None or score >= query.score_threshold:
                    search_results.append(SearchResult(
                        document=vector_doc,
                        score=score,
                        highlights=highlights
                    ))
            
            logger.info(f"Found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            raise
    
    async def search_similar(self, vector: List[float], top_k: int = 10, filters: str = None) -> List[SearchResult]:
        """Search for similar vectors."""
        try:
            logger.info(f"Searching for similar vectors (top_k: {top_k})")
            
            vector_query = VectorizedQuery(
                vector=vector,
                k_nearest_neighbors=top_k,
                fields="content_vector"
            )
            
            search_params = {
                "vector_queries": [vector_query],
                "top": top_k,
                "select": ["id", "content", "title", "source", "metadata", "chunk_id", 
                          "document_id", "chunk_index", "token_count", "created_date", "modified_date"]
            }
            
            if filters:
                search_params["filter"] = filters
            
            results = self.search_client.search(**search_params)
            
            # Convert results
            search_results = []
            for result in results:
                metadata = None
                if result.get("metadata"):
                    try:
                        metadata = json.loads(result["metadata"])
                    except json.JSONDecodeError:
                        metadata = {"raw": result["metadata"]}
                
                vector_doc = VectorDocument(
                    id=result["id"],
                    content=result["content"],
                    content_vector=[],
                    title=result.get("title"),
                    source=result.get("source"),
                    metadata=metadata,
                    chunk_id=result.get("chunk_id"),
                    document_id=result.get("document_id"),
                    chunk_index=result.get("chunk_index"),
                    token_count=result.get("token_count"),
                    created_date=result.get("created_date"),
                    modified_date=result.get("modified_date")
                )
                
                score = getattr(result, '@search.score', 0.0)
                search_results.append(SearchResult(
                    document=vector_doc,
                    score=score
                ))
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error searching similar vectors: {str(e)}")
            raise
    
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Retrieve a specific document by ID."""
        try:
            result = self.search_client.get_document(key=document_id)
            
            metadata = None
            if result.get("metadata"):
                try:
                    metadata = json.loads(result["metadata"])
                except json.JSONDecodeError:
                    metadata = {"raw": result["metadata"]}
            
            return VectorDocument(
                id=result["id"],
                content=result["content"],
                content_vector=result.get("content_vector", []),
                title=result.get("title"),
                source=result.get("source"),
                metadata=metadata,
                chunk_id=result.get("chunk_id"),
                document_id=result.get("document_id"),
                chunk_index=result.get("chunk_index"),
                token_count=result.get("token_count"),
                created_date=result.get("created_date"),
                modified_date=result.get("modified_date")
            )
            
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {str(e)}")
            return None
    
    async def delete_documents(self, document_ids: List[str]) -> None:
        """Delete documents from the vector store."""
        try:
            logger.info(f"Deleting {len(document_ids)} documents from vector store")
            
            delete_documents = [{"id": doc_id} for doc_id in document_ids]
            result = self.search_client.delete_documents(documents=delete_documents)
            
            # Check for errors
            for item in result:
                if not item.succeeded:
                    logger.error(f"Failed to delete document {item.key}: {item.error_message}")
            
            logger.info(f"Successfully deleted {len(document_ids)} documents")
            
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            raise
    
    async def update_documents(self, documents: List[VectorDocument]) -> None:
        """Update existing documents in the vector store."""
        try:
            logger.info(f"Updating {len(documents)} documents in vector store")
            
            # Convert documents to search format
            search_documents = []
            for doc in documents:
                search_doc = {
                    "id": doc.id,
                    "content": doc.content,
                    "content_vector": doc.content_vector,
                    "title": doc.title,
                    "source": doc.source,
                    "metadata": json.dumps(doc.metadata) if doc.metadata else None,
                    "chunk_id": doc.chunk_id,
                    "document_id": doc.document_id,
                    "chunk_index": doc.chunk_index,
                    "token_count": doc.token_count,
                    "created_date": doc.created_date,
                    "modified_date": datetime.now().isoformat()
                }
                search_documents.append(search_doc)
            
            # Update documents
            result = self.search_client.merge_or_upload_documents(documents=search_documents)
            
            # Check for errors
            for item in result:
                if not item.succeeded:
                    logger.error(f"Failed to update document {item.key}: {item.error_message}")
            
            logger.info(f"Successfully updated {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Error updating documents: {str(e)}")
            raise
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """Get statistics about the search index."""
        try:
            index = self.index_client.get_index(self.index_name)
            stats = self.index_client.get_index_statistics(self.index_name)
            
            return {
                "index_name": index.name,
                "document_count": stats.document_count,
                "storage_size": stats.storage_size,
                "vector_index_size": getattr(stats, 'vector_index_size', 'N/A')
            }
            
        except Exception as e:
            logger.error(f"Error getting index statistics: {str(e)}")
            return {}


class VectorStoreManager:
    """High-level manager for vector store operations."""
    
    def __init__(self, 
                 search_service_endpoint: str,
                 search_api_key: str,
                 openai_api_key: str,
                 openai_api_base: str = None,
                 index_name: str = "documents",
                 embedding_model: str = "text-embedding-ada-002"):
        """Initialize vector store manager."""
        
        # Initialize embedding service
        self.embedding_service = OpenAIEmbeddingService(
            api_key=openai_api_key,
            api_base=openai_api_base,
            model=embedding_model
        )
        
        # Initialize vector store
        self.vector_store = AzureSearchVectorStore(
            search_service_endpoint=search_service_endpoint,
            search_api_key=search_api_key,
            index_name=index_name,
            embedding_service=self.embedding_service
        )
    
    async def initialize_index(self, vector_dimensions: int = 1536, delete_if_exists: bool = False):
        """Initialize the search index."""
        self.vector_store.create_index(vector_dimensions, delete_if_exists)
    
    async def add_text_documents(self, 
                               texts: List[str],
                               metadatas: List[Dict[str, Any]] = None,
                               document_ids: List[str] = None) -> List[str]:
        """Add text documents with automatic embedding generation."""
        try:
            logger.info(f"Adding {len(texts)} text documents with embeddings")
            
            # Generate embeddings
            embeddings = await self.embedding_service.generate_embeddings_batch(texts)
            
            # Create vector documents
            documents = []
            added_ids = []
            
            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                doc_id = document_ids[i] if document_ids else str(uuid.uuid4())
                metadata = metadatas[i] if metadatas else {}
                
                vector_doc = VectorDocument(
                    id=doc_id,
                    content=text,
                    content_vector=embedding,
                    title=metadata.get('title'),
                    source=metadata.get('source'),
                    metadata=metadata,
                    chunk_id=metadata.get('chunk_id'),
                    document_id=metadata.get('document_id', doc_id),
                    chunk_index=metadata.get('chunk_index'),
                    token_count=metadata.get('token_count', len(text.split())),
                    created_date=datetime.now().isoformat(),
                    modified_date=datetime.now().isoformat()
                )
                
                documents.append(vector_doc)
                added_ids.append(doc_id)
            
            # Add to vector store
            await self.vector_store.add_documents(documents)
            
            return added_ids
            
        except Exception as e:
            logger.error(f"Error adding text documents: {str(e)}")
            raise
    
    async def search_text(self, 
                         query: str,
                         top_k: int = 10,
                         filters: str = None,
                         score_threshold: float = None,
                         hybrid_search: bool = True) -> List[SearchResult]:
        """Search using text query with automatic embedding generation."""
        try:
            # Generate query embedding
            query_vector = None
            if hybrid_search:
                query_vector = await self.embedding_service.generate_embedding(query)
            
            # Create search query
            search_query = SearchQuery(
                query_text=query,
                query_vector=query_vector,
                filters=filters,
                top_k=top_k,
                score_threshold=score_threshold,
                hybrid_search=hybrid_search
            )
            
            # Perform search
            return await self.vector_store.search(search_query)
            
        except Exception as e:
            logger.error(f"Error searching text: {str(e)}")
            raise
    
    async def search_similar_to_text(self, 
                                   text: str,
                                   top_k: int = 10,
                                   filters: str = None) -> List[SearchResult]:
        """Find documents similar to the given text."""
        try:
            # Generate embedding for the text
            embedding = await self.embedding_service.generate_embedding(text)
            
            # Search for similar vectors
            return await self.vector_store.search_similar(embedding, top_k, filters)
            
        except Exception as e:
            logger.error(f"Error searching similar to text: {str(e)}")
            raise
    
    async def get_relevant_context(self, 
                                 query: str,
                                 max_tokens: int = 4000,
                                 top_k: int = 20) -> Tuple[str, List[SearchResult]]:
        """Get relevant context for RAG generation."""
        try:
            # Search for relevant documents
            results = await self.search_text(query, top_k=top_k)
            
            # Build context within token limit
            context_parts = []
            used_tokens = 0
            used_results = []
            
            for result in results:
                content = result.document.content
                content_tokens = result.document.token_count or len(content.split())
                
                if used_tokens + content_tokens <= max_tokens:
                    context_parts.append(content)
                    used_tokens += content_tokens
                    used_results.append(result)
                else:
                    # Try to fit partial content
                    remaining_tokens = max_tokens - used_tokens
                    if remaining_tokens > 50:  # Minimum useful content
                        words = content.split()
                        partial_content = ' '.join(words[:remaining_tokens])
                        context_parts.append(partial_content)
                        used_results.append(result)
                    break
            
            context = '\n\n'.join(context_parts)
            return context, used_results
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {str(e)}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return self.vector_store.get_index_statistics()


# Factory function for easy initialization
def create_vector_store_manager(config: Dict[str, str]) -> VectorStoreManager:
    """Create vector store manager from configuration."""
    
    return VectorStoreManager(
        search_service_endpoint=config['search_service_endpoint'],
        search_api_key=config['search_api_key'],
        openai_api_key=config['openai_api_key'],
        openai_api_base=config.get('openai_api_base'),
        index_name=config.get('index_name', 'documents'),
        embedding_model=config.get('embedding_model', 'text-embedding-ada-002')
    )


# Example usage
async def main():
    """Example usage of the vector store manager."""
    
    # Configuration
    config = {
        'search_service_endpoint': 'https://your-search-service.search.windows.net',
        'search_api_key': 'your-search-api-key',
        'openai_api_key': 'your-openai-api-key',
        'openai_api_base': 'https://your-openai-endpoint.openai.azure.com/',
        'index_name': 'documents',
        'embedding_model': 'text-embedding-ada-002'
    }
    
    # Create manager
    manager = create_vector_store_manager(config)
    
    # Initialize index
    await manager.initialize_index(delete_if_exists=True)
    
    # Add sample documents
    sample_texts = [
        "Azure Cognitive Search is a cloud search service with AI capabilities.",
        "Vector search enables semantic search using embeddings.",
        "RAG combines retrieval and generation for better AI responses."
    ]
    
    sample_metadata = [
        {"title": "Azure Search", "source": "docs"},
        {"title": "Vector Search", "source": "docs"},
        {"title": "RAG Technology", "source": "docs"}
    ]
    
    document_ids = await manager.add_text_documents(sample_texts, sample_metadata)
    print(f"Added documents: {document_ids}")
    
    # Search for relevant content
    results = await manager.search_text("What is vector search?", top_k=5)
    
    print(f"\nSearch results:")
    for result in results:
        print(f"Score: {result.score:.3f}")
        print(f"Content: {result.document.content[:100]}...")
        print(f"Source: {result.document.source}")
        print()
    
    # Get relevant context for RAG
    context, context_results = await manager.get_relevant_context(
        "Explain vector search", max_tokens=1000
    )
    
    print(f"\nRelevant context ({len(context.split())} words):")
    print(context[:200] + "...")
    
    # Get statistics
    stats = manager.get_statistics()
    print(f"\nIndex statistics: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
