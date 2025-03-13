import sqlite3
import json
import os
import datetime
from typing import List, Dict, Any, Optional


class DatabaseManager:
    """
    Manages SQLite database operations for storing and retrieving query history.
    """
    
    def __init__(self, db_path: str = "est_app.db"):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.initialize_database()
    
    def initialize_database(self):
        """
        Create database tables if they don't exist.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create queries table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            input_text TEXT,
            input_files TEXT,  -- JSON serialized file names
            uploaded_files TEXT,  -- JSON serialized paths to uploaded files
            persist_directory TEXT,
            result_summary TEXT,
            result_data TEXT,  -- JSON serialized result data
            total_estimate TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_query(self, 
                  input_text: str, 
                  input_files: List[str],
                  uploaded_files: List[Dict[str, str]], 
                  persist_directory: str,
                  result_summary: str, 
                  result_data: Any,
                  total_estimate: str) -> int:
        """
        Save a query and its results to the database.
        
        Args:
            input_text: The input requirement text
            input_files: List of input file names
            uploaded_files: List of dicts with info about uploaded files
            persist_directory: ChromaDB persistence directory used
            result_summary: Summary of the analysis result
            result_data: Full result data to serialize
            total_estimate: Total time estimate
            
        Returns:
            ID of the inserted record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert result_data to JSON
        result_data_json = json.dumps(result_data, default=lambda x: x.__dict__)
        
        # Current timestamp
        timestamp = datetime.datetime.now().isoformat()
        
        # Insert query record
        cursor.execute('''
        INSERT INTO queries (timestamp, input_text, input_files, uploaded_files, persist_directory, 
                           result_summary, result_data, total_estimate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, input_text, json.dumps(input_files), json.dumps(uploaded_files),
              persist_directory, result_summary, result_data_json, total_estimate))
        
        # Get the ID of the inserted record
        query_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return query_id
    
    def get_recent_queries(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the most recent queries from the database.
        
        Args:
            limit: Maximum number of queries to retrieve
            
        Returns:
            List of query records
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable row factory to access columns by name
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, timestamp, input_text, input_files, uploaded_files, result_summary, total_estimate
        FROM queries
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        
        # Convert rows to dictionaries
        queries = []
        for row in rows:
            query = dict(row)
            # Parse JSON fields
            if query['input_files']:
                query['input_files'] = json.loads(query['input_files'])
            if query.get('uploaded_files'):
                query['uploaded_files'] = json.loads(query['uploaded_files'])
            queries.append(query)
        
        conn.close()
        
        return queries
    
    def get_query_by_id(self, query_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific query by its ID.
        
        Args:
            query_id: ID of the query to retrieve
            
        Returns:
            Query record or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, timestamp, input_text, input_files, uploaded_files, persist_directory,
               result_summary, result_data, total_estimate
        FROM queries
        WHERE id = ?
        ''', (query_id,))
        
        row = cursor.fetchone()
        
        if row is None:
            conn.close()
            return None
        
        query = dict(row)
        
        # Parse JSON fields
        if query['input_files']:
            query['input_files'] = json.loads(query['input_files'])
        if query.get('uploaded_files'):
            query['uploaded_files'] = json.loads(query['uploaded_files'])
        if query['result_data']:
            query['result_data'] = json.loads(query['result_data'])
        
        conn.close()
        
        return query
    
    def delete_query(self, query_id: int) -> bool:
        """
        Delete a query from the database.
        
        Args:
            query_id: ID of the query to delete
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM queries WHERE id = ?', (query_id,))
        
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return success
