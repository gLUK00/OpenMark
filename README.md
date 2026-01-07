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
                PP[PDF Source Plugins<br/>• HTTP/HTTPS]
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
<!-- Using DAT (recommended - survives page refresh) -->
<iframe 
  src="https://openmark-server.com/api/viewDocument?dat=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  width="100%" 
  height="800"
  frameborder="0"
  allow="fullscreen">
</iframe>

<!-- Legacy method (will lose access on page refresh) -->
<iframe 
  src="https://openmark-server.com/api/viewDocument?tempDocumentId=temp_abc123&token=xyz&hideLogo=true"
  width="100%" 
  height="800"
  frameborder="0"
  allow="fullscreen">
</iframe>
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

### Benefits

| Feature | Legacy (token + tempDocumentId) | DAT |
|---------|--------------------------------|-----|
| Page refresh (F5) | ❌ Loses access | ✅ Works |
| Token validity | Short (matches auth) | Long (2 hours) |
| Parameters in URL | Multiple params | Single `dat` param |
| Re-authentication | Required on refresh | Not needed |
| Parallel documents | Complex | Easy - each has own DAT |
| Shareable URL | No (needs valid token) | Yes (within validity) |

### How It Works

```
1. User authenticates          → Auth token (short-lived)
2. Request document access     → DAT generated (2-hour validity)
3. View document with DAT      → No auth token needed
4. Page refresh (F5)           → DAT still valid ✅
5. Save annotations            → DAT authenticates the request
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

**Authentication Methods:**

1. **Using Document Access Token (DAT)** - Recommended:
   | Parameter | Type | Required | Description |
   |-----------|------|----------|-------------|
   | `dat` | string | Yes | Document Access Token (contains all permissions) |

2. **Using Legacy Method** (backward compatible):
   | Parameter | Type | Required | Description |
   |-----------|------|----------|-------------|
   | `tempDocumentId` | string | Yes | Temporary document ID |
   | `token` | string | Yes | Authentication token |
   | `hideAnnotationsTools` | boolean | No | Hide annotation tools |
   | `hideAnnotations` | boolean | No | Hide existing annotations |
   | `hideLogo` | boolean | No | Hide the OpenMark logo |

> **Note:** When using DAT, view options (hideAnnotationsTools, hideAnnotations, hideLogo) are embedded in the token. No need to add them as query parameters.

**View Modes:**

- **Default mode**: Full annotation capabilities with toolbar and sidebar
- **Read-only mode** (`hideAnnotationsTools=true`): View annotations but cannot create/edit/delete them
- **Clean view mode** (`hideAnnotations=true`): View PDF without any annotations visible (also hides tools)
- **No branding mode** (`hideLogo=true`): Hide the OpenMark logo for embedded or white-label usage

**Example URLs:**

```
# Using DAT (Recommended - survives page refresh)
/api/viewDocument?dat=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Legacy: Full mode (default)
/api/viewDocument?tempDocumentId=temp_abc123&token=xyz

# Legacy: Read-only mode
/api/viewDocument?tempDocumentId=temp_abc123&token=xyz&hideAnnotationsTools=true

# Legacy: Clean view (no annotations)
/api/viewDocument?tempDocumentId=temp_abc123&token=xyz&hideAnnotations=true

# Legacy: Hide logo only
/api/viewDocument?tempDocumentId=temp_abc123&token=xyz&hideLogo=true

# Legacy: Clean view with no logo (embedded mode)
/api/viewDocument?tempDocumentId=temp_abc123&token=xyz&hideAnnotations=true&hideLogo=true
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
