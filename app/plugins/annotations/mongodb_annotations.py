"""MongoDB-based annotations storage plugin."""

from typing import Optional
from datetime import datetime

from app.plugins.base import AnnotationsPlugin


class MongoDBAnnotationsPlugin(AnnotationsPlugin):
    """Annotations plugin using MongoDB for storage."""
    
    def __init__(self, config: dict):
        """Initialize the MongoDB annotations plugin.
        
        Args:
            config: Plugin configuration with 'connection_string', 'database', 'collection'
        """
        super().__init__(config)
        self.connection_string = config.get('connection_string', 'mongodb://localhost:27017')
        self.database_name = config.get('database', 'openmark')
        self.collection_name = config.get('collection', 'annotations')
        
        self._client = None
        self._db = None
        self._collection = None
        
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB."""
        try:
            from pymongo import MongoClient
            
            self._client = MongoClient(self.connection_string)
            self._db = self._client[self.database_name]
            self._collection = self._db[self.collection_name]
            
            # Create index for faster lookups
            self._collection.create_index([('user_id', 1), ('document_id', 1)], unique=True)
        except Exception as e:
            print(f"Warning: Could not connect to MongoDB: {e}")
            self._collection = None
    
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
        if self._collection is None:
            return False
        
        try:
            now = datetime.utcnow()
            
            result = self._collection.update_one(
                {'user_id': user_id, 'document_id': document_id},
                {
                    '$set': {
                        'notes': annotations.get('notes', []),
                        'highlights': annotations.get('highlights', []),
                        'updated_at': now
                    },
                    '$setOnInsert': {
                        'created_at': now
                    }
                },
                upsert=True
            )
            
            return result.acknowledged
        except Exception:
            return False
    
    def get_annotations(self, user_id: str, document_id: str) -> dict:
        """Retrieve annotations for a document.
        
        Args:
            user_id: The user identifier
            document_id: The document identifier
            
        Returns:
            Dict containing 'notes' and 'highlights' lists
        """
        if self._collection is None:
            return {'notes': [], 'highlights': []}
        
        try:
            doc = self._collection.find_one({
                'user_id': user_id,
                'document_id': document_id
            })
            
            if doc:
                return {
                    'notes': doc.get('notes', []),
                    'highlights': doc.get('highlights', [])
                }
        except Exception:
            pass
        
        return {'notes': [], 'highlights': []}
