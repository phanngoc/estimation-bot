import argparse
import chromadb
from chromadb.config import Settings
from pprint import pprint
import os
import sys
from typing import Optional, List, Dict, Any

def connect_to_chroma(
    persist_directory: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None
):
    """Connect to ChromaDB instance (either local or remote)"""
    try:
        if host and port:
            # Connect to Chroma server
            client = chromadb.HttpClient(host=host, port=port)
            print(f"Connected to Chroma server at {host}:{port}")
        else:
            # Use local persistent instance
            if not persist_directory:
                # Default location in the project
                persist_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                              "est_egg", "chroma_db")
            
            if not os.path.exists(persist_directory):
                print(f"Warning: Directory '{persist_directory}' doesn't exist. Creating it.")
                os.makedirs(persist_directory, exist_ok=True)
                
            client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            print(f"Connected to local Chroma DB at {persist_directory}")
        
        return client
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")
        return None

def list_collections(client):
    """List all available collections"""
    try:
        collections = client.list_collections()
        if collections:
            print(f"\nFound {len(collections)} collections:")
            for i, collection in enumerate(collections, 1):
                print(f"{i}. {collection.name} (count: {collection.count()})")
            return [c.name for c in collections]
        else:
            print("No collections found in the database.")
            return []
    except Exception as e:
        print(f"Error listing collections: {e}")
        return []

def get_collection_info(client, collection_name: str):
    """Get detailed information about a specific collection"""
    try:
        collection = client.get_collection(name=collection_name)
        count = collection.count()
        print(f"\nCollection: {collection_name}")
        print(f"Document count: {count}")
        
        # Get sample data to examine schema
        if count > 0:
            sample = collection.peek(limit=1)
            print("\nSample document structure:")
            print(f"- IDs: {sample['ids']}")
            if 'metadatas' in sample and sample['metadatas']:
                print(f"- Metadata keys: {list(sample['metadatas'][0].keys())}")
            if 'documents' in sample and sample['documents']:
                doc_preview = sample['documents'][0]
                if len(doc_preview) > 100:
                    doc_preview = doc_preview[:100] + "..."
                print(f"- Document preview: {doc_preview}")
                
        return collection
    except Exception as e:
        print(f"Error getting collection '{collection_name}': {e}")
        return None

def query_collection(collection, query_text: Optional[str] = None, filter_dict: Optional[Dict] = None, 
                    limit: int = 5, include_documents: bool = True):
    """Query the collection with optional filtering"""
    try:
        if query_text:
            # Query by similarity
            results = collection.query(
                query_texts=[query_text],
                n_results=limit,
                where=filter_dict
            )
            print(f"\nResults for query: '{query_text}'")
        else:
            # Get documents by filter only
            results = collection.get(
                where=filter_dict,
                limit=limit
            )
            print("\nResults for filter query")
        
        # Display results
        if results and 'ids' in results and results['ids']:
            result_count = len(results['ids'][0]) if query_text else len(results['ids'])
            print(f"Found {result_count} results")
            
            if result_count > 0:
                print("\nRESULTS:")
                
                # Format based on query type
                if query_text:  # Results from query() method
                    ids = results['ids'][0]
                    distances = results.get('distances', [[]])[0] if 'distances' in results else None
                    metadatas = results.get('metadatas', [[]])[0] if 'metadatas' in results else None
                    documents = results.get('documents', [[]])[0] if include_documents and 'documents' in results else None
                    
                    for i, doc_id in enumerate(ids):
                        print(f"\n--- Result {i+1} ---")
                        print(f"ID: {doc_id}")
                        if distances:
                            print(f"Distance: {distances[i]}")
                        if metadatas:
                            print("Metadata:")
                            pprint(metadatas[i])
                        if documents:
                            print("Document (preview):")
                            doc_preview = documents[i]
                            if len(doc_preview) > 200:
                                doc_preview = doc_preview[:200] + "..."
                            print(doc_preview)
                else:  # Results from get() method
                    ids = results['ids']
                    metadatas = results.get('metadatas', []) if 'metadatas' in results else None
                    documents = results.get('documents', []) if include_documents and 'documents' in results else None
                    
                    for i, doc_id in enumerate(ids):
                        print(f"\n--- Result {i+1} ---")
                        print(f"ID: {doc_id}")
                        if metadatas:
                            print("Metadata:")
                            pprint(metadatas[i])
                        if documents:
                            print("Document (preview):")
                            doc_preview = documents[i]
                            if len(doc_preview) > 200:
                                doc_preview = doc_preview[:200] + "..."
                            print(doc_preview)
        else:
            print("No results found")
            
        return results
    except Exception as e:
        print(f"Error querying collection: {e}")
        return None

