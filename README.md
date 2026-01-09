# OpenMark

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)

OpenMark is a comprehensive PDF visualization solution with annotation capabilities, including virtual sticky notes and text highlighting features.

![Démo OpenMark](https://github.com/gLUK00/OpenMark/raw/main/docs/openMark.gif)

## Features

- 📄 **PDF Visualization** - View PDF documents directly in your browser
- 📝 **Sticky Notes** - Create, edit, and delete virtual post-it notes on specific document areas
- 🖍️ **Text Highlighting** - Highlight text zones with customizable colors
- 🔐 **Secure Authentication** - Multiple authentication backends (Local, LDAP, OAuth, SSO)
- 📊 **Usage Statistics** - Track document views, notes, and highlights usage
- 📜 **History Tracking** - View consultation history with timestamps and IP addresses
- 🔌 **Plugin System** - Extensible architecture for authentication, PDF sources, and storage

## Architecture

### Integration Overview

OpenMark is designed to be integrated into your existing infrastructure. Your backend server handles user authentication and document access control, then delegates PDF viewing to OpenMark.

```mermaid
graph TD
    subgraph "Your Infrastructure"
        subgraph "Client Application"
            CA[👤 End User Browser]
            IFRAME[iframe / New Tab]
        end
        
        subgraph "Your Backend Server"
            YS[🖥️ Your Server]
            YDB[(Your Database)]
        end
    end
    
    subgraph "OpenMark Docker Container"
        subgraph "OpenMark Server - Flask"
            API[REST API]
            AUTH[Auth Plugin]
            PDF[PDF Source Plugin]
            ANN[Annotations Plugin]
        end
    end
    
    subgraph "External Services"
        PDFREPO[(📁 PDF Repository<br/>HTTP/HTTPS)]
        ANNDB[(💾 Annotations DB<br/>MongoDB/PostgreSQL)]
    end
    
    CA -->|1. Request document| YS
    YS -->|2. Check permissions| YDB
    YS -->|3. POST /api/quickView| API
    API -->|4. Authenticate| AUTH
    API -->|5. Return DAT + viewUrl| YS
    YS -->|6. Send viewer URL| CA
    CA -->|7. Load viewer| IFRAME
    IFRAME -->|8. GET /api/viewDocument?dat=...| API
    API -->|9. Fetch PDF| PDF
    PDF -->|10. Download| PDFREPO
    API -->|11. Load annotations| ANN
    ANN -->|12. Query| ANNDB
    IFRAME -->|13. Display PDF + Annotations| CA
    IFRAME -->|14. POST /api/saveAnnotations| API
    API -->|15. Save| ANN
    ANN -->|16. Store| ANNDB

    style CA fill:#e1f5fe
    style YS fill:#fff3e0
    style API fill:#e8f5e9
    style PDFREPO fill:#fce4ec
    style ANNDB fill:#f3e5f5
```

### Detailed Integration Flow

```mermaid
sequenceDiagram
    participant User as 👤 User Browser
    participant YourServer as 🖥️ Your Server
    participant OpenMark as 📄 OpenMark API
    participant PDFRepo as 📁 PDF Repository
    participant AnnotDB as 💾 Annotations DB

    Note over User,AnnotDB: Step 1: Authentication & Document Request
    User->>YourServer: Request to view document
    YourServer->>YourServer: Verify user permissions
    YourServer->>OpenMark: POST /api/quickView<br/>{username, password, documentId}
    OpenMark->>OpenMark: Authenticate user
    OpenMark->>OpenMark: Generate DAT (Document Access Token)
    OpenMark-->>YourServer: {viewUrl, dat, validFor: "2 hours"}
    YourServer-->>User: Redirect to viewUrl or embed in iframe

    Note over User,AnnotDB: Step 2: Document Viewing
    User->>OpenMark: GET /api/viewDocument?dat=<token>
    OpenMark->>OpenMark: Validate DAT
    OpenMark->>PDFRepo: Fetch PDF (cached if available)
    PDFRepo-->>OpenMark: PDF bytes
    OpenMark->>AnnotDB: Get annotations for user/document
    AnnotDB-->>OpenMark: {notes, highlights}
    OpenMark-->>User: HTML Viewer + PDF + Annotations

    Note over User,AnnotDB: Step 3: Saving Annotations
    User->>OpenMark: POST /api/saveAnnotations<br/>{documentId, annotations}
    OpenMark->>OpenMark: Validate DAT
    OpenMark->>AnnotDB: Save annotations
    AnnotDB-->>OpenMark: Success
    OpenMark-->>User: {success: true}

    Note over User,AnnotDB: ✅ User can refresh (F5) - DAT remains valid for 2 hours
```

### Component Architecture

```mermaid
graph LR
    subgraph "Docker Container"
        subgraph "OpenMark Server"
            FLASK[Flask App]
            JWT[JWT Handler<br/>DAT Generation]
            CACHE[PDF Cache]
            
            subgraph "Plugin System"
                direction TB
                AP[Auth Plugins<br/>• Local JSON<br/>• OAuth 2.0<br/>• SAML SSO<br/>• MongoDB<br/>• PostgreSQL]
                PP[PDF Source Plugins<br/>• HTTP/HTTPS<br/>• AWS S3<br/>• Local Filesystem<br/>• WebDAV<br/>• FTP/FTPS<br/>• SFTP<br/>• CMIS]
                NP[Annotations Plugins<br/>• Local JSON<br/>• MongoDB<br/>• PostgreSQL]
            end
        end
    end
    
    FLASK --> JWT
    FLASK --> CACHE
    FLASK --> AP
    FLASK --> PP
    FLASK --> NP
    
    style FLASK fill:#4caf50,color:#fff
    style JWT fill:#ff9800,color:#fff
    style CACHE fill:#2196f3,color:#fff
```

### Deployment Options

```mermaid
graph TB
    subgraph "Option 1: Standalone"
        S1[OpenMark Container]
        S1DB[(Local JSON Files)]
        S1 --> S1DB
    end
    
    subgraph "Option 2: With MongoDB"
        S2[OpenMark Container]
        S2DB[(MongoDB)]
        S2 --> S2DB
    end
    
    subgraph "Option 3: Enterprise"
        S3[OpenMark Container]
        S3AUTH[(PostgreSQL<br/>Users)]
        S3ANN[(PostgreSQL<br/>Annotations)]
        S3SSO[SAML IdP]
        S3 --> S3AUTH
        S3 --> S3ANN
        S3 --> S3SSO
    end
    
    style S1 fill:#e8f5e9
    style S2 fill:#e3f2fd
    style S3 fill:#fce4ec
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
    "secret_key": "your-secret-key-change-in-production",
    "cors": {
      "allowed_origins": "*",
      "allow_iframe_embedding": true
    }
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

### Cross-Domain and iframe Embedding

OpenMark supports cross-domain usage and iframe embedding, which is essential when:
- The authentication server is on a different domain
- The PDF viewer needs to be embedded in an external application
- Client applications display the viewer in an iframe

#### CORS Configuration

```json
{
  "server": {
    "cors": {
      "allowed_origins": "*",
      "allow_iframe_embedding": true
    }
  }
}
```

| Setting | Description |
|---------|-------------|
| `allowed_origins` | Origins allowed for CORS. Use `"*"` for all origins, or specify domains like `["https://app1.com", "https://app2.com"]` |
| `allow_iframe_embedding` | Enable embedding the viewer in iframes from any origin |

#### Typical Integration Flow

```mermaid
sequenceDiagram
    participant YS as 🖥️ Your Server<br/>(any domain)
    participant OM as 📄 OpenMark Server
    participant CA as 👤 Client App<br/>(browser)

    YS->>OM: 1. POST /api/quickView
    OM-->>YS: 2. Return DAT + viewUrl
    YS->>CA: 3. Send viewer URL
    CA->>OM: 4. Load viewer (iframe or new tab)
    OM-->>CA: 5. Display PDF + Annotations
    
    Note over CA,OM: 🔄 F5 refresh works!<br/>DAT remains valid for 2 hours
```

> **Document Access Token (DAT)** is a self-contained JWT that survives page refreshes. No need to re-authenticate after F5!

#### Example: Embedding in iframe

```html
<!-- On your external application -->
<!-- Using DAT (JWT Document Access Token) -->
<iframe 
  src="https://openmark-server.com/api/viewDocument?dat=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  width="100%" 
  height="800"
  frameborder="0"
  allow="fullscreen">
</iframe>
```

> **Note:** All authentication uses JWT tokens. The DAT (Document Access Token) is a self-contained JWT that includes user permissions and document access rights.

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

#### OAuth 2.0 Authentication Plugin

Authenticate users via OAuth 2.0 providers (Google, GitHub, Microsoft, or custom).

**Requirements:** `pip install requests`

```json
{
  "plugins": {
    "authentication": {
      "type": "oauth",
      "config": {
        "provider": "google",
        "client_id": "your-google-client-id.apps.googleusercontent.com",
        "client_secret": "your-google-client-secret",
        "redirect_uri": "https://your-openmark-server.com/api/oauth/callback",
        "token_expiry_hours": 24,
        "default_role": "user"
      }
    }
  }
}
```

**Supported providers:** `google`, `github`, `microsoft`, `custom`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | string | Yes | OAuth provider name |
| `client_id` | string | Yes | OAuth client ID from provider |
| `client_secret` | string | Yes | OAuth client secret from provider |
| `redirect_uri` | string | Yes | Callback URL after authorization |
| `token_expiry_hours` | number | No | Token validity (default: 24) |
| `default_role` | string | No | Default role for users (default: 'user') |

**Custom provider configuration:**

```json
{
  "plugins": {
    "authentication": {
      "type": "oauth",
      "config": {
        "provider": "custom",
        "client_id": "your-client-id",
        "client_secret": "your-client-secret",
        "redirect_uri": "https://your-server.com/api/oauth/callback",
        "authorize_url": "https://idp.example.com/oauth/authorize",
        "token_url": "https://idp.example.com/oauth/token",
        "userinfo_url": "https://idp.example.com/oauth/userinfo",
        "scope": "openid email profile",
        "username_field": "email"
      }
    }
  }
}
```

**OAuth Flow:**
```
1. Client calls /api/authenticate → Returns {requires_oauth: true, auth_url: "..."}
2. Client redirects user to auth_url
3. User authenticates with OAuth provider
4. Provider redirects to redirect_uri with code
5. Backend calls /api/authenticate with username="oauth_callback", password="code:state"
6. Returns {token: "...", expires_at: "..."}
```

#### SAML SSO Authentication Plugin

Authenticate users via SAML 2.0 Single Sign-On with enterprise Identity Providers.

**Requirements:** `pip install python3-saml` (optional, for full SAML support)

```json
{
  "plugins": {
    "authentication": {
      "type": "saml",
      "config": {
        "idp_entity_id": "https://idp.example.com/saml/metadata",
        "idp_sso_url": "https://idp.example.com/saml/sso",
        "idp_slo_url": "https://idp.example.com/saml/slo",
        "idp_x509_cert": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
        "sp_entity_id": "https://your-openmark-server.com/saml/metadata",
        "sp_acs_url": "https://your-openmark-server.com/api/saml/acs",
        "sp_slo_url": "https://your-openmark-server.com/api/saml/slo",
        "token_expiry_hours": 24,
        "default_role": "user",
        "username_attribute": "email",
        "role_attribute": "role",
        "role_mapping": {
          "admin": "admin",
          "manager": "user",
          "employee": "user"
        }
      }
    }
  }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `idp_entity_id` | string | Yes | Identity Provider Entity ID |
| `idp_sso_url` | string | Yes | IdP Single Sign-On URL |
| `idp_slo_url` | string | No | IdP Single Logout URL |
| `idp_x509_cert` | string | Yes | IdP X.509 certificate (PEM) |
| `sp_entity_id` | string | Yes | Service Provider Entity ID |
| `sp_acs_url` | string | Yes | SP Assertion Consumer Service URL |
| `sp_slo_url` | string | No | SP Single Logout URL |
| `username_attribute` | string | No | SAML attribute for username (default: 'email') |
| `role_attribute` | string | No | SAML attribute for role |
| `role_mapping` | object | No | Map IdP roles to OpenMark roles |

**SAML Flow:**
```
1. Client calls /api/authenticate with username="saml_login"
2. Returns {requires_saml: true, login_url: "https://idp.../saml/sso?SAMLRequest=..."}
3. Client redirects user to login_url
4. User authenticates with IdP
5. IdP POSTs SAMLResponse to sp_acs_url
6. Backend calls /api/authenticate with username="saml_callback", password=<base64 SAMLResponse>
7. Returns {token: "...", expires_at: "...", username: "..."}
```

#### MongoDB Authentication Plugin

Store users and sessions in MongoDB for scalable, multi-instance deployments.

**Requirements:** `pip install pymongo`

```json
{
  "plugins": {
    "authentication": {
      "type": "mongodb",
      "config": {
        "connection_string": "mongodb://localhost:27017",
        "database": "openmark",
        "users_collection": "users",
        "tokens_collection": "auth_tokens",
        "token_expiry_hours": 24,
        "create_indexes": true
      }
    }
  }
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `connection_string` | string | No | mongodb://localhost:27017 | MongoDB connection URI |
| `database` | string | No | openmark | Database name |
| `users_collection` | string | No | users | Users collection name |
| `tokens_collection` | string | No | auth_tokens | Tokens collection name |
| `token_expiry_hours` | number | No | 24 | Token validity duration |
| `create_indexes` | boolean | No | true | Auto-create indexes |

**User document schema:**
```json
{
  "username": "admin",
  "password_hash": "sha256_hash",
  "role": "admin",
  "email": "admin@example.com",
  "created_at": "2026-01-07T10:00:00Z",
  "updated_at": "2026-01-07T10:00:00Z",
  "active": true
}
```

**Features:**
- ✅ TTL index for automatic token expiration
- ✅ Connection pooling for performance
- ✅ Default admin/user accounts created on first run
- ✅ User management methods (create, update, deactivate)

#### PostgreSQL Authentication Plugin

Store users and sessions in PostgreSQL for robust, ACID-compliant authentication.

**Requirements:** `pip install psycopg2-binary`

```json
{
  "plugins": {
    "authentication": {
      "type": "postgresql",
      "config": {
        "host": "localhost",
        "port": 5432,
        "database": "openmark",
        "user": "openmark",
        "password": "your-secure-password",
        "users_table": "auth_users",
        "tokens_table": "auth_tokens",
        "token_expiry_hours": 24,
        "pool_min_conn": 1,
        "pool_max_conn": 10,
        "create_tables": true
      }
    }
  }
}
```

**Alternative connection string format:**
```json
{
  "plugins": {
    "authentication": {
      "type": "postgresql",
      "config": {
        "connection_string": "postgresql://openmark:password@localhost:5432/openmark",
        "token_expiry_hours": 24
      }
    }
  }
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | string | No | localhost | PostgreSQL host |
| `port` | number | No | 5432 | PostgreSQL port |
| `database` | string | No | openmark | Database name |
| `user` | string | No | openmark | Database user |
| `password` | string | Yes* | - | Database password (*if not using connection_string) |
| `connection_string` | string | No | - | Full PostgreSQL URI (alternative to host/port/etc.) |
| `users_table` | string | No | auth_users | Users table name |
| `tokens_table` | string | No | auth_tokens | Tokens table name |
| `pool_min_conn` | number | No | 1 | Minimum pool connections |
| `pool_max_conn` | number | No | 10 | Maximum pool connections |
| `create_tables` | boolean | No | true | Auto-create tables |

**Features:**
- ✅ Connection pooling (ThreadedConnectionPool)
- ✅ Automatic expired token cleanup
- ✅ Cascading delete (deactivating user removes all tokens)
- ✅ Default admin/user accounts created on first run
- ✅ User management methods (create, update, deactivate)

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

#### S3 PDF Source Plugin

Retrieve PDF documents from an AWS S3 bucket or any S3-compatible storage service (MinIO, LocalStack, DigitalOcean Spaces, etc.).

**Requirements:** `pip install boto3`

**Basic configuration with explicit credentials:**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "s3",
      "config": {
        "bucket_name": "my-pdf-bucket",
        "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
        "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "region_name": "eu-west-1",
        "prefix": "documents/"
      }
    }
  }
}
```

**Configuration using IAM roles (recommended for AWS):**

When running on EC2, ECS, or Lambda with an attached IAM role, credentials are automatically retrieved:

```json
{
  "plugins": {
    "pdf_source": {
      "type": "s3",
      "config": {
        "bucket_name": "my-pdf-bucket",
        "region_name": "eu-west-1",
        "prefix": "documents/"
      }
    }
  }
}
```

**Configuration for S3-compatible services (MinIO, LocalStack):**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "s3",
      "config": {
        "bucket_name": "my-pdf-bucket",
        "aws_access_key_id": "minioadmin",
        "aws_secret_access_key": "minioadmin",
        "endpoint_url": "http://localhost:9000",
        "region_name": "us-east-1",
        "use_ssl": false,
        "verify_ssl": false
      }
    }
  }
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `bucket_name` | string | Yes | - | Name of the S3 bucket containing PDFs |
| `aws_access_key_id` | string | No* | - | AWS access key ID (*optional if using IAM roles) |
| `aws_secret_access_key` | string | No* | - | AWS secret access key (*optional if using IAM roles) |
| `aws_session_token` | string | No | - | Session token for temporary credentials |
| `region_name` | string | No | us-east-1 | AWS region where the bucket is located |
| `prefix` | string | No | - | Key prefix for documents (e.g., `documents/` or `pdfs/2024/`) |
| `endpoint_url` | string | No | - | Custom S3 endpoint URL for S3-compatible services |
| `use_ssl` | boolean | No | true | Use SSL/TLS for connections |
| `verify_ssl` | boolean | No | true | Verify SSL certificates |

**S3 Key Structure:**

Documents are retrieved using the pattern: `{prefix}/{document_id}.pdf`

| Configuration | Document ID | S3 Key |
|---------------|-------------|--------|
| `prefix: ""` | `invoice_001` | `invoice_001.pdf` |
| `prefix: "documents/"` | `invoice_001` | `documents/invoice_001.pdf` |
| `prefix: "pdfs/2024/"` | `report` | `pdfs/2024/report.pdf` |

**IAM Policy Example:**

Minimum required permissions for the S3 bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:HeadObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-pdf-bucket",
        "arn:aws:s3:::my-pdf-bucket/*"
      ]
    }
  ]
}
```

