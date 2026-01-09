# Developing OpenMark Plugins

OpenMark features an **automatic plugin discovery system** that scans plugin directories at startup and registers all discovered plugins. This allows you to add custom plugins simply by placing Python files in the appropriate directories.

## Plugin Types

OpenMark supports three types of plugins:

1. **Authentication Plugins** - Handle user authentication
2. **PDF Source Plugins** - Retrieve PDF documents from various sources
3. **Annotations Plugins** - Store and retrieve annotations

## Automatic Plugin Discovery

At startup, OpenMark automatically discovers plugins by:

1. Scanning built-in plugin directories (`app/plugins/auth/`, `app/plugins/pdf_source/`, `app/plugins/annotations/`)
2. Scanning the custom plugins directory (`custom_plugins/` or path set via `OPENMARK_CUSTOM_PLUGINS_DIR`)
3. Finding all classes that inherit from the base plugin classes
4. Registering them with names derived from their class names

**Plugin naming convention:**
- `LocalAuthPlugin` → `local`
- `MongoDBAnnotationsPlugin` → `mongodb`
- `S3SourcePlugin` → `s3`
- `MyCustomAuthPlugin` → `mycustom`

## Adding Custom Plugins (Docker)

The easiest way to add custom plugins when using Docker is to mount a volume:

```yaml
# docker-compose.yml
services:
  openmark:
    image: gluk46546546/openmark:latest
    volumes:
      - ./config.json:/app/config.json:ro
      - ./custom_plugins:/app/custom_plugins:ro
```

**Directory structure:**
```
custom_plugins/
├── auth/
│   └── my_ldap_auth.py
├── pdf_source/
│   └── azure_blob_source.py
└── annotations/
    └── redis_annotations.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENMARK_CUSTOM_PLUGINS_DIR` | `./custom_plugins` | Path to custom plugins directory |

## Plugin Base Classes

All plugins must inherit from their respective base class in `app/plugins/base.py`:

```python
from abc import ABC, abstractmethod
from typing import Optional

class AuthenticationPlugin(ABC):
    def __init__(self, config: dict):
        self.config = config
    
    @abstractmethod
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """Returns {'token': str, 'expires_at': str} or None"""
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> Optional[dict]:
        """Returns {'username': str, 'role': str} or None"""
        pass
    
    @abstractmethod
    def invalidate_token(self, token: str) -> bool:
        """Returns True if successful"""
        pass


class PDFSourcePlugin(ABC):
    def __init__(self, config: dict):
        self.config = config
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[bytes]:
        """Returns PDF bytes or None"""
        pass
    
    @abstractmethod
    def document_exists(self, document_id: str) -> bool:
        """Returns True if document exists"""
        pass


class AnnotationsPlugin(ABC):
    def __init__(self, config: dict):
        self.config = config
    
    @abstractmethod
    def save_annotations(self, user_id: str, document_id: str, 
                         annotations: dict) -> bool:
        """Returns True if successful"""
        pass
    
    @abstractmethod
    def get_annotations(self, user_id: str, document_id: str) -> dict:
        """Returns {'notes': [], 'highlights': []}"""
        pass
```

## Creating a Custom Authentication Plugin

Create a new file in `custom_plugins/auth/`:

```python
# custom_plugins/auth/ldap_auth.py

from app.plugins.base import AuthenticationPlugin
from app.jwt_handler import get_jwt_handler
from typing import Optional
from datetime import datetime, timedelta

class LDAPAuthPlugin(AuthenticationPlugin):
    """LDAP authentication plugin example."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.ldap_url = config.get('ldap_url', 'ldap://localhost:389')
        self.base_dn = config.get('base_dn', 'dc=example,dc=com')
        self.token_expiry_hours = config.get('token_expiry_hours', 24)
    
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """
        Authenticate a user against LDAP.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            Dict with 'token' and 'expires_at' if successful, None otherwise
        """
        try:
            # Your LDAP authentication logic here
            # import ldap
            # conn = ldap.initialize(self.ldap_url)
            # conn.simple_bind_s(f"uid={username},{self.base_dn}", password)
            
            # Use JWT handler for token generation
            jwt_handler = get_jwt_handler()
            result = jwt_handler.generate_auth_token(
                username=username,
                role='user',  # Determine role from LDAP groups
                expires_in_hours=self.token_expiry_hours
            )
            
            return result
            
        except Exception as e:
            print(f"LDAP authentication error: {e}")
            return None
    
    def validate_token(self, token: str) -> Optional[dict]:
        """Validate an authentication token."""
        jwt_handler = get_jwt_handler()
        return jwt_handler.validate_auth_token(token)
    
    def invalidate_token(self, token: str) -> bool:
        """Invalidate an authentication token."""
        jwt_handler = get_jwt_handler()
        return jwt_handler.revoke_token(token)
```

