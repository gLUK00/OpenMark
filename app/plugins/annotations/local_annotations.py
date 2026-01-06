"""Local file-based annotations storage plugin."""

import json
import os
from typing import Optional
from datetime import datetime

from app.plugins.base import AnnotationsPlugin


class LocalAnnotationsPlugin(AnnotationsPlugin):
    """Annotations plugin using local JSON file for storage."""
    
    def __init__(self, config: dict):
        """Initialize the local annotations plugin.
        
        Args:
            config: Plugin configuration with 'storage_path'
        """
        super().__init__(config)
        self.storage_path = config.get('storage_path', './data/annotations.json')
        self._annotations = self._load_annotations()
    
    def _load_annotations(self) -> dict:
        """Load annotations from JSON file.
        
        Returns:
            Dictionary of annotations
        """
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_annotations_file(self):
        """Save annotations to JSON file."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self._annotations, f, indent=2)
    
    def _get_key(self, user_id: str, document_id: str) -> str:
        """Generate a unique key for user/document combination.
        
        Args:
            user_id: The user identifier
            document_id: The document identifier
            
        Returns:
            Unique key string
        """
        return f"{user_id}:{document_id}"
    
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
        try:
            key = self._get_key(user_id, document_id)
            
            # Add metadata
            annotations['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            if key not in self._annotations:
                annotations['created_at'] = annotations['updated_at']
            
            self._annotations[key] = annotations
            self._save_annotations_file()
            return True
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
        key = self._get_key(user_id, document_id)
        annotations = self._annotations.get(key, {})
        
        return {
            'notes': annotations.get('notes', []),
            'highlights': annotations.get('highlights', [])
        }