**Features:**
- ✅ Automatic credential discovery (IAM roles, environment variables, AWS config file)
- ✅ Support for S3-compatible services (MinIO, LocalStack, DigitalOcean Spaces)
- ✅ Configurable key prefix for organizing documents
- ✅ Document existence check without downloading (HEAD request)
- ✅ List documents in bucket
- ✅ Automatic retry on transient failures
- ✅ PDF validation on download

#### Local Filesystem PDF Source Plugin

Retrieve PDF documents from the local filesystem. Ideal for development, testing, or when PDFs are stored on a mounted volume or network share.

**Basic configuration:**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "local",
      "config": {
        "base_path": "./data/pdfs"
      }
    }
  }
}
```

**Configuration with subdirectory support:**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "local",
      "config": {
        "base_path": "/mnt/documents/pdfs",
        "recursive": true,
        "create_base_path": true
      }
    }
  }
}
```

**Docker volume mount example:**

```yaml
# docker-compose.yml
services:
  openmark:
    image: openmark:latest
    volumes:
      - ./my-pdfs:/app/data/pdfs:ro
```

```json
{
  "plugins": {
    "pdf_source": {
      "type": "local",
      "config": {
        "base_path": "/app/data/pdfs",
        "recursive": true
      }
    }
  }
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_path` | string | No | ./data/pdfs | Base directory path for PDF files |
| `recursive` | boolean | No | false | Search subdirectories recursively |
| `allowed_extensions` | array | No | [".pdf"] | List of allowed file extensions |
| `create_base_path` | boolean | No | true | Create base_path if it doesn't exist |

