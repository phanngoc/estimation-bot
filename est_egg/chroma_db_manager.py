import chromadb
import os
import uuid
from typing import List, Dict, Any, Optional
import hashlib


class ChromaDBManager:
    """
    Manages operations with ChromaDB for storing and retrieving requirements.
    """
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize ChromaDB Manager.
        
        Args:
            persist_directory: Directory to persist ChromaDB data. If None, uses in-memory database.
        """
        if persist_directory:
            os.makedirs(persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()
        
        # Create or get collection for storing requirements
        self.collection = self.client.get_or_create_collection(
            name="requirements_collection",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_requirement(self, content: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a requirement to the ChromaDB collection.
        
        Args:
            content: The requirement content
            source: Source of the requirement (filename, user input, etc.)
            metadata: Additional metadata for the requirement
            
        Returns:
            ID of the stored document
        """
        # Generate a deterministic ID based on content to avoid duplicates
        doc_id = hashlib.md5(content.encode()).hexdigest()
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        metadata["source"] = source
        metadata["timestamp"] = str(uuid.uuid4())
        
        # Add to collection
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def add_multiple_requirements(self, contents: List[str], source: str, 
                                 metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        Add multiple requirements to the ChromaDB collection.
        
        Args:
            contents: List of requirement contents
            source: Source of the requirements
            metadatas: List of metadata for each requirement
            
        Returns:
            List of IDs for the stored documents
        """
        if not contents:
            return []
        
        # Generate IDs and prepare metadata
        doc_ids = [hashlib.md5(content.encode()).hexdigest() for content in contents]
        
        if metadatas is None:
            metadatas = [{} for _ in contents]
        
        # Add source and timestamp to each metadata
        for metadata in metadatas:
            metadata["source"] = source
            metadata["timestamp"] = str(uuid.uuid4())
        
        # Add to collection
        self.collection.add(
            documents=contents,
            metadatas=metadatas,
            ids=doc_ids
        )
        
        return doc_ids
    
    def query_similar_requirements(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query the database for requirements similar to the query.
        
        Args:
            query: Query string
            n_results: Number of results to return
            
        Returns:
            List of matching requirements with their metadata
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Format results for easy consumption
        formatted_results = []
        
        if results['documents'] and len(results['documents']) > 0:
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]
            ids = results['ids'][0]
            
            for doc, meta, dist, id_ in zip(documents, metadatas, distances, ids):
                formatted_results.append({
                    "id": id_,
                    "content": doc,
                    "metadata": meta,
                    "relevance_score": 1.0 - dist  # Convert distance to similarity score
                })
        
        return formatted_results
    
    def delete_requirement(self, doc_id: str) -> bool:
        """
        Delete a requirement from the collection.
        
        Args:
            doc_id: ID of the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False
    
    def count_requirements(self) -> int:
        """
        Count the number of requirements stored in the collection.
        
        Returns:
            Number of requirements
        """
        return self.collection.count()
