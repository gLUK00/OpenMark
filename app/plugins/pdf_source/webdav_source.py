"""WebDAV-based PDF source plugin."""

from typing import Optional, List
from urllib.parse import urljoin, quote

from app.plugins.base import PDFSourcePlugin


class WebDAVSourcePlugin(PDFSourcePlugin):
    """PDF source plugin that retrieves documents from a WebDAV server."""
    
    def __init__(self, config: dict):
        """Initialize the WebDAV source plugin.
        
        Args:
            config: Plugin configuration with WebDAV settings:
                - base_url: WebDAV server URL (required, e.g., 'https://webdav.example.com/documents/')
                - username: Username for authentication (optional)
                - password: Password for authentication (optional)
                - prefix: Path prefix for documents (optional, e.g., 'pdfs/')
                - timeout: Request timeout in seconds (default: 30)
                - verify_ssl: Verify SSL certificates (default: True)
                - auth_type: Authentication type: 'basic', 'digest' (default: 'basic')
        """
        super().__init__(config)
        self.base_url = config.get('base_url')
        if not self.base_url:
            raise ValueError("WebDAV plugin requires 'base_url' in configuration")
        
        # Ensure base_url ends with /
        if not self.base_url.endswith('/'):
            self.base_url += '/'
        
        self.username = config.get('username')
        self.password = config.get('password')
        self.prefix = config.get('prefix', '')
        self.timeout = config.get('timeout', 30)
        self.verify_ssl = config.get('verify_ssl', True)
        self.auth_type = config.get('auth_type', 'basic').lower()
        
        # Lazy initialization
        self._session = None
    
    @property
    def session(self):
        """Get or create the requests session (lazy initialization).
        
        Returns:
            requests.Session with authentication configured
        """
        if self._session is None:
            try:
                import requests
                from requests.auth import HTTPBasicAuth, HTTPDigestAuth
            except ImportError:
                raise ImportError(
                    "requests is required for WebDAV PDF source plugin. "
                    "Install it with: pip install requests"
                )
            
            self._session = requests.Session()
            self._session.verify = self.verify_ssl
            
            # Configure authentication
            if self.username and self.password:
                if self.auth_type == 'digest':
                    self._session.auth = HTTPDigestAuth(self.username, self.password)
                else:
                    self._session.auth = HTTPBasicAuth(self.username, self.password)
        
        return self._session
    
    def _get_document_url(self, document_id: str) -> str:
        """Build the full WebDAV URL for a document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Full WebDAV URL
        """
        # Add .pdf extension if not present
        if not document_id.lower().endswith('.pdf'):
            document_id = f"{document_id}.pdf"
        
        # Build path with prefix
        if self.prefix:
            prefix = self.prefix.rstrip('/')
            path = f"{prefix}/{document_id}"
        else:
            path = document_id
        
        # URL encode the path (but preserve slashes)
        path_parts = path.split('/')
        encoded_parts = [quote(part, safe='') for part in path_parts]
        encoded_path = '/'.join(encoded_parts)
        
        return urljoin(self.base_url, encoded_path)
    
    def get_document(self, document_id: str) -> Optional[bytes]:
        """Retrieve a PDF document from the WebDAV server.
        
        Args:
            document_id: The document identifier
            
        Returns:
            PDF bytes if found, None otherwise
        """
        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests is required for WebDAV PDF source plugin. "
                "Install it with: pip install requests"
            )
        
        url = self._get_document_url(document_id)
        
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                content = response.content
                
                # Verify it's a PDF
                content_type = response.headers.get('Content-Type', '')
                if 'pdf' in content_type.lower() or content[:4] == b'%PDF':
                    return content
                else:
                    print(f"Warning: Content-Type '{content_type}' may not be a PDF for {document_id}")
                    return content
            
            elif response.status_code == 404:
                print(f"Document not found on WebDAV: {document_id}")
                return None
            elif response.status_code == 401:
                print(f"Authentication failed for WebDAV: {url}")
                return None
            elif response.status_code == 403:
                print(f"Access denied to WebDAV resource: {url}")
                return None
            else:
                print(f"WebDAV error {response.status_code} fetching document {document_id}")
                return None
                
        except requests.Timeout:
            print(f"Timeout fetching document {document_id} from WebDAV")
            return None
        except requests.ConnectionError as e:
            print(f"Connection error fetching document {document_id} from WebDAV: {e}")
            return None
        except requests.RequestException as e:
            print(f"Request error fetching document {document_id} from WebDAV: {e}")
            return None
    
    def document_exists(self, document_id: str) -> bool:
        """Check if a document exists on the WebDAV server using HEAD request.
        
        Args:
            document_id: The document identifier
            
        Returns:
            True if document exists, False otherwise
        """
        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests is required for WebDAV PDF source plugin. "
                "Install it with: pip install requests"
            )
        
        url = self._get_document_url(document_id)
        
        try:
            response = self.session.head(
                url,
                timeout=self.timeout,
                allow_redirects=True
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def list_documents(self, path: str = "", max_results: int = 100) -> List[str]:
        """List documents in a WebDAV directory using PROPFIND.
        
        Args:
            path: Subdirectory path to list (optional)
            max_results: Maximum number of documents to return
            
        Returns:
            List of document IDs (filenames without .pdf extension)
        """
        try:
            import requests
            import xml.etree.ElementTree as ET
        except ImportError:
            raise ImportError(
                "requests is required for WebDAV PDF source plugin. "
                "Install it with: pip install requests"
            )
        
        # Build URL for listing
        if path:
            list_url = urljoin(self.base_url, f"{self.prefix.rstrip('/')}/{path}/")
        else:
            list_url = urljoin(self.base_url, self.prefix) if self.prefix else self.base_url
        
        # Ensure URL ends with /
        if not list_url.endswith('/'):
            list_url += '/'
        
        # PROPFIND request body
        propfind_body = '''<?xml version="1.0" encoding="utf-8"?>
<D:propfind xmlns:D="DAV:">
    <D:prop>
        <D:displayname/>
        <D:getcontenttype/>
        <D:resourcetype/>
    </D:prop>
</D:propfind>'''
        
        documents = []
        
        try:
            response = self.session.request(
                'PROPFIND',
                list_url,
                data=propfind_body,
                headers={
                    'Content-Type': 'application/xml',
                    'Depth': '1'  # Only immediate children
                },
                timeout=self.timeout
            )
            
            if response.status_code in (200, 207):  # 207 Multi-Status is WebDAV success
                # Parse XML response
                root = ET.fromstring(response.content)
                
                # DAV namespace
                namespaces = {'D': 'DAV:'}
                
                for response_elem in root.findall('.//D:response', namespaces):
                    href = response_elem.find('D:href', namespaces)
                    if href is not None:
                        href_text = href.text
                        
                        # Skip the directory itself
                        if href_text.rstrip('/') == list_url.rstrip('/'):
                            continue
                        
                        # Check if it's a PDF file
                        if href_text.lower().endswith('.pdf'):
                            # Extract filename
                            filename = href_text.rstrip('/').split('/')[-1]
                            # Remove .pdf extension
                            doc_id = filename[:-4] if filename.lower().endswith('.pdf') else filename
                            documents.append(doc_id)
                            
                            if len(documents) >= max_results:
                                break
            else:
                print(f"WebDAV PROPFIND failed with status {response.status_code}")
                
        except requests.RequestException as e:
            print(f"Error listing WebDAV documents: {e}")
        except ET.ParseError as e:
            print(f"Error parsing WebDAV response: {e}")
        
        return documents
    
    def get_document_metadata(self, document_id: str) -> Optional[dict]:
        """Get metadata for a document on the WebDAV server.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Dict with document metadata, or None if not found
        """
        try:
            import requests
            import xml.etree.ElementTree as ET
        except ImportError:
            raise ImportError(
                "requests is required for WebDAV PDF source plugin. "
                "Install it with: pip install requests"
            )
        
        url = self._get_document_url(document_id)
        
        # PROPFIND request body for metadata
        propfind_body = '''<?xml version="1.0" encoding="utf-8"?>
<D:propfind xmlns:D="DAV:">
    <D:prop>
        <D:displayname/>
        <D:getcontenttype/>
        <D:getcontentlength/>
        <D:getlastmodified/>
        <D:getetag/>
        <D:creationdate/>
    </D:prop>
</D:propfind>'''
        
        try:
            response = self.session.request(
                'PROPFIND',
                url,
                data=propfind_body,
                headers={
                    'Content-Type': 'application/xml',
                    'Depth': '0'
                },
                timeout=self.timeout
            )
            
            if response.status_code in (200, 207):
                root = ET.fromstring(response.content)
                namespaces = {'D': 'DAV:'}
                
                props = root.find('.//D:prop', namespaces)
                if props is not None:
                    metadata = {
                        'document_id': document_id,
                        'url': url
                    }
                    
                    # Extract properties
                    displayname = props.find('D:displayname', namespaces)
                    if displayname is not None and displayname.text:
                        metadata['displayname'] = displayname.text
                    
                    content_type = props.find('D:getcontenttype', namespaces)
                    if content_type is not None and content_type.text:
                        metadata['content_type'] = content_type.text
                    
                    content_length = props.find('D:getcontentlength', namespaces)
                    if content_length is not None and content_length.text:
                        metadata['content_length'] = int(content_length.text)
                    
                    last_modified = props.find('D:getlastmodified', namespaces)
                    if last_modified is not None and last_modified.text:
                        metadata['last_modified'] = last_modified.text
                    
                    etag = props.find('D:getetag', namespaces)
                    if etag is not None and etag.text:
                        metadata['etag'] = etag.text.strip('"')
                    
                    creation_date = props.find('D:creationdate', namespaces)
                    if creation_date is not None and creation_date.text:
                        metadata['creation_date'] = creation_date.text
                    
                    return metadata
            
            elif response.status_code == 404:
                return None
            else:
                print(f"WebDAV PROPFIND failed with status {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"Error getting WebDAV document metadata: {e}")
            return None
        except ET.ParseError as e:
            print(f"Error parsing WebDAV metadata response: {e}")
            return None
    
    def test_connection(self) -> dict:
        """Test the WebDAV connection and authentication.
        
        Returns:
            Dict with connection status and server information
        """
        try:
            import requests
        except ImportError:
            return {
                'success': False,
                'error': 'requests library not installed'
            }
        
        try:
            # Try OPTIONS request to test connection
            response = self.session.options(
                self.base_url,
                timeout=self.timeout
            )
            
            dav_header = response.headers.get('DAV', '')
            allow_header = response.headers.get('Allow', '')
            
            return {
                'success': response.status_code in (200, 204),
                'status_code': response.status_code,
                'base_url': self.base_url,
                'dav_compliance': dav_header,
                'allowed_methods': allow_header,
                'server': response.headers.get('Server', 'Unknown')
            }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'base_url': self.base_url
            }