**Document ID to File Path Mapping:**

| Configuration | Document ID | File Path |
|---------------|-------------|-----------|
| `base_path: "./data/pdfs"` | `invoice_001` | `./data/pdfs/invoice_001.pdf` |
| `base_path: "./data/pdfs"` | `2024/report` | `./data/pdfs/2024/report.pdf` |
| `recursive: true` | `invoice_001` | Searches in all subdirectories |

**Security Features:**
- ✅ Path traversal protection (prevents `../` attacks)
- ✅ Validates file paths stay within base_path
- ✅ Extension validation

**Features:**
- ✅ Simple file-based document storage
- ✅ Recursive subdirectory search
- ✅ Docker volume mount friendly
- ✅ Document listing and metadata
- ✅ Automatic directory creation
- ✅ PDF validation on read

#### WebDAV PDF Source Plugin

Retrieve PDF documents from a WebDAV server (Nextcloud, ownCloud, Apache mod_dav, Nginx, SharePoint, etc.).

**Basic configuration:**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "webdav",
      "config": {
        "base_url": "https://webdav.example.com/documents/"
      }
    }
  }
}
```

**Configuration with authentication:**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "webdav",
      "config": {
        "base_url": "https://nextcloud.example.com/remote.php/dav/files/username/",
        "username": "your-username",
        "password": "your-app-password",
        "prefix": "Documents/PDFs",
        "timeout": 30
      }
    }
  }
}
```

