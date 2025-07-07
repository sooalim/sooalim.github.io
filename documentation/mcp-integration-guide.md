# Model Context Protocol (MCP) Integration Guide for RAG Agents

## Overview
This guide provides detailed instructions for integrating Model Context Protocol (MCP) capabilities into your RAG agent implementation, enabling future expansion and interoperability with various AI tools and services.

## What is Model Context Protocol (MCP)?

MCP is an open protocol that enables AI applications to securely access and interact with external data sources and tools. It provides a standardized way for AI models to:
- Access real-time data from various sources
- Execute functions and tools securely
- Maintain context across multiple interactions
- Integrate with third-party services and APIs

## MCP Architecture for RAG Agents

### Core Components

#### 1. MCP Server Implementation
```python
# src/mcp/mcp_server.py
import asyncio
from typing import Dict, List, Any, Optional
from mcp import Server, ClientSession, Tool, Resource
from mcp.types import GetResourceRequest, CallToolRequest

class RAGMCPServer(Server):
    """MCP Server for RAG Agent integration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        self.rag_client = None
        self.vector_store = None
        self.cognitive_services = None
        
    async def initialize(self):
        """Initialize RAG agent components."""
        # Initialize vector store, cognitive services, etc.
        pass
        
    @property
    def tools(self) -> List[Tool]:
        """Define available tools for MCP clients."""
        return [
            Tool(
                name="search_documents",
                description="Search through document collection using semantic search",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query text"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 10
                        },
                        "score_threshold": {
                            "type": "number",
                            "description": "Minimum relevance score",
                            "default": 0.7
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="extract_document_content",
                description="Extract and process content from uploaded documents",
                parameters={
                    "type": "object",
                    "properties": {
                        "document_url": {
                            "type": "string",
                            "description": "URL or path to document"
                        },
                        "extract_tables": {
                            "type": "boolean",
                            "description": "Extract table data",
                            "default": True
                        },
                        "extract_images": {
                            "type": "boolean",
                            "description": "Extract image descriptions",
                            "default": False
                        }
                    },
                    "required": ["document_url"]
                }
            ),
            Tool(
                name="generate_summary",
                description="Generate summary of document or text content",
                parameters={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to summarize"
                        },
                        "max_length": {
                            "type": "integer",
                            "description": "Maximum summary length in words",
                            "default": 200
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific areas to focus on in summary"
                        }
                    },
                    "required": ["content"]
                }
            ),
            Tool(
                name="analyze_sentiment",
                description="Analyze sentiment and emotional tone of text",
                parameters={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to analyze"
                        },
                        "language": {
                            "type": "string",
                            "description": "Language code (e.g., 'en', 'es')",
                            "default": "en"
                        }
                    },
                    "required": ["text"]
                }
            ),
            Tool(
                name="get_document_metadata",
                description="Retrieve metadata for documents in the collection",
                parameters={
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "Document identifier"
                        },
                        "include_content": {
                            "type": "boolean",
                            "description": "Include document content in response",
                            "default": False
                        }
                    },
                    "required": ["document_id"]
                }
            )
        ]
    
    @property
    def resources(self) -> List[Resource]:
        """Define available resources for MCP clients."""
        return [
            Resource(
                uri="rag://documents/",
                name="Document Collection",
                description="Access to the RAG agent's document collection",
                mime_type="application/json"
            ),
            Resource(
                uri="rag://search/",
                name="Search Interface",
                description="Search interface for document collection",
                mime_type="application/json"
            ),
            Resource(
                uri="rag://analytics/",
                name="Analytics Data",
                description="Usage analytics and performance metrics",
                mime_type="application/json"
            )
        ]
    
    async def call_tool(self, request: CallToolRequest) -> Dict[str, Any]:
        """Handle tool execution requests."""
        tool_name = request.method
        args = request.params or {}
        
        if tool_name == "search_documents":
            return await self._search_documents(args)
        elif tool_name == "extract_document_content":
            return await self._extract_document_content(args)
        elif tool_name == "generate_summary":
            return await self._generate_summary(args)
        elif tool_name == "analyze_sentiment":
            return await self._analyze_sentiment(args)
        elif tool_name == "get_document_metadata":
            return await self._get_document_metadata(args)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def get_resource(self, request: GetResourceRequest) -> Dict[str, Any]:
        """Handle resource access requests."""
        uri = request.uri
        
        if uri.startswith("rag://documents/"):
            return await self._get_documents_resource(uri)
        elif uri.startswith("rag://search/"):
            return await self._get_search_resource(uri)
        elif uri.startswith("rag://analytics/"):
            return await self._get_analytics_resource(uri)
        else:
            raise ValueError(f"Unknown resource: {uri}")
    
    # Tool implementation methods
    async def _search_documents(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation for document search."""
        # Implement document search logic
        pass
    
    async def _extract_document_content(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation for document content extraction."""
        # Implement document extraction logic
        pass
    
    async def _generate_summary(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation for text summarization."""
        # Implement summarization logic
        pass
    
    async def _analyze_sentiment(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation for sentiment analysis."""
        # Implement sentiment analysis logic
        pass
    
    async def _get_document_metadata(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation for metadata retrieval."""
        # Implement metadata retrieval logic
        pass
    
    # Resource implementation methods
    async def _get_documents_resource(self, uri: str) -> Dict[str, Any]:
        """Implementation for documents resource access."""
        # Implement documents resource logic
        pass
    
    async def _get_search_resource(self, uri: str) -> Dict[str, Any]:
        """Implementation for search resource access."""
        # Implement search resource logic
        pass
    
    async def _get_analytics_resource(self, uri: str) -> Dict[str, Any]:
        """Implementation for analytics resource access."""
        # Implement analytics resource logic
        pass
```

