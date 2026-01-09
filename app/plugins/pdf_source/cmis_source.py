"""CMIS-based PDF source plugin (Content Management Interoperability Services).

Supports ECM systems like Alfresco, Nuxeo, SharePoint, OpenText, IBM FileNet, etc.
"""

import base64
from typing import Optional, List
from urllib.parse import urljoin, quote

from app.plugins.base import PDFSourcePlugin


class CMISSourcePlugin(PDFSourcePlugin):
    """PDF source plugin that retrieves documents from CMIS-compliant ECM systems.
    
    CMIS (Content Management Interoperability Services) is an OASIS standard
    that enables interoperability between Enterprise Content Management systems.
    
    Supported ECM systems:
    - Alfresco
    - Nuxeo
    - Microsoft SharePoint
    - OpenText
    - IBM FileNet
    - SAP Document Management
    - And any other CMIS 1.0/1.1 compliant system
    """
    
    def __init__(self, config: dict):
        """Initialize the CMIS source plugin.
        
        Args:
            config: Plugin configuration with CMIS settings:
                - url: CMIS service URL (required)
                - binding: CMIS binding type: 'atompub' or 'browser' (default: 'browser')
                - repository_id: Repository ID (optional, uses first if not specified)
                - username: Authentication username (required)
                - password: Authentication password (required)
                - root_folder_path: Root folder path for documents (optional, e.g., '/Sites/docs')
                - timeout: Request timeout in seconds (default: 30)
                - verify_ssl: Verify SSL certificates (default: True)
                - query_type: How to find documents: 'path', 'id', or 'query' (default: 'path')
        """
        super().__init__(config)
        self.url = config.get('url')
        if not self.url:
            raise ValueError("CMIS plugin requires 'url' in configuration")
        
        # Normalize URL
        if not self.url.endswith('/'):
            self.url = self.url + '/'
        
        self.binding = config.get('binding', 'browser').lower()
        if self.binding not in ('atompub', 'browser'):
            raise ValueError("CMIS binding must be 'atompub' or 'browser'")
        
        self.repository_id = config.get('repository_id')
        self.username = config.get('username')
        self.password = config.get('password')
        
        if not self.username or not self.password:
            raise ValueError("CMIS plugin requires 'username' and 'password' in configuration")
        
        self.root_folder_path = config.get('root_folder_path', '')
        if self.root_folder_path and not self.root_folder_path.startswith('/'):
            self.root_folder_path = '/' + self.root_folder_path
        if self.root_folder_path and self.root_folder_path.endswith('/'):
            self.root_folder_path = self.root_folder_path.rstrip('/')
        
        self.timeout = config.get('timeout', 30)
        self.verify_ssl = config.get('verify_ssl', True)
        self.query_type = config.get('query_type', 'path')
        
        # Lazy initialization
        self._session = None
        self._repository_info = None
    
    def _get_session(self):
        """Get or create an HTTP session with authentication.
        
        Returns:
            requests.Session configured for CMIS
        """
        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests is required for CMIS PDF source plugin. "
                "Install it with: pip install requests"
            )
        
        if self._session is None:
            self._session = requests.Session()
            self._session.auth = (self.username, self.password)
            self._session.verify = self.verify_ssl
            self._session.timeout = self.timeout
            self._session.headers.update({
                'Accept': 'application/json',
                'User-Agent': 'OpenMark-CMIS-Plugin/1.0'
            })
        
        return self._session
    
    def _get_repository_info(self) -> dict:
        """Get CMIS repository information.
        
        Returns:
            Repository information dict
        """
        if self._repository_info:
            return self._repository_info
        
        session = self._get_session()
        
        if self.binding == 'browser':
            # CMIS Browser Binding
            response = session.get(self.url, timeout=self.timeout)
            response.raise_for_status()
            repos = response.json()
            
            if self.repository_id:
                if self.repository_id in repos:
                    self._repository_info = repos[self.repository_id]
                else:
                    raise ValueError(f"Repository '{self.repository_id}' not found")
            else:
                # Use first repository
                first_repo_id = list(repos.keys())[0]
                self._repository_info = repos[first_repo_id]
                self.repository_id = first_repo_id
        else:
            # CMIS AtomPub Binding
            response = session.get(self.url, timeout=self.timeout)
            response.raise_for_status()
            # Parse AtomPub service document (simplified)
            self._repository_info = {'repositoryId': self.repository_id or 'default'}
        
        return self._repository_info
    
    def _get_root_folder_url(self) -> str:
        """Get the URL for the root folder.
        
        Returns:
            Root folder URL for CMIS operations
        """
        repo_info = self._get_repository_info()
        
        if self.binding == 'browser':
            return repo_info.get('rootFolderUrl', f"{self.url}{self.repository_id}/root")
        else:
            return f"{self.url}atom/{self.repository_id}/content"
    
    def _get_document_path(self, document_id: str) -> str:
        """Build the full CMIS path for a document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Full CMIS path
        """
        # Add .pdf extension if not present
        if not document_id.lower().endswith('.pdf'):
            document_id = f"{document_id}.pdf"
        
        # Build path with root folder
        if self.root_folder_path:
            return f"{self.root_folder_path}/{document_id}"
        return f"/{document_id}" if not document_id.startswith('/') else document_id
    
    def _get_object_by_path(self, path: str) -> Optional[dict]:
        """Get a CMIS object by its path.
        
        Args:
            path: Document path in repository
            
        Returns:
            CMIS object properties dict or None
        """
        session = self._get_session()
        root_url = self._get_root_folder_url()
        
        if self.binding == 'browser':
            # Browser binding - use cmisselector=object
            # Path needs to be relative to root
            if path.startswith('/'):
                path = path[1:]
            
            url = f"{root_url}/{quote(path, safe='/')}?cmisselector=object"
            
            try:
                response = session.get(url, timeout=self.timeout)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error getting CMIS object by path: {e}")
                return None
        else:
            # AtomPub binding
            url = f"{self.url}atom/{self.repository_id}/path{quote(path, safe='/')}"
            
            try:
                response = session.get(url, timeout=self.timeout)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                # Parse Atom entry (simplified - would need proper XML parsing)
                return {'path': path}
            except Exception as e:
                print(f"Error getting CMIS object by path: {e}")
                return None
    
    def _get_object_by_id(self, object_id: str) -> Optional[dict]:
        """Get a CMIS object by its ID.
        
        Args:
            object_id: CMIS object ID
            
        Returns:
            CMIS object properties dict or None
        """
        session = self._get_session()
        self._get_repository_info()  # Ensure we have repo info
        
        if self.binding == 'browser':
            url = f"{self.url}{self.repository_id}/root?objectId={quote(object_id)}&cmisselector=object"
            
            try:
                response = session.get(url, timeout=self.timeout)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
            except Exception as e:
                print(f"Error getting CMIS object by ID: {e}")
                return None
        else:
            url = f"{self.url}atom/{self.repository_id}/id?id={quote(object_id)}"
            
            try:
                response = session.get(url, timeout=self.timeout)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return {'objectId': object_id}
            except Exception as e:
                print(f"Error getting CMIS object by ID: {e}")
                return None
    
    def _query_for_document(self, document_id: str) -> Optional[dict]:
        """Find a document using CMIS Query Language.
        
        Args:
            document_id: Document name or identifier
            
        Returns:
            First matching document or None
        """
        session = self._get_session()
        self._get_repository_info()
        
        # Add .pdf extension if not present
        if not document_id.lower().endswith('.pdf'):
            doc_name = f"{document_id}.pdf"
        else:
            doc_name = document_id
        
        # CMIS SQL query
        query = f"SELECT * FROM cmis:document WHERE cmis:name = '{doc_name}'"
        
        if self.binding == 'browser':
            url = f"{self.url}{self.repository_id}?cmisselector=query&q={quote(query)}"
            
            try:
                response = session.get(url, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                
                if result.get('results') and len(result['results']) > 0:
                    return result['results'][0]
                return None
            except Exception as e:
                print(f"Error querying CMIS: {e}")
                return None
        else:
            # AtomPub query endpoint
            url = f"{self.url}atom/{self.repository_id}/query"
            
            try:
                response = session.post(
                    url,
                    data={'q': query},
                    timeout=self.timeout
                )
                response.raise_for_status()
                # Would need XML parsing for proper AtomPub response
                return None
            except Exception as e:
                print(f"Error querying CMIS: {e}")
                return None
    
    def _download_content(self, obj: dict) -> Optional[bytes]:
        """Download the content stream of a CMIS object.
        
        Args:
            obj: CMIS object dict with properties
            
        Returns:
            Document content as bytes or None
        """
        session = self._get_session()
        
        # Get content stream URL
        content_url = None
        
        if self.binding == 'browser':
            # Extract object ID from properties
            if 'succinctProperties' in obj:
                object_id = obj['succinctProperties'].get('cmis:objectId')
            elif 'properties' in obj:
                object_id = obj['properties'].get('cmis:objectId', {}).get('value')
            else:
                object_id = obj.get('objectId')
            
            if object_id:
                content_url = f"{self.url}{self.repository_id}/root?objectId={quote(object_id)}&cmisselector=content"
        else:
            # AtomPub - content URL from link
            content_url = obj.get('contentUrl')
        
        if not content_url:
            print("Could not determine content URL for CMIS object")
            return None
        
        try:
            response = session.get(
                content_url, 
                timeout=self.timeout,
                headers={'Accept': 'application/pdf'}
            )
            response.raise_for_status()
            
            content = response.content
            
            # Verify it's a PDF
            if content[:4] == b'%PDF':
                return content
            else:
                print("Warning: Downloaded content may not be a valid PDF")
                return content
                
        except Exception as e:
            print(f"Error downloading CMIS content: {e}")
            return None
    
    def get_document(self, document_id: str) -> Optional[bytes]:
        """Retrieve a PDF document from the CMIS repository.
        
        Args:
            document_id: The document identifier (path, ID, or name depending on query_type)
            
        Returns:
            PDF bytes if found, None otherwise
        """
        try:
            obj = None
            
            if self.query_type == 'id':
                obj = self._get_object_by_id(document_id)
            elif self.query_type == 'query':
                obj = self._query_for_document(document_id)
            else:  # path (default)
                path = self._get_document_path(document_id)
                obj = self._get_object_by_path(path)
            
            if obj:
                return self._download_content(obj)
            
            return None
            
        except Exception as e:
            print(f"Error fetching {document_id} from CMIS: {e}")
            return None
    
    def document_exists(self, document_id: str) -> bool:
        """Check if a document exists in the CMIS repository.
        
        Args:
            document_id: The document identifier
            
        Returns:
            True if document exists, False otherwise
        """
        try:
            obj = None
            
            if self.query_type == 'id':
                obj = self._get_object_by_id(document_id)
            elif self.query_type == 'query':
                obj = self._query_for_document(document_id)
            else:  # path
                path = self._get_document_path(document_id)
                obj = self._get_object_by_path(path)
            
            return obj is not None
            
        except Exception as e:
            print(f"Error checking document existence in CMIS: {e}")
            return False
    
    def list_documents(self, folder_path: str = "", max_results: int = 100) -> List[str]:
        """List PDF documents in a CMIS folder.
        
        Args:
            folder_path: Subfolder path (optional)
            max_results: Maximum number of documents to return
            
        Returns:
            List of document IDs/names
        """
        session = self._get_session()
        self._get_repository_info()
        
        documents = []
        
        # Build folder path
        if folder_path:
            if self.root_folder_path:
                full_path = f"{self.root_folder_path}/{folder_path}"
            else:
                full_path = folder_path if folder_path.startswith('/') else f"/{folder_path}"
        else:
            full_path = self.root_folder_path or '/'
        
        if self.binding == 'browser':
            # Get folder children
            root_url = self._get_root_folder_url()
            path = full_path[1:] if full_path.startswith('/') else full_path
            
            url = f"{root_url}/{quote(path, safe='/')}?cmisselector=children&maxItems={max_results}"
            
            try:
                response = session.get(url, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                
                for obj in result.get('objects', []):
                    props = obj.get('object', {}).get('succinctProperties', {})
                    name = props.get('cmis:name', '')
                    base_type = props.get('cmis:baseTypeId', '')
                    
                    # Only include documents (not folders)
                    if base_type == 'cmis:document' and name.lower().endswith('.pdf'):
                        # Remove .pdf extension
                        doc_id = name[:-4]
                        documents.append(doc_id)
                        
            except Exception as e:
                print(f"Error listing CMIS folder: {e}")
        else:
            # AtomPub - use query instead
            query = f"SELECT cmis:name FROM cmis:document WHERE cmis:name LIKE '%.pdf'"
            if full_path != '/':
                query += f" AND IN_FOLDER('{full_path}')"
            
            # Query execution would go here
            pass
        
        return documents[:max_results]
    
    def get_document_metadata(self, document_id: str) -> Optional[dict]:
        """Get metadata for a document in the CMIS repository.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Dict with document metadata, or None if not found
        """
        try:
            obj = None
            
            if self.query_type == 'id':
                obj = self._get_object_by_id(document_id)
            elif self.query_type == 'query':
                obj = self._query_for_document(document_id)
            else:
                path = self._get_document_path(document_id)
                obj = self._get_object_by_path(path)
            
            if not obj:
                return None
            
            # Extract properties
            if 'succinctProperties' in obj:
                props = obj['succinctProperties']
            elif 'properties' in obj:
                props = {k: v.get('value') for k, v in obj['properties'].items()}
            else:
                props = obj
            
            metadata = {
                'document_id': document_id,
                'cmis_object_id': props.get('cmis:objectId'),
                'name': props.get('cmis:name'),
                'content_type': props.get('cmis:contentStreamMimeType'),
                'size': props.get('cmis:contentStreamLength'),
                'created_by': props.get('cmis:createdBy'),
                'creation_date': props.get('cmis:creationDate'),
                'last_modified_by': props.get('cmis:lastModifiedBy'),
                'last_modification_date': props.get('cmis:lastModificationDate'),
                'version_label': props.get('cmis:versionLabel'),
                'is_latest_version': props.get('cmis:isLatestVersion'),
                'checkin_comment': props.get('cmis:checkinComment')
            }
            
            return {k: v for k, v in metadata.items() if v is not None}
            
        except Exception as e:
            print(f"Error getting CMIS document metadata: {e}")
            return None
    
    def test_connection(self) -> dict:
        """Test the CMIS connection and authentication.
        
        Returns:
            Dict with connection status and repository information
        """
        try:
            repo_info = self._get_repository_info()
            
            # Try to access root folder
            root_url = self._get_root_folder_url()
            session = self._get_session()
            
            root_accessible = False
            try:
                response = session.get(
                    f"{root_url}?cmisselector=object",
                    timeout=self.timeout
                )
                root_accessible = response.status_code == 200
            except:
                pass
            
            return {
                'success': True,
                'url': self.url,
                'binding': self.binding,
                'repository_id': self.repository_id,
                'repository_name': repo_info.get('repositoryName', 'Unknown'),
                'vendor': repo_info.get('vendorName', 'Unknown'),
                'product_name': repo_info.get('productName', 'Unknown'),
                'product_version': repo_info.get('productVersion', 'Unknown'),
                'cmis_version': repo_info.get('cmisVersionSupported', 'Unknown'),
                'root_folder_url': root_url,
                'root_folder_accessible': root_accessible,
                'root_folder_path': self.root_folder_path or '/'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': self.url,
                'binding': self.binding
            }
    
    def search_documents(self, search_term: str, max_results: int = 50) -> List[dict]:
        """Search for documents using CMIS full-text search.
        
        Args:
            search_term: Text to search for
            max_results: Maximum results to return
            
        Returns:
            List of matching documents with metadata
        """
        session = self._get_session()
        self._get_repository_info()
        
        results = []
        
        # CMIS SQL query with CONTAINS for full-text search
        query = f"SELECT * FROM cmis:document WHERE cmis:name LIKE '%{search_term}%' OR CONTAINS('{search_term}')"
        
        if self.binding == 'browser':
            url = f"{self.url}{self.repository_id}?cmisselector=query&q={quote(query)}&maxItems={max_results}"
            
            try:
                response = session.get(url, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                
                for obj in result.get('results', []):
                    props = obj.get('succinctProperties', {})
                    if props.get('cmis:name', '').lower().endswith('.pdf'):
                        results.append({
                            'object_id': props.get('cmis:objectId'),
                            'name': props.get('cmis:name'),
                            'path': props.get('cmis:path'),
                            'size': props.get('cmis:contentStreamLength'),
                            'last_modified': props.get('cmis:lastModificationDate')
                        })
                        
            except Exception as e:
                print(f"Error searching CMIS: {e}")
        
        return results
    
    def get_document_versions(self, document_id: str) -> List[dict]:
        """Get all versions of a document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            List of version information dicts
        """
        session = self._get_session()
        self._get_repository_info()
        
        versions = []
        
        # First get the document to find its object ID
        obj = None
        if self.query_type == 'id':
            obj = self._get_object_by_id(document_id)
        else:
            path = self._get_document_path(document_id)
            obj = self._get_object_by_path(path)
        
        if not obj:
            return versions
        
        # Get version series
        if 'succinctProperties' in obj:
            object_id = obj['succinctProperties'].get('cmis:objectId')
        else:
            object_id = obj.get('objectId')
        
        if object_id and self.binding == 'browser':
            url = f"{self.url}{self.repository_id}/root?objectId={quote(object_id)}&cmisselector=versions"
            
            try:
                response = session.get(url, timeout=self.timeout)
                response.raise_for_status()
                result = response.json()
                
                for ver in result.get('objects', []):
                    props = ver.get('object', {}).get('succinctProperties', {})
                    versions.append({
                        'version_label': props.get('cmis:versionLabel'),
                        'is_latest': props.get('cmis:isLatestVersion'),
                        'is_major': props.get('cmis:isMajorVersion'),
                        'created_by': props.get('cmis:createdBy'),
                        'creation_date': props.get('cmis:creationDate'),
                        'checkin_comment': props.get('cmis:checkinComment')
                    })
                    
            except Exception as e:
                print(f"Error getting document versions: {e}")
        
        return versions