**Configuration for Nextcloud:**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "webdav",
      "config": {
        "base_url": "https://your-nextcloud.com/remote.php/dav/files/username/",
        "username": "username",
        "password": "app-password-from-nextcloud-settings",
        "prefix": "Documents"
      }
    }
  }
}
```

**Configuration for ownCloud:**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "webdav",
      "config": {
        "base_url": "https://your-owncloud.com/remote.php/webdav/",
        "username": "username",
        "password": "password",
        "auth_type": "basic"
      }
    }
  }
}
```

**Configuration with Digest authentication:**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "webdav",
      "config": {
        "base_url": "https://webdav.example.com/",
        "username": "user",
        "password": "password",
        "auth_type": "digest"
      }
    }
  }
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_url` | string | Yes | - | WebDAV server URL (must end with /) |
| `username` | string | No | - | Username for authentication |
| `password` | string | No | - | Password for authentication |
| `prefix` | string | No | - | Path prefix for documents (e.g., `Documents/PDFs`) |
| `timeout` | number | No | 30 | Request timeout in seconds |
| `verify_ssl` | boolean | No | true | Verify SSL certificates |
| `auth_type` | string | No | basic | Authentication type: `basic` or `digest` |

**Document ID to WebDAV URL Mapping:**

| Configuration | Document ID | WebDAV URL |
|---------------|-------------|------------|
| `base_url: "https://dav.example.com/"` | `invoice_001` | `https://dav.example.com/invoice_001.pdf` |
| `prefix: "documents"` | `invoice_001` | `https://dav.example.com/documents/invoice_001.pdf` |
| `prefix: "2024/reports"` | `quarterly` | `https://dav.example.com/2024/reports/quarterly.pdf` |

**Compatible WebDAV Servers:**
- ✅ Nextcloud
- ✅ ownCloud
- ✅ Apache mod_dav
- ✅ Nginx with ngx_http_dav_module
- ✅ Microsoft SharePoint
- ✅ Box.com (WebDAV interface)
- ✅ Any RFC 4918 compliant server

**Features:**
- ✅ Basic and Digest authentication support
- ✅ Document listing via PROPFIND
- ✅ Document metadata retrieval
- ✅ Connection testing
- ✅ SSL/TLS support
- ✅ PDF validation on download
- ✅ URL encoding for special characters

#### FTP/FTPS PDF Source Plugin

Retrieve PDF documents from an FTP or FTPS (FTP over TLS) server.

**Basic configuration:**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "ftp",
      "config": {
        "host": "ftp.example.com",
        "username": "user",
        "password": "password"
      }
    }
  }
}
```

**Configuration with directory prefix:**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "ftp",
      "config": {
        "host": "ftp.example.com",
        "port": 21,
        "username": "documents-user",
        "password": "secure-password",
        "prefix": "/documents/pdfs",
        "passive": true,
        "timeout": 30
      }
    }
  }
}
```

