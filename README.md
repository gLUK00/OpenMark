# OpenMark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)

OpenMark is a comprehensive PDF visualization solution with annotation capabilities, including virtual sticky notes and text highlighting features.

## Features

- 📄 **PDF Visualization** - View PDF documents directly in your browser
- 📝 **Sticky Notes** - Create, edit, and delete virtual post-it notes on specific document areas
- 🖍️ **Text Highlighting** - Highlight text zones with customizable colors
- 🔐 **Secure Authentication** - Multiple authentication backends (Local, LDAP, OAuth, SSO)
- 📊 **Usage Statistics** - Track document views, notes, and highlights usage
- 📜 **History Tracking** - View consultation history with timestamps and IP addresses
- 🔌 **Plugin System** - Extensible architecture for authentication, PDF sources, and storage

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Browser                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    OpenMark Web Interface                            │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────┐  │   │
│  │  │  Login   │  │  PDF Viewer  │  │ Statistics │  │   History    │  │   │
│  │  │   Page   │  │  + Notes     │  │    Page    │  │     Page     │  │   │
│  │  └──────────┘  └──────────────┘  └────────────┘  └──────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTPS
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Docker Container                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      OpenMark Server (Flask)                         │   │
│  │                                                                       │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │                        REST API                              │    │   │
│  │  │  /api/authenticate  /api/requestDocument  /api/viewDocument │    │   │
│  │  │  /api/saveAnnotations  /api/getAnnotations  /api/statistics │    │   │
│  │  │  /api/history  /api/logout                                   │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                              │                                        │   │
│  │  ┌───────────────────────────┼───────────────────────────────────┐  │   │
│  │  │                    Plugin System                               │  │   │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │  │   │
│  │  │  │     Auth     │  │  PDF Source  │  │    Annotations   │    │  │   │
│  │  │  │    Plugin    │  │    Plugin    │  │      Plugin      │    │  │   │
│  │  │  └──────────────┘  └──────────────┘  └──────────────────┘    │  │   │
│  │  └───────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                    │                                    │
                    ▼                                    ▼
    ┌───────────────────────────────────────┐  ┌───────────────────────────┐
    │         PDF Repository                │  │   Annotations Database    │
    │       (HTTP/HTTPS Source)             │  │   (MongoDB / JSON File)   │
    └───────────────────────────────────────┘  └───────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.9 or higher
- Docker (optional, for containerized deployment)
- MongoDB (optional, for database storage)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/OpenMark.git
   cd OpenMark
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the application**
   ```bash
   cp config.example.json config.json
   # Edit config.json with your settings
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t openmark:latest .
   ```

2. **Run with Docker**
   ```bash
   docker run -d -p 5000:5000 -v ./config.json:/app/config.json openmark:latest
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

## Configuration

OpenMark uses a `config.json` file for all configuration settings.

### Basic Configuration

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "secret_key": "your-secret-key-change-in-production"
  },
  "cache": {
    "directory": "./cache",
    "duration_seconds": 3600
  },
  "plugins": {
    "authentication": {
      "type": "local",
      "config": {
        "users_file": "./data/users.json"
      }
    },
    "pdf_source": {
      "type": "http",
      "config": {
        "base_url": "https://your-pdf-repository.com/documents/",
        "timeout": 30
      }
    },
    "annotations": {
      "type": "local",
      "config": {
        "storage_path": "./data/annotations.json"
      }
    }
  },
  "customization": {
    "script_file": null,
    "logo_url": null,
    "primary_color": "#007bff"
  }
}
```

### Plugin Configurations

#### Local Authentication Plugin

```json
{
  "plugins": {
    "authentication": {
      "type": "local",
      "config": {
        "users_file": "./data/users.json",
        "token_expiry_hours": 24
      }
    }
  }
}
```

Users file format (`users.json`):
```json
{
  "users": [
    {
      "username": "admin",
      "password_hash": "sha256_hash_of_password",
      "role": "admin"
    },
    {
      "username": "user1",
      "password_hash": "sha256_hash_of_password",
      "role": "user"
    }
  ]
}
```

#### HTTP PDF Source Plugin

```json
{
  "plugins": {
    "pdf_source": {
      "type": "http",
      "config": {
        "base_url": "https://documents.example.com/",
        "timeout": 30,
        "headers": {
          "Authorization": "Bearer your-api-key"
        }
      }
    }
  }
}
```

#### Local Annotations Plugin

```json
{
  "plugins": {
    "annotations": {
      "type": "local",
      "config": {
        "storage_path": "./data/annotations.json"
      }
    }
  }
}
```

