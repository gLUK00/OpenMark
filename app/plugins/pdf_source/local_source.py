"""Local filesystem PDF source plugin."""

import os
import glob
from pathlib import Path
from typing import Optional, List

from app.plugins.base import PDFSourcePlugin


class LocalSourcePlugin(PDFSourcePlugin):
    """PDF source plugin that retrieves documents from the local filesystem."""
    
    def __init__(self, config: dict):
        """Initialize the local filesystem source plugin.
        
        Args:
            config: Plugin configuration with:
                - base_path: Base directory path for PDF files (required)
                - recursive: Search subdirectories recursively (default: False)
                - allowed_extensions: List of allowed file extensions (default: ['.pdf'])
                - create_base_path: Create base_path if it doesn't exist (default: True)
        """
        super().__init__(config)
        self.base_path = config.get('base_path', './data/pdfs')
        self.recursive = config.get('recursive', False)
        self.allowed_extensions = config.get('allowed_extensions', ['.pdf'])
        self.create_base_path = config.get('create_base_path', True)
        
        # Normalize base path
        self.base_path = os.path.abspath(os.path.expanduser(self.base_path))
        
        # Create base path if needed
        if self.create_base_path and not os.path.exists(self.base_path):
            os.makedirs(self.base_path, exist_ok=True)
            print(f"Created PDF base directory: {self.base_path}")
    
    def _get_document_path(self, document_id: str) -> str:
        """Build the full file path for a document.
        
        Args:
            document_id: The document identifier (filename without extension or with .pdf)
            
        Returns:
            Full file path
        """
        # Add .pdf extension if not present
        if not document_id.lower().endswith('.pdf'):
            document_id = f"{document_id}.pdf"
        
        # Handle subdirectory paths in document_id (e.g., "2024/invoice_001")
        return os.path.join(self.base_path, document_id)
    
    def _is_safe_path(self, path: str) -> bool:
        """Check if a path is safe (doesn't escape base_path).
        
        Args:
            path: The path to check
            
        Returns:
            True if path is within base_path
        """
        # Resolve to absolute path and check it's within base_path
        resolved = os.path.realpath(path)
        base_resolved = os.path.realpath(self.base_path)
        return resolved.startswith(base_resolved)
    
    def _validate_extension(self, path: str) -> bool:
        """Check if the file has an allowed extension.
        
        Args:
            path: The file path
            
        Returns:
            True if extension is allowed
        """
        ext = os.path.splitext(path)[1].lower()
        return ext in [e.lower() for e in self.allowed_extensions]
    
    def get_document(self, document_id: str) -> Optional[bytes]:
        """Retrieve a PDF document from the local filesystem.
        
        Args:
            document_id: The document identifier
            
        Returns:
            PDF bytes if found, None otherwise
        """
        file_path = self._get_document_path(document_id)
        
        # Security check: ensure path doesn't escape base directory
        if not self._is_safe_path(file_path):
            print(f"Security warning: attempted access outside base path: {document_id}")
            return None
        
        # Validate extension
        if not self._validate_extension(file_path):
            print(f"Invalid file extension for document: {document_id}")
            return None
        
        # Check if file exists
        if not os.path.isfile(file_path):
            # Try recursive search if enabled
            if self.recursive:
                found_path = self._find_document_recursive(document_id)
                if found_path:
                    file_path = found_path
                else:
                    print(f"Document not found: {document_id}")
                    return None
            else:
                print(f"Document not found: {document_id}")
                return None
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Verify it's a PDF
            if content[:4] == b'%PDF':
                return content
            else:
                print(f"Warning: File {document_id} may not be a valid PDF")
                return content
                
        except IOError as e:
            print(f"Error reading document {document_id}: {e}")
            return None
        except PermissionError as e:
            print(f"Permission denied reading document {document_id}: {e}")
            return None
    
    def _find_document_recursive(self, document_id: str) -> Optional[str]:
        """Search for a document recursively in subdirectories.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Full path if found, None otherwise
        """
        # Add .pdf extension if not present
        if not document_id.lower().endswith('.pdf'):
            filename = f"{document_id}.pdf"
        else:
            filename = document_id
        
        # Search recursively
        pattern = os.path.join(self.base_path, '**', filename)
        matches = glob.glob(pattern, recursive=True)
        
        if matches:
            # Return first match
            return matches[0]
        return None
    
    def document_exists(self, document_id: str) -> bool:
        """Check if a document exists in the local filesystem.
        
        Args:
            document_id: The document identifier
            
        Returns:
            True if document exists, False otherwise
        """
        file_path = self._get_document_path(document_id)
        
        # Security check
        if not self._is_safe_path(file_path):
            return False
        
        # Direct path check
        if os.path.isfile(file_path):
            return True
        
        # Recursive search if enabled
        if self.recursive:
            return self._find_document_recursive(document_id) is not None
        
        return False
    
    def list_documents(self, subdirectory: str = "", max_results: int = 100) -> List[str]:
        """List available documents in the local filesystem.
        
        Args:
            subdirectory: Optional subdirectory to search in
            max_results: Maximum number of documents to return (default: 100)
            
        Returns:
            List of document IDs (filenames without .pdf extension)
        """
        search_path = os.path.join(self.base_path, subdirectory) if subdirectory else self.base_path
        
        # Security check
        if not self._is_safe_path(search_path):
            return []
        
        documents = []
        
        if self.recursive:
            pattern = os.path.join(search_path, '**', '*.pdf')
            for file_path in glob.iglob(pattern, recursive=True):
                if len(documents) >= max_results:
                    break
                # Get relative path from base_path
                rel_path = os.path.relpath(file_path, self.base_path)
                # Remove .pdf extension
                doc_id = rel_path[:-4] if rel_path.endswith('.pdf') else rel_path
                documents.append(doc_id)
        else:
            pattern = os.path.join(search_path, '*.pdf')
            for file_path in glob.iglob(pattern):
                if len(documents) >= max_results:
                    break
                # Get filename without extension
                filename = os.path.basename(file_path)
                doc_id = filename[:-4] if filename.endswith('.pdf') else filename
                documents.append(doc_id)
        
        return documents
    
    def get_document_metadata(self, document_id: str) -> Optional[dict]:
        """Get metadata for a document in the local filesystem.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Dict with document metadata, or None if not found
        """
        file_path = self._get_document_path(document_id)
        
        # Security check
        if not self._is_safe_path(file_path):
            return None
        
        # Try direct path first
        if not os.path.isfile(file_path):
            if self.recursive:
                file_path = self._find_document_recursive(document_id)
                if not file_path:
                    return None
            else:
                return None
        
        try:
            stat = os.stat(file_path)
            return {
                'document_id': document_id,
                'file_path': file_path,
                'size': stat.st_size,
                'created_at': stat.st_ctime,
                'modified_at': stat.st_mtime,
                'accessed_at': stat.st_atime
            }
        except OSError as e:
            print(f"Error getting metadata for {document_id}: {e}")
            return None
    
    def get_base_path_info(self) -> dict:
        """Get information about the base path.
        
        Returns:
            Dict with base path information
        """
        try:
            total_files = 0
            total_size = 0
            
            if self.recursive:
                pattern = os.path.join(self.base_path, '**', '*.pdf')
                for file_path in glob.iglob(pattern, recursive=True):
                    total_files += 1
                    total_size += os.path.getsize(file_path)
            else:
                pattern = os.path.join(self.base_path, '*.pdf')
                for file_path in glob.iglob(pattern):
                    total_files += 1
                    total_size += os.path.getsize(file_path)
            
            return {
                'base_path': self.base_path,
                'exists': os.path.exists(self.base_path),
                'is_directory': os.path.isdir(self.base_path),
                'recursive': self.recursive,
                'total_pdf_files': total_files,
                'total_size_bytes': total_size
            }
        except Exception as e:
            return {
                'base_path': self.base_path,
                'error': str(e)
            }
