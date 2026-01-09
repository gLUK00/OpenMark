"""SFTP-based PDF source plugin (SSH File Transfer Protocol)."""

import io
import stat
from typing import Optional, List

from app.plugins.base import PDFSourcePlugin


class SFTPSourcePlugin(PDFSourcePlugin):
    """PDF source plugin that retrieves documents from an SFTP server via SSH."""
    
    def __init__(self, config: dict):
        """Initialize the SFTP source plugin.
        
        Args:
            config: Plugin configuration with SFTP settings:
                - host: SFTP server hostname or IP (required)
                - port: SSH port (default: 22)
                - username: SSH username (required)
                - password: SSH password (optional if using key auth)
                - private_key_path: Path to private key file (optional)
                - private_key_passphrase: Passphrase for private key (optional)
                - prefix: Directory path prefix for documents (optional, e.g., '/documents/pdfs')
                - timeout: Connection timeout in seconds (default: 30)
                - known_hosts_path: Path to known_hosts file (optional)
                - auto_add_host_key: Auto-add unknown host keys (default: False, set True only for dev)
                - compress: Enable SSH compression (default: False)
        """
        super().__init__(config)
        self.host = config.get('host')
        if not self.host:
            raise ValueError("SFTP plugin requires 'host' in configuration")
        
        self.port = config.get('port', 22)
        self.username = config.get('username')
        if not self.username:
            raise ValueError("SFTP plugin requires 'username' in configuration")
        
        self.password = config.get('password')
        self.private_key_path = config.get('private_key_path')
        self.private_key_passphrase = config.get('private_key_passphrase')
        self.prefix = config.get('prefix', '')
        self.timeout = config.get('timeout', 30)
        self.known_hosts_path = config.get('known_hosts_path')
        self.auto_add_host_key = config.get('auto_add_host_key', False)
        self.compress = config.get('compress', False)
        
        # Normalize prefix
        if self.prefix and not self.prefix.startswith('/'):
            self.prefix = '/' + self.prefix
        if self.prefix and self.prefix.endswith('/'):
            self.prefix = self.prefix.rstrip('/')
        
        # Lazy initialization
        self._client = None
        self._sftp = None
    
    def _get_connection(self):
        """Create and return an SFTP connection.
        
        Returns:
            Tuple of (SSHClient, SFTPClient)
        """
        try:
            import paramiko
        except ImportError:
            raise ImportError(
                "paramiko is required for SFTP PDF source plugin. "
                "Install it with: pip install paramiko"
            )
        
        client = paramiko.SSHClient()
        
        # Handle host key verification
        if self.known_hosts_path:
            try:
                client.load_host_keys(self.known_hosts_path)
            except Exception as e:
                print(f"Warning: Could not load known_hosts: {e}")
        
        if self.auto_add_host_key:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        else:
            # Use RejectPolicy by default for security
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        
        # Load system host keys
        try:
            client.load_system_host_keys()
        except:
            pass
        
        # Prepare connection parameters
        connect_kwargs = {
            'hostname': self.host,
            'port': self.port,
            'username': self.username,
            'timeout': self.timeout,
            'compress': self.compress
        }
        
        # Authentication: private key or password
        if self.private_key_path:
            try:
                # Try to load the private key
                key = None
                key_types = [
                    paramiko.RSAKey,
                    paramiko.Ed25519Key,
                    paramiko.ECDSAKey,
                    paramiko.DSSKey
                ]
                
                for key_class in key_types:
                    try:
                        if self.private_key_passphrase:
                            key = key_class.from_private_key_file(
                                self.private_key_path,
                                password=self.private_key_passphrase
                            )
                        else:
                            key = key_class.from_private_key_file(self.private_key_path)
                        break
                    except paramiko.SSHException:
                        continue
                
                if key:
                    connect_kwargs['pkey'] = key
                else:
                    raise ValueError(f"Could not load private key from {self.private_key_path}")
                    
            except Exception as e:
                raise ValueError(f"Error loading private key: {e}")
        
        if self.password:
            connect_kwargs['password'] = self.password
        
        try:
            client.connect(**connect_kwargs)
            sftp = client.open_sftp()
            return client, sftp
        except Exception as e:
            client.close()
            raise
    
    def _close_connection(self, client, sftp):
        """Close SFTP and SSH connections.
        
        Args:
            client: SSHClient instance
            sftp: SFTPClient instance
        """
        try:
            if sftp:
                sftp.close()
            if client:
                client.close()
        except:
            pass
    
    def _get_document_path(self, document_id: str) -> str:
        """Build the full SFTP path for a document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Full SFTP path
        """
        # Add .pdf extension if not present
        if not document_id.lower().endswith('.pdf'):
            document_id = f"{document_id}.pdf"
        
        # Build path with prefix
        if self.prefix:
            return f"{self.prefix}/{document_id}"
        return f"/{document_id}" if not document_id.startswith('/') else document_id
    
    def get_document(self, document_id: str) -> Optional[bytes]:
        """Retrieve a PDF document from the SFTP server.
        
        Args:
            document_id: The document identifier
            
        Returns:
            PDF bytes if found, None otherwise
        """
        path = self._get_document_path(document_id)
        client = None
        sftp = None
        
        try:
            client, sftp = self._get_connection()
            
            # Create a BytesIO buffer to store the file
            buffer = io.BytesIO()
            
            # Download the file
            sftp.getfo(path, buffer)
            
            content = buffer.getvalue()
            buffer.close()
            
            # Verify it's a PDF
            if content[:4] == b'%PDF':
                return content
            else:
                print(f"Warning: File {document_id} may not be a valid PDF")
                return content
                
        except FileNotFoundError:
            print(f"Document not found on SFTP: {document_id}")
            return None
        except PermissionError:
            print(f"Permission denied accessing {document_id} on SFTP")
            return None
        except Exception as e:
            print(f"Error fetching {document_id} from SFTP: {e}")
            return None
        finally:
            self._close_connection(client, sftp)
    
    def document_exists(self, document_id: str) -> bool:
        """Check if a document exists on the SFTP server.
        
        Args:
            document_id: The document identifier
            
        Returns:
            True if document exists, False otherwise
        """
        path = self._get_document_path(document_id)
        client = None
        sftp = None
        
        try:
            client, sftp = self._get_connection()
            
            # Try to stat the file
            sftp.stat(path)
            return True
            
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f"Error checking document existence on SFTP: {e}")
            return False
        finally:
            self._close_connection(client, sftp)
    
    def list_documents(self, subdirectory: str = "", max_results: int = 100) -> List[str]:
        """List PDF documents in an SFTP directory.
        
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
        client = None
        sftp = None
        
        try:
            client, sftp = self._get_connection()
            
            # Get list of files with attributes
            for entry in sftp.listdir_attr(path):
                if len(documents) >= max_results:
                    break
                
                # Only include regular files (not directories)
                if stat.S_ISREG(entry.st_mode):
                    filename = entry.filename
                    
                    # Only include PDF files
                    if filename.lower().endswith('.pdf'):
                        # Remove .pdf extension
                        doc_id = filename[:-4]
                        documents.append(doc_id)
            
        except FileNotFoundError:
            print(f"Directory not found on SFTP: {path}")
        except Exception as e:
            print(f"Error listing SFTP documents: {e}")
        finally:
            self._close_connection(client, sftp)
        
        return documents
    
    def get_document_metadata(self, document_id: str) -> Optional[dict]:
        """Get metadata for a document on the SFTP server.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Dict with document metadata, or None if not found
        """
        path = self._get_document_path(document_id)
        client = None
        sftp = None
        
        try:
            client, sftp = self._get_connection()
            
            # Get file attributes
            attrs = sftp.stat(path)
            
            metadata = {
                'document_id': document_id,
                'sftp_path': path,
                'host': self.host,
                'size': attrs.st_size,
                'uid': attrs.st_uid,
                'gid': attrs.st_gid,
                'mode': oct(attrs.st_mode),
                'atime': attrs.st_atime,
                'mtime': attrs.st_mtime
            }
            
            return metadata
            
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"Error getting SFTP document metadata: {e}")
            return None
        finally:
            self._close_connection(client, sftp)
    
    def test_connection(self) -> dict:
        """Test the SFTP connection and authentication.
        
        Returns:
            Dict with connection status and server information
        """
        client = None
        sftp = None
        
        try:
            import paramiko
        except ImportError:
            return {
                'success': False,
                'error': 'paramiko library not installed'
            }
        
        try:
            client, sftp = self._get_connection()
            
            # Get current directory
            current_dir = sftp.getcwd() or sftp.normalize('.')
            
            # Check if prefix directory exists
            prefix_exists = True
            if self.prefix:
                try:
                    sftp.stat(self.prefix)
                except FileNotFoundError:
                    prefix_exists = False
            
            # Get server banner
            transport = client.get_transport()
            server_banner = transport.remote_version if transport else 'Unknown'
            
            return {
                'success': True,
                'host': self.host,
                'port': self.port,
                'username': self.username,
                'current_directory': current_dir,
                'server_banner': server_banner,
                'prefix_exists': prefix_exists,
                'auth_method': 'key' if self.private_key_path else 'password'
            }
            
        except paramiko.AuthenticationException as e:
            return {
                'success': False,
                'error': f'Authentication failed: {e}',
                'host': self.host
            }
        except paramiko.SSHException as e:
            return {
                'success': False,
                'error': f'SSH error: {e}',
                'host': self.host
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'host': self.host
            }
        finally:
            self._close_connection(client, sftp)
    
    def upload_document(self, document_id: str, content: bytes) -> bool:
        """Upload a PDF document to the SFTP server (optional feature).
        
        Args:
            document_id: The document identifier
            content: PDF content as bytes
            
        Returns:
            True if upload successful, False otherwise
        """
        path = self._get_document_path(document_id)
        client = None
        sftp = None
        
        try:
            client, sftp = self._get_connection()
            
            # Create directory if needed
            if self.prefix:
                try:
                    sftp.mkdir(self.prefix)
                except IOError:
                    pass  # Directory probably exists
            
            # Upload the file
            buffer = io.BytesIO(content)
            sftp.putfo(buffer, path)
            buffer.close()
            
            return True
            
        except PermissionError:
            print(f"Permission denied uploading {document_id} to SFTP")
            return False
        except Exception as e:
            print(f"Error uploading {document_id} to SFTP: {e}")
            return False
        finally:
            self._close_connection(client, sftp)
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a PDF document from the SFTP server (optional feature).
        
        Args:
            document_id: The document identifier
            
        Returns:
            True if deletion successful, False otherwise
        """
        path = self._get_document_path(document_id)
        client = None
        sftp = None
        
        try:
            client, sftp = self._get_connection()
            
            sftp.remove(path)
            return True
            
        except FileNotFoundError:
            print(f"Document not found on SFTP: {document_id}")
            return False
        except PermissionError:
            print(f"Permission denied deleting {document_id} from SFTP")
            return False
        except Exception as e:
            print(f"Error deleting {document_id} from SFTP: {e}")
            return False
        finally:
            self._close_connection(client, sftp)