#### MongoDB Annotations Plugin

```json
{
  "plugins": {
    "annotations": {
      "type": "mongodb",
      "config": {
        "connection_string": "mongodb://localhost:27017",
        "database": "openmark",
        "collection": "annotations"
      }
    }
  }
}
```

## API Reference

### Authentication

#### POST `/api/authenticate`

Authenticate a user and receive an access token.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2026-01-07T12:00:00Z"
}
```

**Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": "Invalid credentials"
}
```

#### POST `/api/logout`

Invalidate the current authentication token.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true
}
```

### Document Management

#### POST `/api/requestDocument`

Request a PDF document to be prepared for viewing.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "documentId": "string"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "tempDocumentId": "temp_abc123xyz",
  "expires_at": "2026-01-06T13:00:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "error": "Document not found"
}
```

#### GET `/api/viewDocument`

View a PDF document with annotation capabilities.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tempDocumentId` | string | Yes | Temporary document ID |
| `token` | string | Yes | Authentication token |

**Response:**
Returns an HTML page with the PDF viewer interface.

### Annotations

#### POST `/api/saveAnnotations`

Save annotations (notes and highlights) for a document.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "documentId": "string",
  "annotations": {
    "notes": [
      {
        "id": "note_001",
        "page": 1,
        "x": 100,
        "y": 200,
        "width": 200,
        "height": 150,
        "content": "This is a note",
        "color": "#ffeb3b",
        "created_at": "2026-01-06T12:00:00Z",
        "updated_at": "2026-01-06T12:00:00Z"
      }
    ],
    "highlights": [
      {
        "id": "highlight_001",
        "page": 1,
        "rects": [
          {"x": 50, "y": 100, "width": 200, "height": 20}
        ],
        "color": "#ffff00",
        "created_at": "2026-01-06T12:00:00Z"
      }
    ]
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Annotations saved successfully"
}
```

#### GET `/api/getAnnotations`

Retrieve annotations for a document.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `documentId` | string | Yes | Document identifier |

**Response (200 OK):**
```json
{
  "success": true,
  "annotations": {
    "notes": [],
    "highlights": []
  }
}
```

### Statistics & History

#### GET `/api/statistics`