**Configuration with FTPS (FTP over TLS):**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "ftp",
      "config": {
        "host": "secure-ftp.example.com",
        "port": 21,
        "username": "user",
        "password": "password",
        "use_tls": true,
        "prefix": "/secure/documents"
      }
    }
  }
}
```

**Configuration for anonymous FTP:**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "ftp",
      "config": {
        "host": "ftp.public-archive.org",
        "prefix": "/pub/documents"
      }
    }
  }
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | string | Yes | - | FTP server hostname or IP address |
| `port` | number | No | 21 | FTP server port |
| `username` | string | No | anonymous | Username for authentication |
| `password` | string | No | (empty) | Password for authentication |
| `prefix` | string | No | - | Directory path prefix (e.g., `/documents/pdfs`) |
| `passive` | boolean | No | true | Use passive mode (recommended for firewalls/NAT) |
| `timeout` | number | No | 30 | Connection timeout in seconds |
| `use_tls` | boolean | No | false | Use FTPS (FTP over TLS) |
| `encoding` | string | No | utf-8 | Server filename encoding |

**Document ID to FTP Path Mapping:**

| Configuration | Document ID | FTP Path |
|---------------|-------------|----------|
| `host: "ftp.example.com"` | `invoice_001` | `/invoice_001.pdf` |
| `prefix: "/documents"` | `invoice_001` | `/documents/invoice_001.pdf` |
| `prefix: "/2024/reports"` | `quarterly` | `/2024/reports/quarterly.pdf` |

**Active vs Passive Mode:**

| Mode | Description | Use When |
|------|-------------|----------|
| **Passive** (default) | Client initiates all connections | Behind firewall/NAT, most common |
| **Active** | Server connects back to client | Direct connection, legacy servers |

**FTP vs FTPS:**

| Protocol | Port | Description |
|----------|------|-------------|
| **FTP** | 21 | Standard unencrypted FTP |
| **FTPS** | 21/990 | FTP over TLS (encrypted) |

> ⚠️ **Security Note:** Standard FTP transmits credentials in plain text. Use FTPS (`use_tls: true`) for secure connections.

**Features:**
- ✅ FTP and FTPS (FTP over TLS) support
- ✅ Active and Passive mode support
- ✅ Anonymous FTP access
- ✅ Directory prefix configuration
- ✅ Document listing
- ✅ Document metadata (size, modification time)
- ✅ Connection testing
- ✅ Optional upload support
- ✅ PDF validation on download

#### SFTP PDF Source Plugin (SSH File Transfer Protocol)

The SFTP plugin retrieves PDFs from any server accessible via SSH/SFTP. This is different from FTPS - SFTP runs over SSH and provides better security. Compatible with Linux/Unix servers, NAS devices, cloud VMs, and any SSH-enabled system.

```json
{
  "plugins": {
    "pdf_source": {
      "type": "sftp",
      "config": {
        "host": "sftp.example.com",
        "port": 22,
        "username": "pdf_user",
        "password": "your-password",
        "prefix": "/var/documents/pdfs",
        "timeout": 30
      }
    }
  }
}
```

**SSH Key Authentication (Recommended):**

```json
{
  "plugins": {
    "pdf_source": {
      "type": "sftp",
      "config": {
        "host": "sftp.example.com",
        "port": 22,
        "username": "pdf_user",
        "private_key_path": "/path/to/id_rsa",
        "private_key_passphrase": "optional-key-passphrase",
        "prefix": "/data/pdfs",
        "known_hosts_path": "/home/user/.ssh/known_hosts"
      }
    }
  }
}
```

**Configuration Options:**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `host` | ✅ | - | SFTP server hostname or IP |
| `port` | ❌ | 22 | SSH port |
| `username` | ✅ | - | SSH username |
| `password` | ❌ | - | SSH password (use if no key auth) |
| `private_key_path` | ❌ | - | Path to private key file (RSA, Ed25519, ECDSA, DSS) |
| `private_key_passphrase` | ❌ | - | Passphrase for encrypted private key |
| `prefix` | ❌ | `/` | Directory path prefix for documents |
| `timeout` | ❌ | 30 | Connection timeout in seconds |
| `known_hosts_path` | ❌ | - | Path to known_hosts file for host verification |
| `auto_add_host_key` | ❌ | false | Auto-add unknown host keys (dev only!) |
| `compress` | ❌ | false | Enable SSH compression |

**Server Setup Examples:**

**1. Linux/Unix Server:**

```bash
# Create a dedicated user for PDF access
sudo useradd -m -s /bin/bash pdf_user
sudo mkdir -p /var/pdfs
sudo chown pdf_user:pdf_user /var/pdfs

# Set up SSH key authentication
sudo -u pdf_user mkdir -p /home/pdf_user/.ssh
# Add your public key to /home/pdf_user/.ssh/authorized_keys
```

Config:
```json
{
  "host": "192.168.1.100",
  "username": "pdf_user",
  "private_key_path": "/app/keys/id_ed25519",
  "prefix": "/var/pdfs"
}
```

**2. Synology NAS:**

Config:
```json
{
  "host": "synology.local",
  "port": 22,
  "username": "admin",
  "password": "your-password",
  "prefix": "/volume1/documents/pdfs"
}
```

**3. AWS EC2 / Cloud VM:**

Config:
```json
{
  "host": "ec2-xxx.compute.amazonaws.com",
  "port": 22,
  "username": "ubuntu",
  "private_key_path": "/app/keys/aws-key.pem",
  "prefix": "/home/ubuntu/pdfs"
}
```

**4. Azure VM:**

Config:
```json
{
  "host": "your-vm.westeurope.cloudapp.azure.com",
  "username": "azureuser",
  "private_key_path": "/app/keys/azure-key.pem",
  "prefix": "/data/documents"
}
```

**Document Path Resolution:**

| Config | Document ID | Resolved Path |
|--------|-------------|---------------|
| `prefix: ""` | `report` | `/report.pdf` |
| `prefix: "/docs"` | `report` | `/docs/report.pdf` |
| `prefix: "/data/pdfs"` | `2024/annual` | `/data/pdfs/2024/annual.pdf` |

**FTP vs FTPS vs SFTP Comparison:**

| Feature | FTP | FTPS | SFTP |
|---------|-----|------|------|
| Protocol Base | FTP | FTP + TLS | SSH |
| Default Port | 21 | 21/990 | 22 |
| Encryption | ❌ None | ✅ TLS | ✅ SSH |
| Authentication | User/Pass | User/Pass + Cert | User/Pass + Keys |
| Firewall Friendly | ❌ Multiple ports | ❌ Multiple ports | ✅ Single port |
| Linux Native | Requires FTP server | Requires FTP server | ✅ Built-in (OpenSSH) |

> 🔐 **Security Recommendation:** Use SSH key authentication instead of passwords. Keys are more secure and can be easily rotated.

> ⚠️ **Host Key Verification:** Set `auto_add_host_key: false` in production and provide a `known_hosts_path` to prevent man-in-the-middle attacks.

**Docker Deployment:**

Mount your SSH keys as a read-only volume:

```yaml
services:
  openmark:
    volumes:
      - ./ssh_keys:/app/keys:ro