Configure in `config.json`:

```json
{
  "plugins": {
    "authentication": {
      "type": "ldap",
      "config": {
        "ldap_url": "ldap://your-ldap-server:389",
        "base_dn": "dc=yourcompany,dc=com",
        "token_expiry_hours": 24
      }
    }
  }
}
```

## Creating a Custom PDF Source Plugin

```python
# custom_plugins/pdf_source/azure_blob_source.py

from app.plugins.base import PDFSourcePlugin
from typing import Optional

class AzureBlobSourcePlugin(PDFSourcePlugin):
    """Azure Blob Storage PDF source plugin."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.connection_string = config.get('connection_string')
        self.container_name = config.get('container_name', 'pdfs')
        self.prefix = config.get('prefix', '')
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of Azure Blob client."""
        if self._client is None:
            try:
                from azure.storage.blob import BlobServiceClient
            except ImportError:
                raise ImportError(
                    "azure-storage-blob is required. "
                    "Install with: pip install azure-storage-blob"
                )
            
            self._client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
        return self._client
    
    def _get_blob_name(self, document_id: str) -> str:
        """Build the blob name for a document."""
        if not document_id.endswith('.pdf'):
            document_id = f"{document_id}.pdf"
        if self.prefix:
            return f"{self.prefix.rstrip('/')}/{document_id}"
        return document_id
    
    def get_document(self, document_id: str) -> Optional[bytes]:
        """Retrieve a PDF document from Azure Blob Storage."""
        try:
            blob_name = self._get_blob_name(document_id)
            container = self.client.get_container_client(self.container_name)
            blob = container.get_blob_client(blob_name)
            return blob.download_blob().readall()
        except Exception as e:
            print(f"Error fetching document from Azure Blob: {e}")
            return None
    
    def document_exists(self, document_id: str) -> bool:
        """Check if a document exists in Azure Blob Storage."""
        try:
            blob_name = self._get_blob_name(document_id)
            container = self.client.get_container_client(self.container_name)
            blob = container.get_blob_client(blob_name)
            return blob.exists()
        except Exception:
            return False
```

Configure in `config.json`:

```json
{
  "plugins": {
    "pdf_source": {
      "type": "azureblob",
      "config": {
        "connection_string": "DefaultEndpointsProtocol=https;AccountName=...",
        "container_name": "documents",
        "prefix": "pdfs/"
      }
    }
  }
}
```

## Creating a Custom Annotations Plugin

```python
# custom_plugins/annotations/redis_annotations.py

from app.plugins.base import AnnotationsPlugin
import json

class RedisAnnotationsPlugin(AnnotationsPlugin):
    """Redis-based annotations storage plugin."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.redis_url = config.get('redis_url', 'redis://localhost:6379/0')
        self.key_prefix = config.get('key_prefix', 'openmark:annotations')
        self.ttl = config.get('ttl_seconds')  # Optional TTL
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of Redis client."""
        if self._client is None:
            try:
                import redis
            except ImportError:
                raise ImportError(
                    "redis is required. Install with: pip install redis"
                )
            self._client = redis.from_url(self.redis_url)
        return self._client
    
    def _get_key(self, user_id: str, document_id: str) -> str:
        """Build Redis key for annotations."""
        return f"{self.key_prefix}:{user_id}:{document_id}"
    
    def save_annotations(self, user_id: str, document_id: str, 
                         annotations: dict) -> bool:
        """Save annotations to Redis."""
        try:
            key = self._get_key(user_id, document_id)
            data = json.dumps(annotations)
            
            if self.ttl:
                self.client.setex(key, self.ttl, data)
            else:
                self.client.set(key, data)
            return True
        except Exception as e:
            print(f"Error saving annotations to Redis: {e}")
            return False
    
    def get_annotations(self, user_id: str, document_id: str) -> dict:
        """Retrieve annotations from Redis."""
        try:
            key = self._get_key(user_id, document_id)
            data = self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Error retrieving annotations from Redis: {e}")
        
        return {"notes": [], "highlights": []}
```