#### 2. MCP Client Integration
```python
# src/mcp/mcp_client.py
import asyncio
from typing import Dict, List, Any, Optional
from mcp import ClientSession
from mcp.types import CallToolRequest, GetResourceRequest

class RAGMCPClient:
    """MCP Client for connecting to external MCP servers."""
    
    def __init__(self, server_url: str, api_key: Optional[str] = None):
        self.server_url = server_url
        self.api_key = api_key
        self.session = None
        
    async def connect(self):
        """Connect to MCP server."""
        self.session = ClientSession(self.server_url, api_key=self.api_key)
        await self.session.connect()
        
    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.session:
            await self.session.disconnect()
            
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        request = CallToolRequest(method=tool_name, params=kwargs)
        return await self.session.call_tool(request)
        
    async def get_resource(self, uri: str) -> Dict[str, Any]:
        """Get a resource from the MCP server."""
        request = GetResourceRequest(uri=uri)
        return await self.session.get_resource(request)
        
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools on the server."""
        return await self.session.list_tools()
        
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources on the server."""
        return await self.session.list_resources()
```

#### 3. Integration with Azure Functions
```python
# src/azure-functions/mcp-integration/function_app.py
import json
import logging
from typing import Dict, Any
import azure.functions as func
from mcp_server import RAGMCPServer

app = func.FunctionApp()

# Initialize MCP server
mcp_server = RAGMCPServer({
    'azure_config': {
        'storage_account': 'your_storage_account',
        'search_service': 'your_search_service',
        'openai_endpoint': 'your_openai_endpoint'
    }
})

@app.route(route="mcp/tools", auth_level=func.AuthLevel.FUNCTION)
async def list_tools(req: func.HttpRequest) -> func.HttpResponse:
    """List available MCP tools."""
    try:
        tools = mcp_server.tools
        return func.HttpResponse(
            json.dumps([tool.dict() for tool in tools]),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error listing tools: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="mcp/call-tool", auth_level=func.AuthLevel.FUNCTION)
async def call_tool(req: func.HttpRequest) -> func.HttpResponse:
    """Call an MCP tool."""
    try:
        req_body = req.get_json()
        tool_name = req_body.get('tool_name')
        params = req_body.get('params', {})
        
        # Create call request
        from mcp.types import CallToolRequest
        request = CallToolRequest(method=tool_name, params=params)
        
        # Execute tool
        result = await mcp_server.call_tool(request)
        
        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error calling tool: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="mcp/resources", auth_level=func.AuthLevel.FUNCTION)
async def list_resources(req: func.HttpRequest) -> func.HttpResponse:
    """List available MCP resources."""
    try:
        resources = mcp_server.resources
        return func.HttpResponse(
            json.dumps([resource.dict() for resource in resources]),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error listing resources: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="mcp/get-resource", auth_level=func.AuthLevel.FUNCTION)
async def get_resource(req: func.HttpRequest) -> func.HttpResponse:
    """Get an MCP resource."""
    try:
        uri = req.params.get('uri')
        if not uri:
            return func.HttpResponse(
                json.dumps({"error": "URI parameter required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Create resource request
        from mcp.types import GetResourceRequest
        request = GetResourceRequest(uri=uri)
        
        # Get resource
        result = await mcp_server.get_resource(request)
        
        return func.HttpResponse(
            json.dumps(result),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error getting resource: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
```

## Integration Scenarios

