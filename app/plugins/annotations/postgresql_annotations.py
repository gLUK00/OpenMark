"""PostgreSQL-based annotations storage plugin."""

import json
from typing import Optional
from datetime import datetime

from app.plugins.base import AnnotationsPlugin

# Try to import psycopg2
try:
    import psycopg2
    from psycopg2 import pool
    from psycopg2.extras import RealDictCursor, Json
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class PostgreSQLAnnotationsPlugin(AnnotationsPlugin):
    """Annotations plugin using PostgreSQL for storage.
    
    Requires: pip install psycopg2-binary
    
    This plugin stores annotations in a PostgreSQL database with JSONB columns
    for efficient storage and querying of notes and highlights.
    """
    
    # SQL statements for table creation
    CREATE_TABLE = '''
        CREATE TABLE IF NOT EXISTS {table} (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            document_id VARCHAR(255) NOT NULL,
            notes JSONB DEFAULT '[]'::jsonb,
            highlights JSONB DEFAULT '[]'::jsonb,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, document_id)
        )
    '''
    
    CREATE_INDEXES = '''
        CREATE INDEX IF NOT EXISTS idx_{table}_user_doc ON {table}(user_id, document_id);
        CREATE INDEX IF NOT EXISTS idx_{table}_user ON {table}(user_id);
        CREATE INDEX IF NOT EXISTS idx_{table}_doc ON {table}(document_id);
        CREATE INDEX IF NOT EXISTS idx_{table}_notes ON {table} USING GIN (notes);
        CREATE INDEX IF NOT EXISTS idx_{table}_highlights ON {table} USING GIN (highlights);
    '''
    
    def __init__(self, config: dict):
        """Initialize the PostgreSQL annotations plugin.
        
        Args:
            config: Plugin configuration with:
                - host: PostgreSQL host (default: localhost)
                - port: PostgreSQL port (default: 5432)
                - database: Database name (default: openmark)
                - user: Database user (default: openmark)
                - password: Database password (required)
                - table: Annotations table name (default: annotations)
                - pool_min_conn: Minimum pool connections (default: 1)
                - pool_max_conn: Maximum pool connections (default: 10)
                - create_table: Auto-create table on startup (default: True)
                
                Alternative connection:
                - connection_string: Full PostgreSQL connection URI
        """
        super().__init__(config)
        
        if not PSYCOPG2_AVAILABLE:
            raise ImportError(
                "PostgreSQL annotations plugin requires psycopg2. "
                "Install it with: pip install psycopg2-binary"
            )
        
        # Connection parameters
        self.connection_string = config.get('connection_string')
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 5432)
        self.database = config.get('database', 'openmark')
        self.user = config.get('user', 'openmark')
        self.password = config.get('password')
        
        # Table name
        self.table = config.get('table', 'annotations')
        
        # Connection pool settings
        self.pool_min_conn = config.get('pool_min_conn', 1)
        self.pool_max_conn = config.get('pool_max_conn', 10)
        
        # Auto-create table
        self.create_table = config.get('create_table', True)
        
        # Initialize connection pool
        self._pool = None
        self._connect()
    
    def _connect(self):
        """Establish connection pool to PostgreSQL."""
        try:
            if self.connection_string:
                self._pool = pool.ThreadedConnectionPool(
                    self.pool_min_conn,
                    self.pool_max_conn,
                    self.connection_string
                )
            else:
                self._pool = pool.ThreadedConnectionPool(
                    self.pool_min_conn,
                    self.pool_max_conn,
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
            
            if self.create_table:
                self._setup_table()
                
        except psycopg2.Error as e:
            print(f"Warning: Could not connect to PostgreSQL: {e}")
            self._pool = None
    
    def _get_connection(self):
        """Get a connection from the pool."""
        if self._pool:
            return self._pool.getconn()
        return None
    
    def _put_connection(self, conn):
        """Return a connection to the pool."""
        if self._pool and conn:
            self._pool.putconn(conn)
    
    def _setup_table(self):
        """Create the annotations table and indexes."""
        conn = self._get_connection()
        if not conn:
            return
            
        try:
            with conn.cursor() as cur:
                # Create table
                cur.execute(self.CREATE_TABLE.format(table=self.table))
                
                # Create indexes
                for statement in self.CREATE_INDEXES.format(table=self.table).split(';'):
                    if statement.strip():
                        cur.execute(statement)
                
                conn.commit()
                
        except psycopg2.Error as e:
            print(f"Warning: Could not create annotations table: {e}")
            conn.rollback()
        finally:
            self._put_connection(conn)
    
    def save_annotations(self, user_id: str, document_id: str, 
                         annotations: dict) -> bool:
        """Save annotations for a document.
        
        Args:
            user_id: The user identifier
            document_id: The document identifier
            annotations: Dict containing 'notes' and 'highlights' lists
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                notes = annotations.get('notes', [])
                highlights = annotations.get('highlights', [])
                now = datetime.utcnow()
                
                # Upsert: insert or update on conflict
                cur.execute(f'''
                    INSERT INTO {self.table} (user_id, document_id, notes, highlights, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, document_id)
                    DO UPDATE SET
                        notes = EXCLUDED.notes,
                        highlights = EXCLUDED.highlights,
                        updated_at = EXCLUDED.updated_at
                ''', (
                    user_id,
                    document_id,
                    Json(notes),
                    Json(highlights),
                    now,
                    now
                ))
                
                conn.commit()
                return True
                
        except psycopg2.Error as e:
            print(f"Error saving annotations: {e}")
            conn.rollback()
            return False
        finally:
            self._put_connection(conn)
    
    def get_annotations(self, user_id: str, document_id: str) -> dict:
        """Retrieve annotations for a document.
        
        Args:
            user_id: The user identifier
            document_id: The document identifier
            
        Returns:
            Dict containing 'notes' and 'highlights' lists
        """
        conn = self._get_connection()
        if not conn:
            return {'notes': [], 'highlights': []}
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f'''
                    SELECT notes, highlights 
                    FROM {self.table} 
                    WHERE user_id = %s AND document_id = %s
                ''', (user_id, document_id))
                
                row = cur.fetchone()
                
                if row:
                    return {
                        'notes': row['notes'] or [],
                        'highlights': row['highlights'] or []
                    }
                    
        except psycopg2.Error as e:
            print(f"Error getting annotations: {e}")
        finally:
            self._put_connection(conn)
        
        return {'notes': [], 'highlights': []}
    
    # Additional utility methods
    
    def delete_annotations(self, user_id: str, document_id: str) -> bool:
        """Delete annotations for a document.
        
        Args:
            user_id: The user identifier
            document_id: The document identifier
            
        Returns:
            True if successful, False otherwise
        """
        conn = self._get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cur:
                cur.execute(f'''
                    DELETE FROM {self.table} 
                    WHERE user_id = %s AND document_id = %s
                ''', (user_id, document_id))
                
                conn.commit()
                return cur.rowcount > 0
                
        except psycopg2.Error:
            conn.rollback()
            return False
        finally:
            self._put_connection(conn)
    
    def get_user_documents(self, user_id: str, offset: int = 0, limit: int = 100) -> list:
        """Get all documents with annotations for a user.
        
        Args:
            user_id: The user identifier
            offset: Number of documents to skip
            limit: Maximum number of documents to return
            
        Returns:
            List of document IDs with annotation counts
        """
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f'''
                    SELECT 
                        document_id,
                        jsonb_array_length(notes) as notes_count,
                        jsonb_array_length(highlights) as highlights_count,
                        updated_at
                    FROM {self.table} 
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    OFFSET %s LIMIT %s
                ''', (user_id, offset, limit))
                
                return [dict(row) for row in cur.fetchall()]
                
        except psycopg2.Error:
            return []
        finally:
            self._put_connection(conn)
    
    def get_document_users(self, document_id: str) -> list:
        """Get all users who have annotated a document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            List of user IDs with annotation counts
        """
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(f'''
                    SELECT 
                        user_id,
                        jsonb_array_length(notes) as notes_count,
                        jsonb_array_length(highlights) as highlights_count,
                        updated_at
                    FROM {self.table} 
                    WHERE document_id = %s
                    ORDER BY updated_at DESC
                ''', (document_id,))
                
                return [dict(row) for row in cur.fetchall()]
                
        except psycopg2.Error:
            return []
        finally:
            self._put_connection(conn)
    
    def search_notes(self, user_id: str, search_text: str, limit: int = 50) -> list:
        """Search notes by text content.
        
        Args:
            user_id: The user identifier
            search_text: Text to search for in notes
            limit: Maximum number of results
            
        Returns:
            List of matching documents with notes containing search text
        """
        conn = self._get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Search in JSONB notes array for text content
                cur.execute(f'''
                    SELECT document_id, notes, updated_at
                    FROM {self.table}
                    WHERE user_id = %s
                    AND EXISTS (
                        SELECT 1 FROM jsonb_array_elements(notes) AS note
                        WHERE note->>'text' ILIKE %s
                    )
                    ORDER BY updated_at DESC
                    LIMIT %s
                ''', (user_id, f'%{search_text}%', limit))
                
                return [dict(row) for row in cur.fetchall()]
                
        except psycopg2.Error:
            return []
        finally:
            self._put_connection(conn)
    
    def get_statistics(self, user_id: Optional[str] = None) -> dict:
        """Get annotation statistics.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            Statistics dict with counts
        """
        conn = self._get_connection()
        if not conn:
            return {'total_documents': 0, 'total_notes': 0, 'total_highlights': 0}
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if user_id:
                    cur.execute(f'''
                        SELECT 
                            COUNT(DISTINCT document_id) as total_documents,
                            COALESCE(SUM(jsonb_array_length(notes)), 0) as total_notes,
                            COALESCE(SUM(jsonb_array_length(highlights)), 0) as total_highlights
                        FROM {self.table}
                        WHERE user_id = %s
                    ''', (user_id,))
                else:
                    cur.execute(f'''
                        SELECT 
                            COUNT(DISTINCT document_id) as total_documents,
                            COALESCE(SUM(jsonb_array_length(notes)), 0) as total_notes,
                            COALESCE(SUM(jsonb_array_length(highlights)), 0) as total_highlights
                        FROM {self.table}
                    ''')
                
                row = cur.fetchone()
                if row:
                    return {
                        'total_documents': row['total_documents'] or 0,
                        'total_notes': row['total_notes'] or 0,
                        'total_highlights': row['total_highlights'] or 0
                    }
                    
        except psycopg2.Error:
            pass
        finally:
            self._put_connection(conn)
        
        return {'total_documents': 0, 'total_notes': 0, 'total_highlights': 0}
    
    def close(self):
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()
