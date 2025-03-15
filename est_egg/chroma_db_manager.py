import chromadb
import os
import uuid
from typing import List, Dict, Any, Optional
import hashlib
from est_egg.database_manager import DatabaseManager

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
            print('persist_directory:', persist_directory)
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()
        
        # Create or get collection for storing requirements
        self.collection = self.client.get_or_create_collection(
            name="requirements_collection",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize SQLite database manager
        self.db_manager = DatabaseManager()
    
    def add_requirement(self, content: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a requirement to the ChromaDB collection and SQLite.
        
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
        
        # Add to ChromaDB collection
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        # Also save to SQLite
        self.db_manager.save_requirements([doc_id], [content], source, [metadata])
        
        return doc_id
    
    def add_multiple_requirements(self, contents: List[str], source: str, 
                                 metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        Add multiple requirements to the ChromaDB collection and SQLite.
        If documents with the same ID already exist, they will be updated.
        
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
        print('add_multiple_requirements:doc_ids:', doc_ids)
        if metadatas is None:
            metadatas = [{} for _ in contents]
        
        # Add source and timestamp to each metadata
        for metadata in metadatas:
            metadata["source"] = source
            metadata["timestamp"] = str(uuid.uuid4())
        
        # Store in ChromaDB
        try:
            existing_ids = []
            for doc_id in doc_ids:
                try:
                    # Try to get the document by ID
                    self.collection.get(ids=[doc_id])
                    existing_ids.append(doc_id)
                except Exception:
                    # ID doesn't exist
                    pass
            
            # Separate documents into those to update and those to add
            to_update = {i: (doc_ids[i], contents[i], metadatas[i]) 
                        for i in range(len(doc_ids)) if doc_ids[i] in existing_ids}
            to_add = {i: (doc_ids[i], contents[i], metadatas[i]) 
                     for i in range(len(doc_ids)) if doc_ids[i] not in existing_ids}
            
            # Update existing documents
            if to_update:
                update_ids = [item[0] for item in to_update.values()]
                update_docs = [item[1] for item in to_update.values()]
                update_metas = [item[2] for item in to_update.values()]
                self.collection.update(
                    ids=update_ids,
                    documents=update_docs,
                    metadatas=update_metas
                )
            
            # Add new documents
            if to_add:
                add_ids = [item[0] for item in to_add.values()]
                add_docs = [item[1] for item in to_add.values()]
                add_metas = [item[2] for item in to_add.values()]
                self.collection.add(
                    ids=add_ids,
                    documents=add_docs,
                    metadatas=add_metas
                )
        except Exception as e:
            # Fallback to direct add with upsert if the above approach fails
            print(f"Using fallback method for adding documents: {str(e)}")
            self.collection.upsert(
                documents=contents,
                metadatas=metadatas,
                ids=doc_ids
            )
        
        # Also save to SQLite - will handle duplicates with INSERT OR REPLACE
        self.db_manager.save_requirements(doc_ids, contents, source, metadatas)
        
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
