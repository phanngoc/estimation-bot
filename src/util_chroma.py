import chromadb
from chromadb.config import Settings
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

def delete_chroma_collection(
    collection_name: str,
    persist_directory: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None
) -> bool:
    """
    Delete a Chroma collection by name.
    
    Args:
        collection_name: Name of the collection to delete
        persist_directory: Local directory for persistence if using local Chroma
        host: Host address if using Chroma server mode
        port: Port number if using Chroma server mode
        
    Returns:
        bool: True if collection was successfully deleted, False otherwise
    """
    try:
        # Configure client based on provided parameters
        if host and port:
            # Use Chroma in client mode
            client = chromadb.HttpClient(host=host, port=port)
            logger.info(f"Connected to Chroma server at {host}:{port}")
        else:
            # Use Chroma in local mode
            if not persist_directory:
                persist_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
            
            client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            logger.info(f"Connected to local Chroma DB at {persist_directory}")
        
        # List all collections
        collections = client.list_collections()
        collection_names = [collection.name for collection in collections]
        
        # Check if collection exists
        if collection_name not in collection_names:
            logger.warning(f"Collection '{collection_name}' does not exist. Available collections: {collection_names}")
            return False
        
        # Delete the collection
        client.delete_collection(name=collection_name)
        logger.info(f"Successfully deleted collection '{collection_name}'")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete collection '{collection_name}': {str(e)}")
        return False
    

def list_chroma_collections(
    persist_directory: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None
) -> list:
    """
    List all available Chroma collections.
    
    Args:
        persist_directory: Local directory for persistence if using local Chroma
        host: Host address if using Chroma server mode
        port: Port number if using Chroma server mode
        
    Returns:
        list: List of collection names
    """
    try:
        if host and port:
            client = chromadb.HttpClient(host=host, port=port)
            logger.info(f"Connected to Chroma server at {host}:{port}")
        else:
            if not persist_directory:
                persist_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db")
            
            client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            logger.info(f"Connected to local Chroma DB at {persist_directory}")
            
        collections = client.list_collections()
        collection_names = [collection.name for collection in collections]
        logger.info(f"Found collections: {collection_names}")
        return collection_names
        
    except Exception as e:
        logger.error(f"Failed to list collections: {str(e)}")
        return []
    
print('list_chroma_collections:', list_chroma_collections('./data'))