```

**Features:**
- ✅ SSH key authentication (RSA, Ed25519, ECDSA, DSS)
- ✅ Password authentication
- ✅ Known hosts verification
- ✅ SSH compression support
- ✅ Directory prefix configuration
- ✅ Document listing
- ✅ Document metadata (size, permissions, timestamps)
- ✅ Connection testing
- ✅ Optional upload/delete support
- ✅ PDF validation on download

#### CMIS PDF Source Plugin (Enterprise Content Management)

The CMIS plugin retrieves PDFs from any ECM (Enterprise Content Management) system that supports the CMIS standard (Content Management Interoperability Services). This OASIS standard is supported by many enterprise systems.

**Supported ECM Systems:**
- **Alfresco** (Community & Enterprise)
- **Nuxeo Platform**
- **Microsoft SharePoint** (with CMIS connector)
- **OpenText Documentum**
- **IBM FileNet**
- **SAP Document Management**
- Any other CMIS 1.0/1.1 compliant system

```json
{
  "plugins": {
    "pdf_source": {
      "type": "cmis",
      "config": {
        "url": "https://ecm.example.com/alfresco/api/-default-/public/cmis/versions/1.1/browser",
        "binding": "browser",
        "username": "admin",
        "password": "your-password",
        "root_folder_path": "/Sites/documents/pdfs"
      }
    }
  }
}
```

**Configuration Options:**

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `url` | ✅ | - | CMIS service endpoint URL |
| `binding` | ❌ | `browser` | CMIS binding: `browser` or `atompub` |
| `repository_id` | ❌ | first | Repository ID (uses first if not specified) |
| `username` | ✅ | - | Authentication username |
| `password` | ✅ | - | Authentication password |
| `root_folder_path` | ❌ | `/` | Root folder path for documents |
| `query_type` | ❌ | `path` | How to find docs: `path`, `id`, or `query` |
| `timeout` | ❌ | 30 | Request timeout in seconds |
| `verify_ssl` | ❌ | true | Verify SSL certificates |

**ECM-Specific Configuration Examples:**

**1. Alfresco Community/Enterprise:**

```json
{
  "url": "https://alfresco.example.com/alfresco/api/-default-/public/cmis/versions/1.1/browser",
  "binding": "browser",
  "username": "admin",
  "password": "admin",
  "root_folder_path": "/Sites/mysite/documentLibrary/pdfs"
}
```

**2. Nuxeo Platform:**

```json
{
  "url": "https://nuxeo.example.com/nuxeo/json/cmis",
  "binding": "browser",
  "repository_id": "default",
  "username": "Administrator",
  "password": "Administrator",
  "root_folder_path": "/default-domain/workspaces/documents"
}
```

**3. SharePoint (with CMIS connector):**

```json
{
  "url": "https://sharepoint.example.com/_vti_bin/cmis/rest",
  "binding": "atompub",
  "username": "user@domain.com",
  "password": "your-password",
  "root_folder_path": "/Shared Documents/PDFs"
}
```

**4. OpenText Documentum:**

```json
{
  "url": "https://documentum.example.com/emc-cmis-webapp/browser",
  "binding": "browser",
  "repository_id": "MyRepository",
  "username": "dm_admin",
  "password": "your-password",
  "root_folder_path": "/Cabinet/Documents"
}
```

**Query Types:**

| Query Type | Document ID Format | Use Case |
|------------|-------------------|----------|
| `path` (default) | `reports/annual` | Documents organized in folders |
| `id` | `workspace://SpacesStore/abc-123` | Direct object ID access |
| `query` | `annual_report` | Search by document name |

**Document Path Resolution (query_type: path):**

| Config | Document ID | Resolved Path |
|--------|-------------|---------------|
| `root_folder_path: ""` | `report` | `/report.pdf` |
| `root_folder_path: "/docs"` | `report` | `/docs/report.pdf` |
| `root_folder_path: "/Sites/mysite"` | `2024/annual` | `/Sites/mysite/2024/annual.pdf` |

**CMIS Bindings:**

| Binding | Description | Recommended For |
|---------|-------------|-----------------|
| `browser` | JSON-based, modern | Alfresco 5+, Nuxeo, most modern ECMs |
| `atompub` | XML-based, legacy | SharePoint, older systems |

> 💡 **Tip:** Use `browser` binding when possible - it's more efficient and easier to debug.

**Advanced Features:**

```python
# Document versioning
versions = plugin.get_document_versions('annual_report')
for v in versions:
    print(f"Version {v['version_label']}: {v['checkin_comment']}")

# Full-text search
results = plugin.search_documents('budget 2024')
for doc in results:
    print(f"{doc['name']} - {doc['path']}")

# Get document metadata
metadata = plugin.get_document_metadata('report')
print(f"Last modified by: {metadata['last_modified_by']}")
```

**Features:**
- ✅ CMIS 1.0 and 1.1 support
- ✅ Browser and AtomPub bindings
- ✅ Path-based, ID-based, and query-based document access
- ✅ Multiple ECM vendor support
- ✅ Document versioning support
- ✅ Full-text search
- ✅ Rich metadata extraction
- ✅ SSL/TLS support
- ✅ Connection testing
- ✅ PDF validation on download

#### Local Annotations Plugin

> ⚠️ **WARNING: Development/Demo Use Only**
> 
> The Local Annotations Plugin stores all annotations in a single JSON file. This approach is **NOT recommended for production** environments because:
> - **Performance issues**: Reading and writing a large file can become slow as annotations grow
> - **Concurrency problems**: Simultaneous read/write operations may cause data corruption
> - **Scalability limitations**: The file can become unwieldy with many users and documents
> 
> **For production environments, use the MongoDB or PostgreSQL Annotations Plugin instead.**

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