Configure in `config.json`:

```json
{
  "plugins": {
    "annotations": {
      "type": "redis",
      "config": {
        "redis_url": "redis://localhost:6379/0",
        "key_prefix": "myapp:annotations",
        "ttl_seconds": 86400
      }
    }
  }
}
```

## Listing Available Plugins

At startup, OpenMark logs all discovered plugins:

```
🔍 Discovering plugins...
  Scanning auth plugins in app/plugins/auth...
  ✓ Registered auth plugin: local
  ✓ Registered auth plugin: oauth
  ✓ Registered auth plugin: saml
  ✓ Registered auth plugin: mongodb
  ✓ Registered auth plugin: postgresql
  Scanning pdf_source plugins in app/plugins/pdf_source...
  ✓ Registered pdf_source plugin: http
  ✓ Registered pdf_source plugin: s3
  ✓ Registered pdf_source plugin: local
  ✓ Registered pdf_source plugin: webdav
  ✓ Registered pdf_source plugin: ftp
  ✓ Registered pdf_source plugin: sftp
  ✓ Registered pdf_source plugin: cmis
  Scanning annotations plugins in app/plugins/annotations...
  ✓ Registered annotations plugin: local
  ✓ Registered annotations plugin: mongodb
  ✓ Registered annotations plugin: postgresql
  Scanning custom plugins in ./custom_plugins...
    Custom auth plugins...
    ✓ Registered auth plugin: ldap
    Custom pdf_source plugins...
    ✓ Registered pdf_source plugin: azureblob
✅ Plugin discovery complete.
```

## Best Practices

### 1. Use Lazy Initialization

For optional dependencies, use lazy initialization:

```python
@property
def client(self):
    if self._client is None:
        try:
            import some_library
        except ImportError:
            raise ImportError("some_library is required. Install with: pip install some_library")
        self._client = some_library.Client()
    return self._client
```

### 2. Handle Errors Gracefully

Always wrap external calls in try/except blocks:

```python
def get_document(self, document_id: str) -> Optional[bytes]:
    try:
        return self._fetch_document(document_id)
    except Exception as e:
        print(f"Error fetching document: {e}")
        return None
```

### 3. Use the JWT Handler for Authentication Plugins

For consistency, use the centralized JWT handler:

```python
from app.jwt_handler import get_jwt_handler

jwt_handler = get_jwt_handler()
result = jwt_handler.generate_auth_token(username, role, expires_in_hours)
```

### 4. Validate Configuration

Check required configuration parameters:

```python
def __init__(self, config: dict):
    super().__init__(config)
    
    if 'connection_string' not in config:
        raise ValueError("connection_string is required")
    
    self.connection_string = config['connection_string']
```

## Troubleshooting Custom Plugins

**Plugin not discovered:**
- Ensure the file is in the correct subdirectory (`auth/`, `pdf_source/`, or `annotations/`)
- Check that the class inherits from the correct base class
- Verify there are no syntax errors (check startup logs)
- Make sure the file doesn't start with `__` or `test_`

**Import errors:**
- Install required dependencies in the Docker container
- Use lazy initialization for optional dependencies

**Plugin name conflicts:**
- Custom plugins with the same name as built-in plugins will override them
- Use unique class names to avoid conflicts

## Testing Plugins

Create unit tests for your plugins:

```python
# tests/test_my_plugin.py

import pytest
from custom_plugins.pdf_source.azure_blob_source import AzureBlobSourcePlugin

def test_blob_name_generation():
    plugin = AzureBlobSourcePlugin({
        'connection_string': 'test',
        'prefix': 'documents/'
    })
    
    assert plugin._get_blob_name('report') == 'documents/report.pdf'
    assert plugin._get_blob_name('report.pdf') == 'documents/report.pdf'
```

Run tests with:

```bash
pytest tests/test_my_plugin.py
```