Get usage statistics for the authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "statistics": {
    "documents_viewed": 42,
    "notes_created": 156,
    "highlights_created": 89,
    "last_activity": "2026-01-06T11:30:00Z"
  }
}
```

#### GET `/api/history`

Get document consultation history.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Maximum number of entries (default: 50) |
| `offset` | integer | No | Pagination offset (default: 0) |

**Response (200 OK):**
```json
{
  "success": true,
  "history": [
    {
      "document_id": "doc123",
      "document_name": "Report Q4 2025",
      "timestamp": "2026-01-06T10:30:00Z",
      "ip_address": "192.168.1.100",
      "duration_seconds": 1800
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

## Plugin Development

OpenMark supports three types of plugins:

1. **Authentication Plugins** - Handle user authentication
2. **PDF Source Plugins** - Retrieve PDF documents from various sources
3. **Annotations Plugins** - Store and retrieve annotations

### Creating a Custom Authentication Plugin

Create a new file in `plugins/auth/`:

```python
# plugins/auth/custom_auth.py

from plugins.base import AuthenticationPlugin

class CustomAuthPlugin(AuthenticationPlugin):
    """Custom authentication plugin example."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        # Initialize your authentication backend
        self.api_url = config.get('api_url')
    
    def authenticate(self, username: str, password: str) -> dict | None:
        """
        Authenticate a user.
        
        Args:
            username: The username
            password: The password
            
        Returns:
            User dict with 'username' and 'role' keys if successful,
            None if authentication fails
        """
        # Implement your authentication logic
        # Example: call external API
        response = requests.post(f"{self.api_url}/auth", json={
            "username": username,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            return {
                "username": data["username"],
                "role": data.get("role", "user")
            }
        return None
    
    def validate_token(self, token: str) -> dict | None:
        """
        Validate an authentication token.
        
        Args:
            token: The JWT token
            
        Returns:
            User dict if valid, None otherwise
        """
        # Implement token validation
        pass
```

Register the plugin in `config.json`:

```json
{
  "plugins": {
    "authentication": {
      "type": "custom_auth",
      "config": {
        "api_url": "https://your-auth-service.com"
      }
    }
  }
}
```

### Creating a Custom PDF Source Plugin

```python
# plugins/pdf_source/s3_source.py

from plugins.base import PDFSourcePlugin
import boto3

class S3SourcePlugin(PDFSourcePlugin):
    """AWS S3 PDF source plugin."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=config['access_key'],
            aws_secret_access_key=config['secret_key'],
            region_name=config.get('region', 'us-east-1')
        )
        self.bucket = config['bucket']
    
    def get_document(self, document_id: str) -> bytes | None:
        """
        Retrieve a PDF document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            PDF bytes if found, None otherwise
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=f"{document_id}.pdf"
            )
            return response['Body'].read()
        except Exception:
            return None
    
    def document_exists(self, document_id: str) -> bool:
        """Check if a document exists."""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket,
                Key=f"{document_id}.pdf"
            )
            return True
        except Exception:
            return False
```

### Creating a Custom Annotations Plugin

```python
# plugins/annotations/postgresql_annotations.py

from plugins.base import AnnotationsPlugin
import psycopg2

class PostgreSQLAnnotationsPlugin(AnnotationsPlugin):
    """PostgreSQL annotations storage plugin."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.conn = psycopg2.connect(
            host=config['host'],
            port=config.get('port', 5432),
            database=config['database'],
            user=config['user'],
            password=config['password']
        )
    
    def save_annotations(self, user_id: str, document_id: str, 
                         annotations: dict) -> bool:
        """Save annotations to PostgreSQL."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO annotations (user_id, document_id, data)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, document_id) 
                DO UPDATE SET data = %s, updated_at = NOW()
            """, (user_id, document_id, json.dumps(annotations), 
                  json.dumps(annotations)))
            self.conn.commit()
            return True
        except Exception:
            return False
    
    def get_annotations(self, user_id: str, document_id: str) -> dict:
        """Retrieve annotations from PostgreSQL."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT data FROM annotations 
            WHERE user_id = %s AND document_id = %s
        """, (user_id, document_id))
        
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return {"notes": [], "highlights": []}
```

### Plugin Base Classes

All plugins must inherit from their respective base class:

```python
# plugins/base.py

from abc import ABC, abstractmethod

class AuthenticationPlugin(ABC):
    def __init__(self, config: dict):
        self.config = config
    
    @abstractmethod
    def authenticate(self, username: str, password: str) -> dict | None:
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> dict | None:
        pass


class PDFSourcePlugin(ABC):
    def __init__(self, config: dict):
        self.config = config
    
    @abstractmethod
    def get_document(self, document_id: str) -> bytes | None:
        pass
    
    @abstractmethod
    def document_exists(self, document_id: str) -> bool:
        pass


class AnnotationsPlugin(ABC):
    def __init__(self, config: dict):
        self.config = config
    
    @abstractmethod
    def save_annotations(self, user_id: str, document_id: str, 
                         annotations: dict) -> bool:
        pass
    
    @abstractmethod
    def get_annotations(self, user_id: str, document_id: str) -> dict:
        pass
```

## Usage Examples

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:5000"

# Authenticate
response = requests.post(f"{BASE_URL}/api/authenticate", json={
    "username": "user1",
    "password": "password123"
})
token = response.json()["token"]

headers = {"Authorization": f"Bearer {token}"}

# Request a document
response = requests.post(f"{BASE_URL}/api/requestDocument", 
    headers=headers,
    json={"documentId": "report-2025-q4"}
)
temp_doc_id = response.json()["tempDocumentId"]

# View document (open in browser)
view_url = f"{BASE_URL}/api/viewDocument?tempDocumentId={temp_doc_id}&token={token}"
print(f"Open in browser: {view_url}")

# Get annotations
response = requests.get(f"{BASE_URL}/api/getAnnotations",
    headers=headers,
    params={"documentId": "report-2025-q4"}
)
annotations = response.json()["annotations"]

# Save annotations
response = requests.post(f"{BASE_URL}/api/saveAnnotations",
    headers=headers,
    json={
        "documentId": "report-2025-q4",
        "annotations": {
            "notes": [{
                "id": "note_001",
                "page": 1,
                "x": 100,
                "y": 200,
                "width": 200,
                "height": 150,
                "content": "Important section",
                "color": "#ffeb3b"
            }],
            "highlights": []
        }
    }
)
```

### cURL Examples

```bash
# Authenticate
curl -X POST http://localhost:5000/api/authenticate \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "password123"}'

# Request document
curl -X POST http://localhost:5000/api/requestDocument \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"documentId": "report-2025-q4"}'

# Get statistics
curl -X GET http://localhost:5000/api/statistics \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get history
curl -X GET "http://localhost:5000/api/history?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

For support, please open an issue on GitHub or contact the maintainers.