#### MongoDB Annotations Plugin (Recommended for Production)

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

#### PostgreSQL Annotations Plugin

Store annotations in PostgreSQL using JSONB columns for efficient storage and querying.

**Requirements:** `pip install psycopg2-binary`

```json
{
  "plugins": {
    "annotations": {
      "type": "postgresql",
      "config": {
        "host": "localhost",
        "port": 5432,
        "database": "openmark",
        "user": "openmark",
        "password": "your-secure-password",
        "table": "annotations",
        "pool_min_conn": 1,
        "pool_max_conn": 10,
        "create_table": true
      }
    }
  }
}
```

**Alternative connection string format:**
```json
{
  "plugins": {
    "annotations": {
      "type": "postgresql",
      "config": {
        "connection_string": "postgresql://openmark:password@localhost:5432/openmark",
        "table": "annotations"
      }
    }
  }
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | string | No | localhost | PostgreSQL host |
| `port` | number | No | 5432 | PostgreSQL port |
| `database` | string | No | openmark | Database name |
| `user` | string | No | openmark | Database user |
| `password` | string | Yes* | - | Database password (*if not using connection_string) |
| `connection_string` | string | No | - | Full PostgreSQL URI |
| `table` | string | No | annotations | Annotations table name |
| `pool_min_conn` | number | No | 1 | Minimum pool connections |
| `pool_max_conn` | number | No | 10 | Maximum pool connections |
| `create_table` | boolean | No | true | Auto-create table and indexes |

**Database schema:**
```sql
CREATE TABLE annotations (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    notes JSONB DEFAULT '[]'::jsonb,
    highlights JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, document_id)
);
```

**Features:**
- ✅ JSONB columns for efficient JSON storage and querying
- ✅ GIN indexes for fast JSONB searches
- ✅ Connection pooling for performance
- ✅ Upsert support (INSERT ON CONFLICT)
- ✅ Additional methods: `delete_annotations()`, `get_user_documents()`, `search_notes()`, `get_statistics()`

## Security: Document Access Token (DAT)

OpenMark uses a **Document Access Token (DAT)** system for secure, stateless document access.

### What is DAT?

DAT is a self-contained JSON Web Token (JWT) that includes all necessary information to access a specific document:

### JWT Token Architecture

OpenMark uses JWT (JSON Web Tokens) for all authentication and authorization:

#### Token Types

| Token Type | Purpose | Lifetime | Usage |
|------------|---------|----------|-------|
| **AT (Authentication Token)** | API authentication after login | Configurable (default: 24h) | `Authorization: Bearer <token>` header |
| **DAT (Document Access Token)** | Document viewing access | 4× cache duration (min 2h) | URL parameter `?dat=<token>` |

#### Authentication Token (AT) Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    Authentication Token (AT)                     │
├─────────────────────────────────────────────────────────────────┤
│  Header:    { "alg": "HS256", "typ": "JWT" }                    │
│  Payload:   {                                                   │
│               "sub": "username",         // User identifier     │
│               "role": "admin",           // User role           │
│               "type": "at",              // Token type          │
│               "iat": 1736262000,         // Issued at           │
│               "exp": 1736348400,         // Expiration          │
│               "nbf": 1736262000          // Not before          │
│             }                                                   │
│  Signature: HMACSHA256(header + payload, SECRET_KEY)            │
└─────────────────────────────────────────────────────────────────┘
```

