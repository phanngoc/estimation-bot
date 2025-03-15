import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

class DatabaseManager:
    """
    Manages operations with SQLite database for storing and retrieving 
    analysis results, queries, and requirements.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize SQLite Database Manager.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses a default path.
        """
        if db_path is None:
            # Default to a database in the current directory
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database.db")
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table for storing analysis queries and results
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_text TEXT,
            input_files TEXT,
            uploaded_files TEXT,
            persist_directory TEXT,
            result_summary TEXT,
            result_data TEXT,
            total_estimate TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create table for requirements
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS requirements (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            source TEXT,
            metadata TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_query(self, input_text: str, input_files: List[str], uploaded_files: List[Dict], 
                  persist_directory: str, result_summary: str, result_data: Any, 
                  total_estimate: str):
        """
        Save a query and its results to the database.
        
        Args:
            input_text: The text input for the query
            input_files: List of input file names
            uploaded_files: List of uploaded file info dictionaries
            persist_directory: Directory where ChromaDB data is stored
            result_summary: Summary of the analysis results
            result_data: Complete analysis results object
            total_estimate: Total estimated time for the project
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert lists and objects to JSON strings for storage
        input_files_json = json.dumps(input_files)
        uploaded_files_json = json.dumps(uploaded_files)
        result_data_json = json.dumps(result_data, default=lambda o: o.__dict__)
        
        cursor.execute('''
        INSERT INTO queries 
        (input_text, input_files, uploaded_files, persist_directory, 
        result_summary, result_data, total_estimate, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            input_text, input_files_json, uploaded_files_json, persist_directory,
            result_summary, result_data_json, total_estimate, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_query(self, query_id: int) -> Dict:
        """
        Get a specific query by ID.
        
        Args:
            query_id: The ID of the query to retrieve
            
        Returns:
            Dictionary with query information or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM queries WHERE id = ?', (query_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Convert row to dictionary
        columns = [column[0] for column in cursor.description]
        query_dict = dict(zip(columns, row))
        
        # Parse JSON fields
        query_dict["input_files"] = json.loads(query_dict["input_files"]) if query_dict["input_files"] else []
        query_dict["uploaded_files"] = json.loads(query_dict["uploaded_files"]) if query_dict["uploaded_files"] else []
        query_dict["result_data"] = json.loads(query_dict["result_data"]) if query_dict["result_data"] else {}
        
        return query_dict
    
    def get_recent_queries(self, limit: int = 5) -> List[Dict]:
        """
        Get most recent queries.
        
        Args:
            limit: Maximum number of queries to return
            
        Returns:
            List of query dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, result_summary, uploaded_files, timestamp
        FROM queries
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        queries = []
        for row in rows:
            query_dict = dict(row)
            query_dict["uploaded_files"] = json.loads(query_dict["uploaded_files"]) if query_dict["uploaded_files"] else []
            queries.append(query_dict)
        
        return queries
    
    def save_requirements(self, ids: List[str], contents: List[str], source: str, 
                         metadatas: List[Dict[str, Any]]):
        """
        Save requirements to the database.
        
        Args:
            ids: List of requirement IDs
            contents: List of requirement contents
            source: Source of the requirements
            metadatas: List of metadata dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prepare data for batch insertion
        data = []
        for i in range(len(ids)):
            metadata_json = json.dumps(metadatas[i])
            data.append((ids[i], contents[i], source, metadata_json))
        
        # Insert or replace (to handle duplicates)
        cursor.executemany('''
        INSERT OR REPLACE INTO requirements
        (id, content, source, metadata)
        VALUES (?, ?, ?, ?)
        ''', data)
        
        conn.commit()
        conn.close()
    
    def get_requirements(self, limit: int = None, source: str = None) -> List[Dict]:
        """
        Get requirements from the database.
        
        Args:
            limit: Maximum number of requirements to return
            source: Filter by source
            
        Returns:
            List of requirement dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM requirements'
        params = []
        
        if source:
            query += ' WHERE source = ?'
            params.append(source)
        
        query += ' ORDER BY timestamp DESC'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        requirements = []
        for row in rows:
            req_dict = dict(row)
            req_dict["metadata"] = json.loads(req_dict["metadata"]) if req_dict["metadata"] else {}
            requirements.append(req_dict)
        
        return requirements
    
    def clear_all_queries(self):
        """
        Clear all query records from the database.
        
        Returns:
            Number of records deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get count of records before deletion
        cursor.execute('SELECT COUNT(*) FROM queries')
        count = cursor.fetchone()[0]
        
        # Delete all records
        cursor.execute('DELETE FROM queries')
        
        conn.commit()
        conn.close()
        
        return count
        
    def truncate_requirements(self):
        """
        Remove all requirements from the database.
        
        Returns:
            Number of records deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute('SELECT COUNT(*) FROM requirements')
        count = cursor.fetchone()[0]
        
        # Delete all records
        cursor.execute('DELETE FROM requirements')
        
        conn.commit()
        conn.close()
        
        return count
