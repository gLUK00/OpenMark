# Default Plugin Configurations

This document provides detailed configuration examples for all built-in OpenMark plugins.

## Authentication Plugins

### Local Authentication Plugin

Store users in a local JSON file. Best for development and small deployments.

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

**Users file format (`users.json`):**
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

---

### OAuth 2.0 Authentication Plugin

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

---

### SAML SSO Authentication Plugin

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

---

### MongoDB Authentication Plugin

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
        "revoked_tokens_collection": "revoked_tokens",
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
| `revoked_tokens_collection` | string | No | revoked_tokens | Revoked tokens collection (for JWT blacklist) |
| `token_expiry_hours` | number | No | 24 | JWT token validity duration |
| `create_indexes` | boolean | No | true | Auto-create indexes |

**Features:**
- ✅ JWT-based stateless authentication
- ✅ TTL index for automatic revoked token cleanup
- ✅ Distributed token revocation (logout works across instances)
- ✅ Connection pooling for performance
- ✅ Default admin/user accounts created on first run
- ✅ User management methods (create, update, deactivate)

---

### PostgreSQL Authentication Plugin

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
        "revoked_tokens_table": "revoked_tokens",
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
| `revoked_tokens_table` | string | No | revoked_tokens | Revoked tokens table (for JWT blacklist) |
| `pool_min_conn` | number | No | 1 | Minimum pool connections |
| `pool_max_conn` | number | No | 10 | Maximum pool connections |
| `create_tables` | boolean | No | true | Auto-create tables |

**Features:**
- ✅ JWT-based stateless authentication
- ✅ Connection pooling (ThreadedConnectionPool)
- ✅ Distributed token revocation (logout works across instances)
- ✅ Automatic expired revoked token cleanup
- ✅ Cascading delete (deactivating user invalidates sessions)
- ✅ Default admin/user accounts created on first run
- ✅ User management methods (create, update, deactivate)

---

## PDF Source Plugins

### HTTP PDF Source Plugin

Retrieve PDFs from any HTTP/HTTPS endpoint.

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

---

### S3 PDF Source Plugin

Retrieve PDF documents from an AWS S3 bucket or S3-compatible storage.

**Requirements:** `pip install boto3`

**Basic configuration:**
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

**IAM roles (recommended for AWS):**
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

**S3-compatible services (MinIO, LocalStack):**
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
| `prefix` | string | No | - | Key prefix for documents |
| `endpoint_url` | string | No | - | Custom S3 endpoint URL for S3-compatible services |
| `use_ssl` | boolean | No | true | Use SSL/TLS for connections |
| `verify_ssl` | boolean | No | true | Verify SSL certificates |

---

### Local Filesystem PDF Source Plugin

Retrieve PDF documents from the local filesystem.

```json
{
  "plugins": {
    "pdf_source": {
      "type": "local",
      "config": {
        "base_path": "./data/pdfs",
        "recursive": true,
        "create_base_path": true
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

---

### WebDAV PDF Source Plugin

Retrieve PDFs from WebDAV servers (Nextcloud, ownCloud, Apache mod_dav, etc.).

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

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `base_url` | string | Yes | - | WebDAV server URL (must end with /) |
| `username` | string | No | - | Username for authentication |
| `password` | string | No | - | Password for authentication |
| `prefix` | string | No | - | Path prefix for documents |
| `timeout` | number | No | 30 | Request timeout in seconds |
| `verify_ssl` | boolean | No | true | Verify SSL certificates |
| `auth_type` | string | No | basic | Authentication type: `basic` or `digest` |

---

### FTP/FTPS PDF Source Plugin

Retrieve PDFs from FTP or FTPS servers.

```json
{
  "plugins": {
    "pdf_source": {
      "type": "ftp",
      "config": {
        "host": "ftp.example.com",
        "port": 21,
        "username": "user",
        "password": "password",
        "prefix": "/documents/pdfs",
        "passive": true,
        "use_tls": false
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
| `prefix` | string | No | - | Directory path prefix |
| `passive` | boolean | No | true | Use passive mode |
| `timeout` | number | No | 30 | Connection timeout in seconds |
| `use_tls` | boolean | No | false | Use FTPS (FTP over TLS) |
| `encoding` | string | No | utf-8 | Server filename encoding |

---

### SFTP PDF Source Plugin

Retrieve PDFs from SFTP servers (SSH File Transfer Protocol).

**Requirements:** `pip install paramiko`

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

| Option | Required | Default | Description |
|--------|----------|---------|-------------|
| `host` | ✅ | - | SFTP server hostname or IP |
| `port` | ❌ | 22 | SSH port |
| `username` | ✅ | - | SSH username |
| `password` | ❌ | - | SSH password (use if no key auth) |
| `private_key_path` | ❌ | - | Path to private key file |
| `private_key_passphrase` | ❌ | - | Passphrase for encrypted private key |
| `prefix` | ❌ | `/` | Directory path prefix for documents |
| `timeout` | ❌ | 30 | Connection timeout in seconds |
| `known_hosts_path` | ❌ | - | Path to known_hosts file |
| `auto_add_host_key` | ❌ | false | Auto-add unknown host keys (dev only!) |
| `compress` | ❌ | false | Enable SSH compression |

---

### CMIS PDF Source Plugin

Retrieve PDFs from ECM systems supporting CMIS (Alfresco, Nuxeo, SharePoint, etc.).

**Requirements:** `pip install cmislib`

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

---

## Annotations Plugins

### Local Annotations Plugin

> ⚠️ **WARNING: Development/Demo Use Only**
> 
> The Local Annotations Plugin stores all annotations in a single JSON file. This approach is **NOT recommended for production** environments.

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

---

### MongoDB Annotations Plugin (Recommended)

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

---

### PostgreSQL Annotations Plugin

Store annotations in PostgreSQL using JSONB columns.

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

**Features:**
- ✅ JSONB columns for efficient JSON storage and querying
- ✅ GIN indexes for fast JSONB searches
- ✅ Connection pooling for performance
- ✅ Upsert support (INSERT ON CONFLICT)
- ✅ Additional methods: `delete_annotations()`, `get_user_documents()`, `search_notes()`, `get_statistics()`