#### Document Access Token (DAT) Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    Document Access Token (DAT)                  │
├─────────────────────────────────────────────────────────────────┤
│  Header:    { "alg": "HS256", "typ": "JWT" }                    │
│  Payload:   {                                                   │
│               "tid": "temp_abc123",      // Temp Document ID    │
│               "did": "invoice_001",      // Document ID         │
│               "sub": "username",         // User                │
│               "hat": false,              // hideAnnotationsTools│
│               "ha": false,               // hideAnnotations     │
│               "hl": true,                // hideLogo            │
│               "exp": 1736265600,         // Expiration          │
│               "type": "dat"              // Token type          │
│             }                                                   │
│  Signature: HMACSHA256(header + payload, SECRET_KEY)            │
└─────────────────────────────────────────────────────────────────┘
```

### Benefits of JWT Architecture

| Feature | Description |
|---------|-------------|
| **Stateless** | Tokens are self-contained, no server-side session storage required |
| **Page refresh (F5)** | DAT survives browser refresh |
| **Scalability** | Works seamlessly with load balancers and multiple instances |
| **Token revocation** | Supported via blacklist (in-memory, MongoDB, or PostgreSQL) |
| **Single URL parameter** | DAT contains all permissions, no multiple query params needed |
| **Shareable URLs** | Document URLs with DAT can be shared (within validity period) |

### How It Works

```
1. User authenticates          → AT (Authentication Token) returned
2. Request document access     → DAT generated (2-hour minimum validity)
3. View document with DAT      → No AT needed for viewing
4. Page refresh (F5)           → DAT still valid ✅
5. Save annotations            → DAT authenticates the request
6. Logout                      → AT revoked via blacklist
```

### Configuration

DAT validity duration is automatically calculated as **4× the cache duration**, with a minimum of 2 hours:

```json
{
  "cache": {
    "duration_seconds": 3600  // 1 hour cache → 4 hours DAT validity
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

#### POST `/api/quickView`

**One-step authentication and document request.** This API combines authentication, document request, and URL generation into a single call. Ideal for external server integration where you need to generate a viewer URL to send to client applications.

**Request:**
```json
{
  "username": "string",
  "password": "string",
  "documentId": "string",
  "hideAnnotationsTools": false,
  "hideAnnotations": false,
  "hideLogo": false
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `username` | string | Yes | - | User's username |
| `password` | string | Yes | - | User's password |
| `documentId` | string | Yes | - | ID of the PDF document to view |
| `hideAnnotationsTools` | boolean | No | `false` | Hide annotation tools in the viewer |
| `hideAnnotations` | boolean | No | `false` | Hide existing annotations |
| `hideLogo` | boolean | No | `false` | Hide the OpenMark logo |

**Response (200 OK):**
```json
{
  "success": true,
  "viewUrl": "/api/viewDocument?dat=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "dat": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tempDocumentId": "temp_abc123",
  "validFor": "2 hours",
  "expires_at": "2026-01-07T15:00:00Z"
}
```

> **Note:** The response includes a **Document Access Token (DAT)** - a self-contained JWT that includes the user, document ID, view options, and expiration. This token allows secure document access without requiring the original auth token.
>
> **Benefits of DAT:**
> - ✅ Page refresh (F5) works without losing access
> - ✅ Valid for 2 hours (longer than cache duration)
> - ✅ Single token contains all necessary permissions
> - ✅ Can be stored and reused within validity period

**Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": "Invalid credentials"
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "error": "Document not found"
}
```

**Usage Example (External Server Integration):**

```python
import requests

OPENMARK_SERVER = 'https://openmark.example.com'

# Your external server calls OpenMark API
response = requests.post(f'{OPENMARK_SERVER}/api/quickView', json={
    'username': 'viewer_user',
    'password': 'secure_password',
    'documentId': 'invoice_2026_001',
    'hideAnnotationsTools': True,
    'hideLogo': True
})

data = response.json()
if data['success']:
    # Build full URL with the Document Access Token (DAT)
    viewer_url = OPENMARK_SERVER + data['viewUrl']
    # The DAT is valid for 2 hours - can safely store and reuse
    dat = data['dat']
    # Send this URL to your client application
```

```javascript
// Client-side: embed in iframe
// The DAT-based URL survives page refreshes!
const OPENMARK_SERVER = 'https://openmark.example.com';
const iframe = document.createElement('iframe');
iframe.src = OPENMARK_SERVER + viewUrl;  // Contains ?dat=<token>
iframe.width = '100%';
iframe.height = '800px';
document.body.appendChild(iframe);
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
  "documentId": "string",
  "hideAnnotationsTools": false,
  "hideAnnotations": false,
  "hideLogo": false
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `documentId` | string | Yes | - | ID of the PDF document to view |
| `hideAnnotationsTools` | boolean | No | `false` | Hide annotation tools in the viewer |
| `hideAnnotations` | boolean | No | `false` | Hide existing annotations |
| `hideLogo` | boolean | No | `false` | Hide the OpenMark logo |

**Response (200 OK):**
```json
{
  "success": true,
  "tempDocumentId": "temp_abc123xyz",
  "dat": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "validFor": "2 hours",
  "expires_at": "2026-01-06T15:00:00Z"
}
```

> **Recommended:** Use the `dat` (Document Access Token) for building view URLs. It's self-contained and survives page refreshes.
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

**Authentication:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dat` | string | Yes | Document Access Token (JWT containing all permissions) |

> **Note:** View options (hideAnnotationsTools, hideAnnotations, hideLogo) are embedded in the DAT token. No need to add them as query parameters.

**View Modes (configured when requesting document):**

- **Default mode**: Full annotation capabilities with toolbar and sidebar
- **Read-only mode** (`hideAnnotationsTools=true`): View annotations but cannot create/edit/delete them
- **Clean view mode** (`hideAnnotations=true`): View PDF without any annotations visible (also hides tools)
- **No branding mode** (`hideLogo=true`): Hide the OpenMark logo for embedded or white-label usage

**Example URL:**

```
/api/viewDocument?dat=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

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

OpenMark features an **automatic plugin discovery system** that scans plugin directories at startup and registers all discovered plugins. This allows you to add custom plugins simply by placing Python files in the appropriate directories.

### Plugin Types

OpenMark supports three types of plugins:

1. **Authentication Plugins** - Handle user authentication
2. **PDF Source Plugins** - Retrieve PDF documents from various sources
3. **Annotations Plugins** - Store and retrieve annotations

### Automatic Plugin Discovery

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

### Adding Custom Plugins (Docker)

The easiest way to add custom plugins when using Docker is to mount a volume:

```yaml
# docker-compose.yml
services:
  openmark:
    image: openmark:latest
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

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENMARK_CUSTOM_PLUGINS_DIR` | `./custom_plugins` | Path to custom plugins directory |

### Creating a Custom Authentication Plugin

Create a new file in `custom_plugins/auth/`:

```python
# custom_plugins/auth/ldap_auth.py

from app.plugins.base import AuthenticationPlugin
from typing import Optional
import hashlib
import secrets
from datetime import datetime, timedelta

class LDAPAuthPlugin(AuthenticationPlugin):
    """LDAP authentication plugin example."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.ldap_url = config.get('ldap_url', 'ldap://localhost:389')
        self.base_dn = config.get('base_dn', 'dc=example,dc=com')
        self.token_expiry_hours = config.get('token_expiry_hours', 24)
        self._tokens = {}  # In production, use Redis or database
    
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
            
            # Generate token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
            
            self._tokens[token] = {
                'username': username,
                'role': 'user',
                'expires_at': expires_at
            }
            
            return {
                'token': token,
                'expires_at': expires_at.isoformat()
            }
        except Exception as e:
            print(f"LDAP authentication error: {e}")
            return None
    
    def validate_token(self, token: str) -> Optional[dict]:
        """Validate an authentication token."""
        if token not in self._tokens:
            return None
        
        token_data = self._tokens[token]
        if datetime.utcnow() > token_data['expires_at']:
            del self._tokens[token]
            return None
        
        return {
            'username': token_data['username'],
            'role': token_data['role']
        }
    
    def invalidate_token(self, token: str) -> bool:
        """Invalidate an authentication token."""
        if token in self._tokens:
            del self._tokens[token]
            return True
        return False
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

### Creating a Custom PDF Source Plugin

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

### Creating a Custom Annotations Plugin

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

### Plugin Base Classes

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

### Listing Available Plugins

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
  Scanning annotations plugins in app/plugins/annotations...
  ✓ Registered annotations plugin: local
  ✓ Registered annotations plugin: mongodb
  ✓ Registered annotations plugin: postgresql
  Scanning custom plugins in ./custom_plugins...
    Custom auth plugins...
    ✓ Registered auth plugin: ldap
    Custom pdf_source plugins...
    ✓ Registered pdf_source plugin: azureblob
✅ Plugin discovery complete. Found: {'auth': ['local', 'oauth', 'saml', 'mongodb', 'postgresql', 'ldap'], ...}
```

### Troubleshooting Custom Plugins

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
