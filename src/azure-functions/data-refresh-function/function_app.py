"""
Azure Functions App for RAG Agent Data Refresh

This function app handles automated data refresh operations for the RAG agent,
including document processing, vector generation, and index updates.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.storage.blob import BlobServiceClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Function App
app = func.FunctionApp()

# Global configuration
config = {
    'key_vault_name': os.getenv('KEY_VAULT_NAME'),
    'storage_account_name': os.getenv('STORAGE_ACCOUNT_NAME'),
    'search_service_name': os.getenv('SEARCH_SERVICE_NAME'),
    'documents_container': os.getenv('DOCUMENTS_CONTAINER', 'documents'),
    'processed_container': os.getenv('PROCESSED_CONTAINER', 'processed'),
    'chunk_size': int(os.getenv('CHUNK_SIZE', '1000')),
    'chunk_overlap': int(os.getenv('CHUNK_OVERLAP', '100')),
    'max_tokens': int(os.getenv('MAX_TOKENS', '4000')),
    'embedding_model': os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002'),
    'batch_size': int(os.getenv('BATCH_SIZE', '10'))
}


# Initialize Azure clients
def get_azure_clients():
    """Initialize Azure service clients."""
    try:
        credential = DefaultAzureCredential()
        
        # Key Vault client
        key_vault_url = f"https://{config['key_vault_name']}.vault.azure.com/"
        secret_client = SecretClient(vault_url=key_vault_url, credential=credential)
        
        # Get secrets
        storage_connection_string = secret_client.get_secret("storage-connection-string").value
        openai_api_key = secret_client.get_secret("openai-api-key").value
        search_api_key = secret_client.get_secret("search-api-key").value
        
        # Storage client
        blob_client = BlobServiceClient.from_connection_string(storage_connection_string)
        
        return {
            'blob_client': blob_client,
            'openai_api_key': openai_api_key,
            'search_api_key': search_api_key,
            'search_endpoint': f"https://{config['search_service_name']}.search.windows.net"
        }
        
    except Exception as e:
        logger.error(f"Error initializing Azure clients: {str(e)}")
        raise


# Timer-triggered function for scheduled data refresh
@app.timer_trigger(schedule="0 0 2 * * *",  # Daily at 2 AM
                   arg_name="timer",
                   run_on_startup=True,
                   use_monitor=False)
async def scheduled_data_refresh(timer: func.TimerRequest) -> None:
    """Timer-triggered function for scheduled data refresh."""
    
    logger.info("Starting scheduled data refresh")
    
    try:
        # Get Azure clients
        clients = get_azure_clients()
        
        # Process new and updated documents
        await process_document_changes(clients)
        
        # Clean up old processed files
        await cleanup_old_processed_files(clients)
        
        logger.info("Scheduled data refresh completed successfully")
        
    except Exception as e:
        logger.error(f"Error in scheduled data refresh: {str(e)}")
        raise


# HTTP-triggered function for manual data refresh
@app.route(route="refresh-data", auth_level=func.AuthLevel.FUNCTION)
async def manual_data_refresh(req: func.HttpRequest) -> func.HttpResponse:
    """HTTP-triggered function for manual data refresh."""
    
    logger.info("Manual data refresh triggered")
    
    try:
        # Parse request parameters
        force_refresh = req.params.get('force', 'false').lower() == 'true'
        document_path = req.params.get('document_path')
        
        # Get Azure clients
        clients = get_azure_clients()
        
        if document_path:
            # Process specific document
            result = await process_single_document(clients, document_path, force_refresh)
        else:
            # Process all documents
            result = await process_document_changes(clients, force_refresh)
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Error in manual data refresh: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# Blob-triggered function for real-time processing
@app.blob_trigger(arg_name="blob",
                  path=f"{config['documents_container']}/{{name}}",
                  connection="AzureWebJobsStorage")
async def blob_upload_processor(blob: func.InputStream) -> None:
    """Blob-triggered function for processing uploaded documents."""
    
    logger.info(f"Processing uploaded blob: {blob.name}")
    
    try:
        # Get Azure clients
        clients = get_azure_clients()
        
        # Process the uploaded document
        await process_single_document(clients, blob.name, force_refresh=True)
        
        logger.info(f"Successfully processed uploaded blob: {blob.name}")
        
    except Exception as e:
        logger.error(f"Error processing uploaded blob {blob.name}: {str(e)}")
        raise


# Queue-triggered function for batch processing
@app.queue_trigger(arg_name="msg",
                   queue_name="data-processing",
                   connection="AzureWebJobsStorage")
async def queue_processor(msg: func.QueueMessage) -> None:
    """Queue-triggered function for processing document batches."""
    
    logger.info("Processing queue message for document batch")
    
    try:
        # Parse queue message
        message_data = json.loads(msg.get_body().decode('utf-8'))
        document_paths = message_data.get('document_paths', [])
        force_refresh = message_data.get('force_refresh', False)
        
        # Get Azure clients
        clients = get_azure_clients()
        
        # Process documents in batch
        results = await process_document_batch(clients, document_paths, force_refresh)
        
        logger.info(f"Successfully processed batch of {len(document_paths)} documents")
        
    except Exception as e:
        logger.error(f"Error processing queue message: {str(e)}")
        raise


# Health check endpoint
@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS)
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    
    try:
        # Perform basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "config": {
                "key_vault_configured": bool(config['key_vault_name']),
                "storage_configured": bool(config['storage_account_name']),
                "search_configured": bool(config['search_service_name'])
            }
        }
        
        return func.HttpResponse(
            json.dumps(health_status),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        error_status = {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        
        return func.HttpResponse(
            json.dumps(error_status),
            status_code=500,
            mimetype="application/json"
        )


# Processing functions
async def process_document_changes(clients: Dict[str, Any], force_refresh: bool = False) -> Dict[str, Any]:
    """Process new and updated documents."""
    
    logger.info("Processing document changes")
    
    blob_client = clients['blob_client']
    container_client = blob_client.get_container_client(config['documents_container'])
    
    # Get list of documents to process
    documents_to_process = []
    processed_count = 0
    error_count = 0
    
    try:
        # List all blobs in documents container
        blobs = container_client.list_blobs(include=['metadata'])
        
        for blob in blobs:
            # Check if document needs processing
            if should_process_document(blob, force_refresh):
                documents_to_process.append(blob.name)
        
        logger.info(f"Found {len(documents_to_process)} documents to process")
        
        # Process documents in batches
        for i in range(0, len(documents_to_process), config['batch_size']):
            batch = documents_to_process[i:i + config['batch_size']]
            
            try:
                await process_document_batch(clients, batch, force_refresh)
                processed_count += len(batch)
                
            except Exception as e:
                logger.error(f"Error processing batch: {str(e)}")
                error_count += len(batch)
        
        return {
            "total_documents": len(documents_to_process),
            "processed_count": processed_count,
            "error_count": error_count,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing document changes: {str(e)}")
        raise


async def process_single_document(clients: Dict[str, Any], document_path: str, force_refresh: bool = False) -> Dict[str, Any]:
    """Process a single document."""
    
    logger.info(f"Processing single document: {document_path}")
    
    try:
        # Import processing modules (lazy import to avoid startup issues)
        from data_extraction.data_extractor import DataExtractionManager
        from data_extraction.azure_cognitive_processor import create_cognitive_processor
        from data_ingestion.chunk_processor import ChunkProcessor, ChunkStrategy
        from data_ingestion.vector_store_manager import create_vector_store_manager
        
        # Initialize processors
        extraction_manager = DataExtractionManager()
        
        cognitive_config = {
            'form_recognizer_endpoint': f"https://{config['search_service_name']}-formrecognizer.cognitiveservices.azure.com/",
            'text_analytics_endpoint': f"https://{config['search_service_name']}-textanalytics.cognitiveservices.azure.com/",
            'form_recognizer_key': clients.get('form_recognizer_key'),
            'text_analytics_key': clients.get('text_analytics_key')
        }
        
        vector_config = {
            'search_service_endpoint': clients['search_endpoint'],
            'search_api_key': clients['search_api_key'],
            'openai_api_key': clients['openai_api_key'],
            'embedding_model': config['embedding_model']
        }
        
        chunk_processor = ChunkProcessor()
        vector_manager = create_vector_store_manager(vector_config)
        
        # Extract document content
        blob_client = clients['blob_client']
        extracted_doc = await extraction_manager.extract_from_blob(
            config['documents_container'], 
            document_path
        )
        
        # Process with cognitive services if available
        if cognitive_config.get('form_recognizer_key'):
            cognitive_processor = create_cognitive_processor(cognitive_config)
            
            # Download blob to temporary file for cognitive processing
            container_client = blob_client.get_container_client(config['documents_container'])
            blob_client_instance = container_client.get_blob_client(document_path)
            
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                blob_data = blob_client_instance.download_blob()
                temp_file.write(blob_data.readall())
                temp_file_path = temp_file.name
            
            try:
                cognitive_result = await cognitive_processor.process_document(
                    temp_file_path,
                    analysis_types=['document', 'text_analytics']
                )
                
                # Enhance extracted document with cognitive results
                if cognitive_result.content:
                    extracted_doc.content = cognitive_result.content
                
                extracted_doc.metadata.custom_metadata.update({
                    'cognitive_entities': cognitive_result.entities,
                    'cognitive_key_phrases': cognitive_result.key_phrases,
                    'cognitive_sentiment': cognitive_result.sentiment,
                    'cognitive_language': cognitive_result.language
                })
                
            finally:
                os.unlink(temp_file_path)
        
        # Chunk the document
        chunks = await chunk_processor.process_document(
            text=extracted_doc.content,
            document_id=document_path,
            strategy=ChunkStrategy.RECURSIVE_CHARACTER,
            chunk_size=config['chunk_size'],
            overlap=config['chunk_overlap']
        )
        
        # Prepare chunk texts and metadata for vector storage
        chunk_texts = [chunk.content for chunk in chunks]
        chunk_metadata = []
        
        for chunk in chunks:
            metadata = {
                'title': extracted_doc.metadata.title,
                'source': document_path,
                'chunk_id': chunk.metadata.chunk_id,
                'document_id': chunk.metadata.document_id,
                'chunk_index': chunk.metadata.chunk_index,
                'token_count': chunk.metadata.token_count,
                'file_type': extracted_doc.metadata.file_type,
                'extraction_date': extracted_doc.metadata.extraction_date.isoformat()
            }
            
            # Add cognitive metadata if available
            if hasattr(extracted_doc.metadata, 'custom_metadata'):
                metadata.update(extracted_doc.metadata.custom_metadata)
            
            chunk_metadata.append(metadata)
        
        # Add to vector store
        chunk_ids = await vector_manager.add_text_documents(
            texts=chunk_texts,
            metadatas=chunk_metadata
        )
        
        # Save processed document metadata
        await save_processed_metadata(clients, document_path, {
            'document_id': document_path,
            'processed_date': datetime.utcnow().isoformat(),
            'chunk_count': len(chunks),
            'chunk_ids': chunk_ids,
            'file_size': extracted_doc.metadata.file_size,
            'file_type': extracted_doc.metadata.file_type,
            'extraction_metadata': asdict(extracted_doc.metadata)
        })
        
        return {
            "document_path": document_path,
            "chunk_count": len(chunks),
            "chunk_ids": chunk_ids,
            "processed_date": datetime.utcnow().isoformat(),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error processing document {document_path}: {str(e)}")
        raise


async def process_document_batch(clients: Dict[str, Any], document_paths: List[str], force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Process a batch of documents."""
    
    logger.info(f"Processing batch of {len(document_paths)} documents")
    
    results = []
    
    for document_path in document_paths:
        try:
            result = await process_single_document(clients, document_path, force_refresh)
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing document {document_path}: {str(e)}")
            results.append({
                "document_path": document_path,
                "status": "error",
                "error": str(e),
                "processed_date": datetime.utcnow().isoformat()
            })
    
    return results


