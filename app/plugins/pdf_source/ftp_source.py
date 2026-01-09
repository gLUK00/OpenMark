"""FTP-based PDF source plugin."""

import ftplib
import io
from typing import Optional, List

from app.plugins.base import PDFSourcePlugin


class FTPSourcePlugin(PDFSourcePlugin):
    """PDF source plugin that retrieves documents from an FTP/FTPS server."""
    
    def __init__(self, config: dict):
        """Initialize the FTP source plugin.
        
        Args:
            config: Plugin configuration with FTP settings:
                - host: FTP server hostname or IP (required)
                - port: FTP server port (default: 21)
                - username: Username for authentication (default: 'anonymous')
                - password: Password for authentication (default: '')
                - prefix: Directory path prefix for documents (optional, e.g., '/documents/pdfs')
                - passive: Use passive mode (default: True)
                - timeout: Connection timeout in seconds (default: 30)
                - use_tls: Use FTPS (FTP over TLS) (default: False)
                - encoding: Server encoding (default: 'utf-8')
        """
        super().__init__(config)
        self.host = config.get('host')
        if not self.host:
            raise ValueError("FTP plugin requires 'host' in configuration")
        
        self.port = config.get('port', 21)
        self.username = config.get('username', 'anonymous')
        self.password = config.get('password', '')
        self.prefix = config.get('prefix', '')
        self.passive = config.get('passive', True)
        self.timeout = config.get('timeout', 30)
        self.use_tls = config.get('use_tls', False)
        self.encoding = config.get('encoding', 'utf-8')
        
        # Normalize prefix
        if self.prefix and not self.prefix.startswith('/'):
            self.prefix = '/' + self.prefix
        if self.prefix and self.prefix.endswith('/'):
            self.prefix = self.prefix.rstrip('/')
    
    def _get_connection(self) -> ftplib.FTP:
        """Create and return an FTP connection.
        
        Returns:
            Connected FTP object
        """
        if self.use_tls:
            ftp = ftplib.FTP_TLS(timeout=self.timeout)
        else:
            ftp = ftplib.FTP(timeout=self.timeout)
        
        ftp.encoding = self.encoding
        
        try:
            ftp.connect(self.host, self.port)
            ftp.login(self.username, self.password)
            
            if self.use_tls:
                ftp.prot_p()  # Enable data connection security
            
            if self.passive:
                ftp.set_pasv(True)
            else:
                ftp.set_pasv(False)
            
            return ftp
        except Exception as e:
            print(f"FTP connection error: {e}")
            raise
    
    def _get_document_path(self, document_id: str) -> str:
        """Build the full FTP path for a document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Full FTP path
        """
        # Add .pdf extension if not present
        if not document_id.lower().endswith('.pdf'):
            document_id = f"{document_id}.pdf"
        
        # Build path with prefix
        if self.prefix:
            return f"{self.prefix}/{document_id}"
        return f"/{document_id}" if not document_id.startswith('/') else document_id
    
    def get_document(self, document_id: str) -> Optional[bytes]:
        """Retrieve a PDF document from the FTP server.
        
        Args:
            document_id: The document identifier
            
        Returns:
            PDF bytes if found, None otherwise
        """
        path = self._get_document_path(document_id)
        
        try:
            ftp = self._get_connection()
            
            try:
                # Create a BytesIO buffer to store the file
                buffer = io.BytesIO()
                
                # Download the file
                ftp.retrbinary(f'RETR {path}', buffer.write)
                
                content = buffer.getvalue()
                buffer.close()
                
                # Verify it's a PDF
                if content[:4] == b'%PDF':
                    return content
                else:
                    print(f"Warning: File {document_id} may not be a valid PDF")
                    return content
                    
            finally:
                ftp.quit()
                
        except ftplib.error_perm as e:
            error_code = str(e).split()[0] if str(e) else ''
            if error_code in ('550', '553'):
                print(f"Document not found on FTP: {document_id}")
            else:
                print(f"FTP permission error fetching {document_id}: {e}")
            return None
        except ftplib.error_temp as e:
            print(f"FTP temporary error fetching {document_id}: {e}")
            return None
        except (ConnectionError, TimeoutError) as e:
            print(f"FTP connection error fetching {document_id}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching {document_id} from FTP: {e}")
            return None
    
    def document_exists(self, document_id: str) -> bool:
        """Check if a document exists on the FTP server.
        
        Args:
            document_id: The document identifier
            
        Returns:
            True if document exists, False otherwise
        """
        path = self._get_document_path(document_id)
        
        try:
            ftp = self._get_connection()
            
            try:
                # Try to get file size (will fail if file doesn't exist)
                ftp.size(path)
                return True
            except ftplib.error_perm:
                # File doesn't exist or no permission
                # Try alternative method using MLST or directory listing
                try:
                    directory = '/'.join(path.split('/')[:-1]) or '/'
                    filename = path.split('/')[-1]
                    
                    files = ftp.nlst(directory)
                    # Check if file is in the listing
                    for f in files:
                        if f.endswith(filename) or f == filename:
                            return True
                    return False
                except:
                    return False
            finally:
                ftp.quit()
                
        except Exception as e:
            print(f"Error checking document existence on FTP: {e}")
            return False
    
    def list_documents(self, subdirectory: str = "", max_results: int = 100) -> List[str]:
        """List PDF documents in an FTP directory.
        
        Args:
            subdirectory: Subdirectory to list (optional)
            max_results: Maximum number of documents to return
            
        Returns:
            List of document IDs (filenames without .pdf extension)
        """
        if subdirectory:
            if self.prefix:
                path = f"{self.prefix}/{subdirectory}"
            else:
                path = f"/{subdirectory}" if not subdirectory.startswith('/') else subdirectory
        else:
            path = self.prefix or '/'
        
        documents = []
        
        try:
            ftp = self._get_connection()
            
            try:
                # Get list of files
                files = ftp.nlst(path)
                
                for filepath in files:
                    if len(documents) >= max_results:
                        break
                    
                    # Get filename from path
                    filename = filepath.split('/')[-1] if '/' in filepath else filepath
                    
                    # Only include PDF files
                    if filename.lower().endswith('.pdf'):
                        # Remove .pdf extension
                        doc_id = filename[:-4]
                        documents.append(doc_id)
                
            finally:
                ftp.quit()
                
        except ftplib.error_perm as e:
            print(f"FTP permission error listing directory: {e}")
        except Exception as e:
            print(f"Error listing FTP documents: {e}")
        
        return documents
    
    def get_document_metadata(self, document_id: str) -> Optional[dict]:
        """Get metadata for a document on the FTP server.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Dict with document metadata, or None if not found
        """
        path = self._get_document_path(document_id)
        
        try:
            ftp = self._get_connection()
            
            try:
                metadata = {
                    'document_id': document_id,
                    'ftp_path': path,
                    'host': self.host
                }
                
                # Try to get file size
                try:
                    size = ftp.size(path)
                    if size is not None:
                        metadata['size'] = size
                except:
                    pass
                
                # Try to get modification time
                try:
                    mdtm_response = ftp.sendcmd(f'MDTM {path}')
                    if mdtm_response.startswith('213'):
                        # Parse timestamp: 213 YYYYMMDDhhmmss
                        timestamp = mdtm_response[4:].strip()
                        metadata['modified_time'] = timestamp
                except:
                    pass
                
                return metadata
                
            finally:
                ftp.quit()
                
        except ftplib.error_perm:
            return None
        except Exception as e:
            print(f"Error getting FTP document metadata: {e}")
            return None
    
    def test_connection(self) -> dict:
        """Test the FTP connection and authentication.
        
        Returns:
            Dict with connection status and server information
        """
        try:
            ftp = self._get_connection()
            
            try:
                # Get server welcome message
                welcome = ftp.getwelcome()
                
                # Try to get current directory
                current_dir = ftp.pwd()
                
                # Try to get system type
                try:
                    system_type = ftp.sendcmd('SYST')
                except:
                    system_type = 'Unknown'
                
                # Check if prefix directory exists
                prefix_exists = True
                if self.prefix:
                    try:
                        ftp.cwd(self.prefix)
                    except ftplib.error_perm:
                        prefix_exists = False
                
                return {
                    'success': True,
                    'host': self.host,
                    'port': self.port,
                    'welcome': welcome,
                    'current_directory': current_dir,
                    'system': system_type,
                    'tls_enabled': self.use_tls,
                    'passive_mode': self.passive,
                    'prefix_exists': prefix_exists
                }
                
            finally:
                ftp.quit()
                
        except ftplib.error_perm as e:
            return {
                'success': False,
                'error': f'Permission denied: {e}',
                'host': self.host
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'host': self.host
            }
    
    def upload_document(self, document_id: str, content: bytes) -> bool:
        """Upload a PDF document to the FTP server (optional feature).
        
        Args:
            document_id: The document identifier
            content: PDF content as bytes
            
        Returns:
            True if upload successful, False otherwise
        """
        path = self._get_document_path(document_id)
        
        try:
            ftp = self._get_connection()
            
            try:
                # Create directory if needed
                if self.prefix:
                    try:
                        ftp.mkd(self.prefix)
                    except ftplib.error_perm:
                        pass  # Directory probably exists
                
                # Upload the file
                buffer = io.BytesIO(content)
                ftp.storbinary(f'STOR {path}', buffer)
                buffer.close()
                
                return True
                
            finally:
                ftp.quit()
                
        except ftplib.error_perm as e:
            print(f"FTP permission error uploading {document_id}: {e}")
            return False
        except Exception as e:
            print(f"Error uploading {document_id} to FTP: {e}")
            return False
