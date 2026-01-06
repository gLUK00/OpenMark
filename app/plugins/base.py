"""Base classes for OpenMark plugins."""

from abc import ABC, abstractmethod
from typing import Optional


class AuthenticationPlugin(ABC):
    """Base class for authentication plugins."""
    
    def __init__(self, config: dict):
        """Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        self.config = config
    
    @abstractmethod
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            Dict with 'token' and 'expires_at' keys if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> Optional[dict]:
        """Validate an authentication token.
        
        Args:
            token: The authentication token
            
        Returns:
            User dict with 'username' and 'role' keys if valid, None otherwise
        """
        pass
    
    @abstractmethod
    def invalidate_token(self, token: str) -> bool:
        """Invalidate an authentication token.
        
        Args:
            token: The authentication token
            
        Returns:
            True if successful, False otherwise
        """
        pass


class PDFSourcePlugin(ABC):
    """Base class for PDF source plugins."""
    
    def __init__(self, config: dict):
        """Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        self.config = config
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[bytes]:
        """Retrieve a PDF document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            PDF bytes if found, None otherwise
        """
        pass
    
    @abstractmethod
    def document_exists(self, document_id: str) -> bool:
        """Check if a document exists.
        
        Args:
            document_id: The document identifier
            
        Returns:
            True if document exists, False otherwise
        """
        pass


class AnnotationsPlugin(ABC):
    """Base class for annotations storage plugins."""
    
    def __init__(self, config: dict):
        """Initialize the plugin with configuration.
        
        Args:
            config: Plugin configuration dictionary
        """
        self.config = config
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_annotations(self, user_id: str, document_id: str) -> dict:
        """Retrieve annotations for a document.
        
        Args:
            user_id: The user identifier
            document_id: The document identifier
            
        Returns:
            Dict containing 'notes' and 'highlights' lists
        """
        pass