### 1. Claude Desktop Integration
Enable Claude Desktop to access your RAG agent's document collection:

```json
{
  "mcpServers": {
    "rag-agent": {
      "command": "python",
      "args": ["-m", "mcp", "serve", "rag-agent"],
      "env": {
        "AZURE_STORAGE_CONNECTION_STRING": "your_connection_string",
        "AZURE_SEARCH_ENDPOINT": "your_search_endpoint",
        "AZURE_OPENAI_ENDPOINT": "your_openai_endpoint"
      }
    }
  }
}
```

### 2. Custom AI Applications
Integrate with custom AI applications using MCP client:

```python
# Example: Custom AI assistant integration
from mcp_client import RAGMCPClient

class AIAssistant:
    def __init__(self, rag_mcp_url: str):
        self.rag_client = RAGMCPClient(rag_mcp_url)
        
    async def search_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """Search the RAG agent's knowledge base."""
        result = await self.rag_client.call_tool(
            "search_documents",
            query=query,
            max_results=5
        )
        return result.get('documents', [])
        
    async def analyze_document(self, document_url: str) -> Dict[str, Any]:
        """Analyze a document using RAG agent capabilities."""
        extraction_result = await self.rag_client.call_tool(
            "extract_document_content",
            document_url=document_url
        )
        
        if extraction_result.get('content'):
            summary_result = await self.rag_client.call_tool(
                "generate_summary",
                content=extraction_result['content']
            )
            return {
                'extraction': extraction_result,
                'summary': summary_result
            }
        return extraction_result
```

### 3. Third-Party Tool Integration
Connect your RAG agent to external tools and services:

```python
# src/mcp/integrations/external_tools.py
from typing import Dict, Any, List
from mcp_client import RAGMCPClient

class ExternalToolIntegration:
    """Integration with external tools via MCP."""
    
    def __init__(self, rag_mcp_url: str):
        self.rag_client = RAGMCPClient(rag_mcp_url)
        self.external_tools = {}
        
    async def register_external_tool(self, name: str, mcp_url: str):
        """Register an external MCP tool."""
        self.external_tools[name] = RAGMCPClient(mcp_url)
        await self.external_tools[name].connect()
        
    async def enhanced_search(self, query: str) -> Dict[str, Any]:
        """Enhanced search using both internal and external tools."""
        # Search internal knowledge base
        internal_results = await self.rag_client.call_tool(
            "search_documents",
            query=query
        )
        
        # Search external knowledge bases
        external_results = {}
        for tool_name, client in self.external_tools.items():
            try:
                result = await client.call_tool("search", query=query)
                external_results[tool_name] = result
            except Exception as e:
                logging.warning(f"Error searching {tool_name}: {e}")
        
        return {
            'internal': internal_results,
            'external': external_results,
            'combined_score': self._calculate_combined_relevance(
                internal_results, external_results
            )
        }
        
    def _calculate_combined_relevance(self, internal: Dict, external: Dict) -> float:
        """Calculate combined relevance score."""
        # Implement relevance scoring logic
        pass
```

## Security Considerations

### 1. Authentication and Authorization
```python
# src/mcp/security/auth.py
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class MCPAuthManager:
    """Authentication manager for MCP connections."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        
    def generate_token(self, client_id: str, permissions: List[str]) -> str:
        """Generate JWT token for MCP client."""
        payload = {
            'client_id': client_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
        
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
            
    def check_permission(self, token_payload: Dict[str, Any], 
                        required_permission: str) -> bool:
        """Check if token has required permission."""
        permissions = token_payload.get('permissions', [])
        return required_permission in permissions or 'admin' in permissions
```

### 2. Rate Limiting and Throttling
```python
# src/mcp/security/rate_limiter.py
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any

class MCPRateLimiter:
    """Rate limiter for MCP connections."""
    
    def __init__(self, max_requests: int = 100, window_minutes: int = 60):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests = defaultdict(list)
        
    async def check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        # Check current rate
        if len(self.requests[client_id]) >= self.max_requests:
            return False
            
        # Record new request
        self.requests[client_id].append(now)
        return True
```

## Performance Optimization