def should_process_document(blob, force_refresh: bool = False) -> bool:
    """Check if a document should be processed."""
    
    if force_refresh:
        return True
    
    # Check if document has been processed before
    if blob.metadata and blob.metadata.get('processed_date'):
        processed_date = datetime.fromisoformat(blob.metadata['processed_date'])
        
        # Check if document was modified after processing
        if blob.last_modified > processed_date:
            return True
        
        # Skip if recently processed (within 1 hour)
        if datetime.utcnow() - processed_date < timedelta(hours=1):
            return False
    
    # Process if not processed before or if file is new
    return True


async def save_processed_metadata(clients: Dict[str, Any], document_path: str, metadata: Dict[str, Any]) -> None:
    """Save processed document metadata."""
    
    try:
        blob_client = clients['blob_client']
        container_client = blob_client.get_container_client(config['processed_container'])
        
        # Create metadata file
        metadata_filename = f"{document_path.replace('/', '_')}_metadata.json"
        metadata_blob = container_client.get_blob_client(metadata_filename)
        
        # Upload metadata
        metadata_json = json.dumps(metadata, indent=2)
        metadata_blob.upload_blob(metadata_json, overwrite=True)
        
        # Update original blob metadata
        original_container = blob_client.get_container_client(config['documents_container'])
        original_blob = original_container.get_blob_client(document_path)
        
        # Set processed metadata
        original_blob.set_blob_metadata({
            'processed_date': metadata['processed_date'],
            'chunk_count': str(metadata['chunk_count']),
            'status': 'processed'
        })
        
        logger.info(f"Saved processed metadata for {document_path}")
        
    except Exception as e:
        logger.error(f"Error saving processed metadata for {document_path}: {str(e)}")
        raise


async def cleanup_old_processed_files(clients: Dict[str, Any], retention_days: int = 30) -> None:
    """Clean up old processed files."""
    
    try:
        blob_client = clients['blob_client']
        container_client = blob_client.get_container_client(config['processed_container'])
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        deleted_count = 0
        
        # List all blobs in processed container
        blobs = container_client.list_blobs()
        
        for blob in blobs:
            if blob.last_modified < cutoff_date:
                try:
                    container_client.delete_blob(blob.name)
                    deleted_count += 1
                    logger.debug(f"Deleted old processed file: {blob.name}")
                    
                except Exception as e:
                    logger.warning(f"Error deleting old file {blob.name}: {str(e)}")
        
        logger.info(f"Cleaned up {deleted_count} old processed files")
        
    except Exception as e:
        logger.error(f"Error cleaning up old processed files: {str(e)}")
        raise


# Helper function to import modules with error handling
def safe_import(module_name: str):
    """Safely import a module with error handling."""
    try:
        return __import__(module_name, fromlist=[''])
    except ImportError as e:
        logger.error(f"Error importing {module_name}: {str(e)}")
        return None


# Utility function for async dict conversion
def asdict(obj):
    """Convert dataclass to dictionary."""
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)
