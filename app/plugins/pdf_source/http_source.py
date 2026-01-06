"""HTTP-based PDF source plugin."""

import os
from typing import Optional
from urllib.parse import urljoin

import requests

from app.plugins.base import PDFSourcePlugin


class HTTPSourcePlugin(PDFSourcePlugin):
    """PDF source plugin that retrieves documents via HTTP/HTTPS."""
    
    def __init__(self, config: dict):
        """Initialize the HTTP source plugin.
        
        Args:
            config: Plugin configuration with 'base_url', 'timeout', and optional 'headers'
        """
        super().__init__(config)
        self.base_url = config.get('base_url', '')
        self.timeout = config.get('timeout', 30)
        self.headers = config.get('headers', {})
        self.local_path = config.get('local_path', './data/pdfs')
    
    def _get_document_url(self, document_id: str) -> str:
        """Build the full URL for a document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Full document URL
        """
        if self.base_url:
            # Add .pdf extension if not present
            if not document_id.endswith('.pdf'):
                document_id = f"{document_id}.pdf"
            return urljoin(self.base_url, document_id)
        return document_id
    
    def _get_local_path(self, document_id: str) -> str:
        """Get local file path for a document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Local file path
        """
        if not document_id.endswith('.pdf'):
            document_id = f"{document_id}.pdf"
        return os.path.join(self.local_path, document_id)
    
    def get_document(self, document_id: str) -> Optional[bytes]:
        """Retrieve a PDF document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            PDF bytes if found, None otherwise
        """
        # First try local path
        local_path = self._get_local_path(document_id)
        if os.path.exists(local_path):
            try:
                with open(local_path, 'rb') as f:
                    return f.read()
            except IOError:
                pass
        
        # Then try HTTP if base_url is configured
        if self.base_url:
            try:
                url = self._get_document_url(document_id)
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.content
            except requests.RequestException:
                pass
        
        return None
    
    def document_exists(self, document_id: str) -> bool:
        """Check if a document exists.
        
        Args:
            document_id: The document identifier
            
        Returns:
            True if document exists, False otherwise
        """
        # First check local path
        local_path = self._get_local_path(document_id)
        if os.path.exists(local_path):
            return True
        
        # Then check HTTP if base_url is configured
        if self.base_url:
            try:
                url = self._get_document_url(document_id)
                response = requests.head(
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                return response.status_code == 200
            except requests.RequestException:
                pass
        
        return False