### 1. Caching Strategy
```python
# src/mcp/caching/cache_manager.py
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

class MCPCacheManager:
    """Caching manager for MCP responses."""
    
    def __init__(self, storage_connection: str, container_name: str = "mcp-cache"):
        self.blob_client = BlobServiceClient.from_connection_string(storage_connection)
        self.container_name = container_name
        self.default_ttl = timedelta(hours=1)
        
    async def get_cached_response(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached response."""
        try:
            blob_client = self.blob_client.get_blob_client(
                container=self.container_name,
                blob=key
            )
            
            # Check if blob exists and is not expired
            properties = blob_client.get_blob_properties()
            if self._is_expired(properties.last_modified):
                await self._delete_cache_entry(key)
                return None
                
            # Get cached data
            blob_data = blob_client.download_blob()
            return json.loads(blob_data.readall().decode('utf-8'))
            
        except ResourceNotFoundError:
            return None
            
    async def set_cached_response(self, key: str, data: Dict[str, Any], 
                                 ttl: Optional[timedelta] = None):
        """Set cached response."""
        blob_client = self.blob_client.get_blob_client(
            container=self.container_name,
            blob=key
        )
        
        # Store data with metadata
        metadata = {
            'ttl': str(ttl or self.default_ttl),
            'created': datetime.utcnow().isoformat()
        }
        
        blob_client.upload_blob(
            json.dumps(data).encode('utf-8'),
            metadata=metadata,
            overwrite=True
        )
        
    def _generate_cache_key(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Generate cache key for tool call."""
        key_data = f"{tool_name}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_data.encode('utf-8')).hexdigest()
        
    def _is_expired(self, last_modified: datetime) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() - last_modified.replace(tzinfo=None) > self.default_ttl
        
    async def _delete_cache_entry(self, key: str):
        """Delete expired cache entry."""
        try:
            blob_client = self.blob_client.get_blob_client(
                container=self.container_name,
                blob=key
            )
            blob_client.delete_blob()
        except ResourceNotFoundError:
            pass
```

### 2. Connection Pooling
```python
# src/mcp/connection/pool_manager.py
import asyncio
from typing import Dict, Any, List
from mcp_client import RAGMCPClient

class MCPConnectionPool:
    """Connection pool for MCP clients."""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.available_connections = asyncio.Queue()
        self.active_connections = {}
        self.connection_count = 0
        
    async def get_connection(self, server_url: str) -> RAGMCPClient:
        """Get connection from pool."""
        if not self.available_connections.empty():
            return await self.available_connections.get()
            
        if self.connection_count < self.max_connections:
            client = RAGMCPClient(server_url)
            await client.connect()
            self.connection_count += 1
            return client
            
        # Wait for available connection
        return await self.available_connections.get()
        
    async def return_connection(self, client: RAGMCPClient):
        """Return connection to pool."""
        await self.available_connections.put(client)
        
    async def close_all_connections(self):
        """Close all connections in pool."""
        while not self.available_connections.empty():
            client = await self.available_connections.get()
            await client.disconnect()
            
        self.connection_count = 0
```

## Monitoring and Analytics

### 1. Usage Tracking
```python
# src/mcp/monitoring/usage_tracker.py
from datetime import datetime
from typing import Dict, Any
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

class MCPUsageTracker:
    """Usage tracking for MCP operations."""
    
    def __init__(self, connection_string: str):
        configure_azure_monitor(connection_string=connection_string)
        self.tracer = trace.get_tracer(__name__)
        
    async def track_tool_call(self, tool_name: str, params: Dict[str, Any], 
                             duration: float, success: bool):
        """Track tool call metrics."""
        with self.tracer.start_as_current_span(f"mcp.tool.{tool_name}") as span:
            span.set_attribute("tool.name", tool_name)
            span.set_attribute("tool.duration", duration)
            span.set_attribute("tool.success", success)
            span.set_attribute("tool.params_count", len(params))
            
            if success:
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(Status(StatusCode.ERROR))
                
    async def track_resource_access(self, uri: str, duration: float, 
                                   success: bool):
        """Track resource access metrics."""
        with self.tracer.start_as_current_span(f"mcp.resource.access") as span:
            span.set_attribute("resource.uri", uri)
            span.set_attribute("resource.duration", duration)
            span.set_attribute("resource.success", success)
            
            if success:
                span.set_status(Status(StatusCode.OK))
            else:
                span.set_status(Status(StatusCode.ERROR))
```

## Deployment Configuration

### 1. Azure Functions Configuration
```json
{
  "version": "2.0",
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  },
  "customHandler": {
    "description": {
      "defaultExecutablePath": "python",
      "workingDirectory": "",
      "arguments": ["-m", "mcp", "serve", "rag-agent"]
    }
  },
  "functionTimeout": "00:30:00",
  "extensions": {
    "http": {
      "routePrefix": "api/mcp"
    }
  }
}
```