def interactive_mode(client):
    """Run an interactive session for exploring ChromaDB"""
    print("\nWelcome to ChromaDB Explorer")
    
    while True:
        collections = list_collections(client)
        if not collections:
            create = input("\nNo collections found. Create a collection? (y/n): ").lower()
            if create == 'y':
                name = input("Enter collection name: ")
                if name:
                    client.create_collection(name=name)
                    continue
            else:
                print("Exiting - no collections to explore.")
                break
        
        # Select collection
        selected = input("\nEnter collection number to explore (or q to quit): ")
        if selected.lower() == 'q':
            break
        
        try:
            idx = int(selected) - 1
            if 0 <= idx < len(collections):
                collection_name = collections[idx]
                collection = get_collection_info(client, collection_name)
                
                if collection:
                    # Collection-specific operations
                    while True:
                        print("\nOptions:")
                        print("1. Query by text similarity")
                        print("2. Filter by metadata")
                        print("3. Get document count")
                        print("4. Peek at documents")
                        print("5. Return to collections list")
                        
                        option = input("\nChoose an option (1-5): ")
                        
                        if option == '1':
                            query = input("Enter query text: ")
                            limit = input("Max results (default 5): ")
                            limit = int(limit) if limit.isdigit() else 5
                            query_collection(collection, query_text=query, limit=limit)
                        
                        elif option == '2':
                            print("\nEnter metadata filter (example: source=filename)")
                            filter_input = input("Filter: ")
                            filter_dict = {}
                            
                            if filter_input:
                                try:
                                    key, value = filter_input.split('=', 1)
                                    filter_dict = {key.strip(): value.strip()}
                                except:
                                    print("Invalid filter format. Use key=value")
                                    continue
                            
                            limit = input("Max results (default 5): ")
                            limit = int(limit) if limit.isdigit() else 5
                            query_collection(collection, filter_dict=filter_dict, limit=limit)
                        
                        elif option == '3':
                            count = collection.count()
                            print(f"Collection '{collection_name}' has {count} documents")
                        
                        elif option == '4':
                            limit = input("Number of documents to peek (default 5): ")
                            limit = int(limit) if limit.isdigit() else 5
                            results = collection.peek(limit=limit)
                            print("\nPeeking at documents:")
                            
                            for i in range(len(results['ids'])):
                                print(f"\n--- Document {i+1} ---")
                                print(f"ID: {results['ids'][i]}")
                                if 'metadatas' in results and results['metadatas']:
                                    print("Metadata:")
                                    pprint(results['metadatas'][i])
                                if 'documents' in results and results['documents']:
                                    print("Content:")
                                    doc = results['documents'][i]
                                    if len(doc) > 500:
                                        doc = doc[:500] + "..."
                                    print(doc)
                        
                        elif option == '5':
                            break
            else:
                print("Invalid selection")
        except ValueError:
            print("Please enter a valid number")

def main():
    parser = argparse.ArgumentParser(description="ChromaDB Query Tool")
    parser.add_argument("--dir", help="Directory where ChromaDB is persisted")
    parser.add_argument("--host", help="ChromaDB server host")
    parser.add_argument("--port", type=int, help="ChromaDB server port")
    parser.add_argument("--collection", help="Collection name to examine")
    parser.add_argument("--query", help="Query text to search for similar documents")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    # Connect to ChromaDB
    client = connect_to_chroma(
        persist_directory=args.dir,
        host=args.host,
        port=args.port
    )
    
    if not client:
        sys.exit(1)
    
    # Run in interactive mode if requested
    if args.interactive:
        interactive_mode(client)
        sys.exit(0)
    
    # List collections if no specific one is provided
    if not args.collection:
        list_collections(client)
        sys.exit(0)
    
    # Get the specified collection
    collection = get_collection_info(client, args.collection)
    if not collection:
        sys.exit(1)
    
    # Query if requested
    if args.query:
        query_collection(collection, query_text=args.query)

if __name__ == "__main__":
    main()

