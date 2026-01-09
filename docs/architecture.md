# OpenMark Architecture

This document describes the architecture of OpenMark and how it integrates with your existing infrastructure.

## Integration Overview

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

## Detailed Integration Flow

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

## Component Architecture

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

## Deployment Options

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

## JWT Token Architecture

OpenMark uses JWT (JSON Web Tokens) for all authentication and authorization:

### Token Types

| Token Type | Purpose | Lifetime | Usage |
|------------|---------|----------|-------|
| **AT (Authentication Token)** | API authentication after login | Configurable (default: 24h) | `Authorization: Bearer <token>` header |
| **DAT (Document Access Token)** | Document viewing access | 4× cache duration (min 2h) | URL parameter `?dat=<token>` |

### Authentication Token (AT) Structure

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

### Document Access Token (DAT) Structure

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

### How Authentication Works

```
1. User authenticates          → AT (Authentication Token) returned
2. Request document access     → DAT generated (2-hour minimum validity)
3. View document with DAT      → No AT needed for viewing
4. Page refresh (F5)           → DAT still valid ✅
5. Save annotations            → DAT authenticates the request
6. Logout                      → AT revoked via blacklist
```

## Cross-Domain and iframe Embedding

OpenMark supports cross-domain usage and iframe embedding, which is essential when:
- The authentication server is on a different domain
- The PDF viewer needs to be embedded in an external application
- Client applications display the viewer in an iframe

### Typical Integration Flow

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

### Example: Embedding in iframe

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