### 2. Environment Variables
```bash
# MCP Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
MCP_AUTH_SECRET=your-secret-key
MCP_RATE_LIMIT_MAX_REQUESTS=100
MCP_RATE_LIMIT_WINDOW_MINUTES=60

# Azure Integration
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_SEARCH_ENDPOINT=your-search-endpoint
AZURE_OPENAI_ENDPOINT=your-openai-endpoint
AZURE_MONITOR_CONNECTION_STRING=your-monitor-connection

# Caching
MCP_CACHE_ENABLED=true
MCP_CACHE_TTL_HOURS=1
MCP_CACHE_CONTAINER=mcp-cache

# Security
MCP_CORS_ENABLED=true
MCP_CORS_ORIGINS=*
MCP_SSL_ENABLED=false
```

## Testing and Validation

### 1. Unit Tests
```python
# tests/test_mcp_integration.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from mcp_server import RAGMCPServer
from mcp.types import CallToolRequest

@pytest.fixture
async def mcp_server():
    """Create MCP server for testing."""
    config = {
        'azure_config': {
            'storage_account': 'test_storage',
            'search_service': 'test_search',
            'openai_endpoint': 'test_openai'
        }
    }
    server = RAGMCPServer(config)
    await server.initialize()
    return server

@pytest.mark.asyncio
async def test_search_documents_tool(mcp_server):
    """Test document search tool."""
    # Mock vector store
    mcp_server.vector_store = AsyncMock()
    mcp_server.vector_store.search.return_value = [
        {'content': 'Test document', 'score': 0.9}
    ]
    
    # Create tool request
    request = CallToolRequest(
        method='search_documents',
        params={'query': 'test query', 'max_results': 5}
    )
    
    # Execute tool
    result = await mcp_server.call_tool(request)
    
    # Verify result
    assert 'documents' in result
    assert len(result['documents']) == 1
    assert result['documents'][0]['content'] == 'Test document'

@pytest.mark.asyncio
async def test_extract_document_content_tool(mcp_server):
    """Test document extraction tool."""
    # Mock extraction service
    mcp_server.extraction_service = AsyncMock()
    mcp_server.extraction_service.extract.return_value = {
        'content': 'Extracted content',
        'metadata': {'title': 'Test Document'}
    }
    
    # Create tool request
    request = CallToolRequest(
        method='extract_document_content',
        params={'document_url': 'https://example.com/test.pdf'}
    )
    
    # Execute tool
    result = await mcp_server.call_tool(request)
    
    # Verify result
    assert 'content' in result
    assert result['content'] == 'Extracted content'
    assert 'metadata' in result
```

### 2. Integration Tests
```python
# tests/test_mcp_client_integration.py
import pytest
from mcp_client import RAGMCPClient

@pytest.mark.asyncio
async def test_mcp_client_connection():
    """Test MCP client connection."""
    client = RAGMCPClient('http://localhost:8000')
    
    # Test connection
    await client.connect()
    assert client.session is not None
    
    # Test tool listing
    tools = await client.list_tools()
    assert len(tools) > 0
    
    # Test tool execution
    result = await client.call_tool(
        'search_documents',
        query='test query'
    )
    assert 'documents' in result
    
    # Cleanup
    await client.disconnect()
```

## Future Expansion Possibilities

### 1. Multi-Modal Support
- Integration with vision models for image analysis
- Audio processing capabilities
- Video content analysis
- Multi-modal search and retrieval

### 2. Advanced AI Capabilities
- Custom model fine-tuning integration
- Reinforcement learning from human feedback
- Advanced reasoning and planning
- Multi-agent collaboration

### 3. Enterprise Features
- Advanced security and compliance
- Audit logging and governance
- Custom deployment models
- Integration with enterprise systems

## Best Practices

### 1. Security
- Always use HTTPS for MCP connections
- Implement proper authentication and authorization
- Use rate limiting to prevent abuse
- Validate all input parameters
- Log security events for monitoring

### 2. Performance
- Implement caching for frequently accessed data
- Use connection pooling for external services
- Monitor and optimize resource usage
- Implement proper error handling and retry logic

### 3. Scalability
- Design for horizontal scaling
- Use async/await patterns for better concurrency
- Implement proper resource management
- Monitor performance metrics

### 4. Maintainability
- Use clear naming conventions
- Implement comprehensive logging
- Write thorough documentation
- Use type hints and validation
- Implement automated testing

## Conclusion

MCP integration provides a powerful framework for extending your RAG agent's capabilities and enabling interoperability with various AI tools and services. By following this guide, you can implement a robust MCP integration that supports future expansion while maintaining security, performance, and maintainability standards.

The modular architecture allows for easy addition of new tools and resources, while the security and monitoring components ensure safe and reliable operation in production environments.