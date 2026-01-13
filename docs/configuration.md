# OpenMark Configuration Guide

OpenMark uses a `config.json` file for all configuration settings.

## Basic Configuration

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

## Server Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `host` | string | `0.0.0.0` | Server bind address |
| `port` | number | `5000` | Server port |
| `debug` | boolean | `false` | Enable debug mode (development only) |
| `secret_key` | string | **required** | Secret key for JWT signing |

### CORS Configuration

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

## Cache Configuration

```json
{
  "cache": {
    "directory": "./cache",
    "duration_seconds": 3600
  }
}
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `directory` | string | `./cache` | Directory for cached PDFs |
| `duration_seconds` | number | `3600` | Cache duration in seconds |

> **Note:** DAT (Document Access Token) validity is automatically calculated as **4× the cache duration**, with a minimum of 2 hours.

## Plugin Configuration

OpenMark uses a plugin system for:
- **Authentication** - How users are authenticated
- **PDF Source** - Where PDFs are retrieved from
- **Annotations** - Where annotations are stored

### Plugin Structure

```json
{
  "plugins": {
    "authentication": {
      "type": "plugin_name",
      "config": {
        // Plugin-specific configuration
      }
    },
    "pdf_source": {
      "type": "plugin_name",
      "config": {
        // Plugin-specific configuration
      }
    },
    "annotations": {
      "type": "plugin_name",
      "config": {
        // Plugin-specific configuration
      }
    }
  }
}
```

For detailed plugin configurations, see [Default Plugin Configurations](default_plugin_configurations.md).

## Customization

```json
{
  "customization": {
    "script_file": "/path/to/custom.js",
    "logo_url": "https://example.com/logo.png",
    "primary_color": "#007bff"
  }
}
```

| Setting | Type | Description |
|---------|------|-------------|
| `script_file` | string | Path to custom JavaScript file |
| `logo_url` | string | URL or path to custom logo |
| `primary_color` | string | Primary color for UI elements |

## Environment Variables

Configuration values can be overridden with environment variables:

| Variable | Description |
|----------|-------------|
| `OPENMARK_SECRET_KEY` | Override `server.secret_key` |
| `OPENMARK_CUSTOM_PLUGINS_DIR` | Path to custom plugins directory |

## Configuration Examples

### Development Configuration

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 5000,
    "debug": true,
    "secret_key": "dev-secret-key"
  },
  "cache": {
    "directory": "./cache",
    "duration_seconds": 300
  },
  "plugins": {
    "authentication": {
      "type": "local",
      "config": {
        "users_file": "./data/users.json"
      }
    },
    "pdf_source": {
      "type": "local",
      "config": {
        "base_path": "./data/pdfs"
      }
    },
    "annotations": {
      "type": "local",
      "config": {
        "storage_path": "./data/annotations.json"
      }
    }
  }
}
```

### Production Configuration (MongoDB)

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "secret_key": "your-production-secret-key-min-32-chars",
    "cors": {
      "allowed_origins": ["https://your-app.com"],
      "allow_iframe_embedding": true
    }
  },
  "cache": {
    "directory": "./cache",
    "duration_seconds": 3600
  },
  "plugins": {
    "authentication": {
      "type": "mongodb",
      "config": {
        "connection_string": "mongodb://mongo:27017",
        "database": "openmark",
        "token_expiry_hours": 24
      }
    },
    "pdf_source": {
      "type": "s3",
      "config": {
        "bucket_name": "company-documents",
        "region_name": "eu-west-1",
        "prefix": "pdfs/"
      }
    },
    "annotations": {
      "type": "mongodb",
      "config": {
        "connection_string": "mongodb://mongo:27017",
        "database": "openmark",
        "collection": "annotations"
      }
    }
  }
}
```

### Enterprise Configuration (PostgreSQL + SAML)

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "secret_key": "your-enterprise-secret-key-min-32-chars",
    "cors": {
      "allowed_origins": ["https://intranet.company.com"],
      "allow_iframe_embedding": true
    }
  },
  "cache": {
    "directory": "./cache",
    "duration_seconds": 7200
  },
  "plugins": {
    "authentication": {
      "type": "saml",
      "config": {
        "idp_entity_id": "https://idp.company.com/saml/metadata",
        "idp_sso_url": "https://idp.company.com/saml/sso",
        "idp_x509_cert": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
        "sp_entity_id": "https://openmark.company.com/saml/metadata",
        "sp_acs_url": "https://openmark.company.com/api/saml/acs",
        "token_expiry_hours": 8,
        "role_mapping": {
          "Administrators": "admin",
          "Users": "user"
        }
      }
    },
    "pdf_source": {
      "type": "cmis",
      "config": {
        "url": "https://ecm.company.com/alfresco/api/-default-/public/cmis/versions/1.1/browser",
        "username": "openmark-service",
        "password": "service-password",
        "root_folder_path": "/Sites/documents"
      }
    },
    "annotations": {
      "type": "postgresql",
      "config": {
        "host": "postgres.company.com",
        "database": "openmark",
        "user": "openmark",
        "password": "db-password",
        "pool_max_conn": 20
      }
    }
  }
}
```

## User Management Scripts

OpenMark provides command-line scripts for managing users in the authentication database. These scripts **automatically use the backend configured** in `config.json` (local, MongoDB, or PostgreSQL).

For complete documentation, see [Scripts Administration](scripts_administration.md).

### Supported Backends

| Backend | Configuration Type | Requirements |
|---------|-------------------|--------------|
| Local JSON file | `local` | None |
| MongoDB | `mongodb` | `pip install pymongo` |
| PostgreSQL | `postgresql` | `pip install psycopg2-binary` |

### List Users

```bash
# Display all users (table format)
python3 scripts/user_list.py

# Filter by role
python3 scripts/user_list.py --role admin
python3 scripts/user_list.py --role user

# Export as JSON
python3 scripts/user_list.py --format json

# Export as CSV
python3 scripts/user_list.py --format csv > users.csv

# Use specific configuration file
python3 scripts/user_list.py -c ./config-production.json
```

### Create User

```bash
# Create a standard user
python3 scripts/user_create.py -u john -p secret123

# Create an administrator
python3 scripts/user_create.py -u admin2 -p adminpass -r admin

# With email (MongoDB/PostgreSQL)
python3 scripts/user_create.py -u john -p secret123 -e john@example.com

# Interactive password entry (recommended for security)
python3 scripts/user_create.py -u john
```

| Option | Description |
|--------|-------------|
| `-u, --username` | Username (required) |
| `-p, --password` | Password (optional, prompted if not provided) |
| `-r, --role` | User role: `admin` or `user` (default: `user`) |
| `-e, --email` | User email (optional, supported by MongoDB/PostgreSQL) |
| `-c, --config` | Path to configuration file (default: `config.json`) |

### Modify User

```bash
# Change password
python3 scripts/user_modify.py -u john -p newpassword123

# Change role
python3 scripts/user_modify.py -u john -r admin

# Change username
python3 scripts/user_modify.py -u john --new-username johnny

# Change email
python3 scripts/user_modify.py -u john -e john@newdomain.com

# Multiple changes at once
python3 scripts/user_modify.py -u john -p newpass -r admin --new-username johnny
```

| Option | Description |
|--------|-------------|
| `-u, --username` | Current username (required) |
| `-p, --password` | New password |
| `-r, --role` | New role: `admin` or `user` |
| `--new-username` | New username |
| `-e, --email` | New email |
| `-c, --config` | Path to configuration file |

### Delete User

```bash
# Delete with confirmation
python3 scripts/user_delete.py -u john

# Delete without confirmation
python3 scripts/user_delete.py -u john --force
```

| Option | Description |
|--------|-------------|
| `-u, --username` | Username to delete (required) |
| `--force, -y` | Skip confirmation prompt |
| `-c, --config` | Path to configuration file |

> **Note:** The last administrator cannot be deleted to prevent lockout.

### Security Best Practices

- Use interactive password entry (`-p` without value) to avoid passwords in shell history
- Restrict file permissions on configuration files:
  ```bash
  chmod 600 config.json
  chmod 600 data/users.json
  ```
- Passwords are hashed with SHA-256 before storage

## Annotations Import/Export Scripts

OpenMark provides command-line scripts for importing and exporting annotations. These scripts **automatically use the backend configured** in `config.json` (local, MongoDB, or PostgreSQL).

For complete documentation, see [Annotations Import/Export](annotations_import.md).

### Export Annotations

```bash
# Export a specific document
python3 scripts/annotations_export.py -u admin -d report-2026 -o export.json

# Export all documents for a user
python3 scripts/annotations_export.py -u admin --all -o backup.json

# Output to stdout (for piping)
python3 scripts/annotations_export.py -u admin -d doc1 | jq .
```

### Import Annotations

```bash
# Import from file (multi-user format)
python3 scripts/annotations_import.py -f export.json

# Import to specific user/document
python3 scripts/annotations_import.py -f notes.json -u admin -d report-2026

# Replace existing annotations
python3 scripts/annotations_import.py -f export.json --mode replace

# Validate without importing
python3 scripts/annotations_import.py -f export.json --dry-run
```

### JSON Format

```json
{
  "version": "1.0",
  "data": [
    {
      "user_id": "admin",
      "document_id": "report-2026",
      "annotations": {
        "notes": [
          {"page": 1, "x": 100, "y": 200, "content": "Note text", "color": "#ffff00"}
        ],
        "highlights": [
          {"page": 1, "rects": [{"x": 50, "y": 100, "width": 300, "height": 20}], "color": "#00ff00"}
        ]
      }
    }
  ]
}
```

## Docker Compose Development Environment

OpenMark provides a complete Docker Compose setup for development and testing with all supported backends. The Docker Compose configuration is located in the `dev/` directory.

### Available Services

| Service | Port | Description | Credentials |
|---------|------|-------------|-------------|
| OpenMark | 8080 | Main application | - |
| MongoDB | 27017 | NoSQL database | admin / adminpassword |
| Mongo Express | 8081 | MongoDB web UI | admin / admin123 |
| PostgreSQL | 5432 | SQL database | openmark / openmarkpassword |
| pgAdmin | 8082 | PostgreSQL web UI | admin@openmark.local / admin123 |
| MinIO | 9000/9001 | S3-compatible storage | minioadmin / minioadmin123 |
| FTP | 21 | FTP server | openmark / openmarkftp |
| SFTP | 2222 | SFTP server | openmark / openmarksftp |
| WebDAV | 8083 | WebDAV server | openmark / openmarkwebdav |
| Nginx PDFs | 8084 | HTTP PDF server | - |

### Quick Start

```bash
# Navigate to the dev directory
cd dev

# Start all services
docker-compose up -d

# Start only specific services
docker-compose up -d mongodb mongo-express
docker-compose up -d postgres pgadmin

# View logs
docker-compose logs -f openmark

# Stop all services
docker-compose down

# Stop and remove volumes (clean start)
docker-compose down -v
```

### Configuration Files for Testing

Create configuration files for each backend:

**config-mongodb.json:**
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "secret_key": "your-secret-key"
  },
  "plugins": {
    "authentication": {
      "type": "mongodb",
      "config": {
        "connection_string": "mongodb://admin:adminpassword@localhost:27017/",
        "database": "openmark"
      }
    },
    "annotations": {
      "type": "mongodb",
      "config": {
        "connection_string": "mongodb://admin:adminpassword@localhost:27017/",
        "database": "openmark"
      }
    },
    "pdf_source": {
      "type": "http",
      "config": {
        "base_url": "http://localhost:8084/"
      }
    }
  }
}
```

**config-postgresql.json:**
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "secret_key": "your-secret-key"
  },
  "plugins": {
    "authentication": {
      "type": "postgresql",
      "config": {
        "host": "localhost",
        "port": 5432,
        "database": "openmark",
        "user": "openmark",
        "password": "openmarkpassword"
      }
    },
    "annotations": {
      "type": "postgresql",
      "config": {
        "host": "localhost",
        "port": 5432,
        "database": "openmark",
        "user": "openmark",
        "password": "openmarkpassword"
      }
    },
    "pdf_source": {
      "type": "s3",
      "config": {
        "endpoint_url": "http://localhost:9000",
        "bucket_name": "pdfs",
        "aws_access_key_id": "minioadmin",
        "aws_secret_access_key": "minioadmin123"
      }
    }
  }
}
```

### Testing with Scripts

```bash
# Test with MongoDB backend
python3 scripts/user_list.py -c config-mongodb.json
python3 scripts/user_create.py -c config-mongodb.json -u testuser -p test123

# Test with PostgreSQL backend
python3 scripts/user_list.py -c config-postgresql.json
python3 scripts/user_create.py -c config-postgresql.json -u testuser -p test123
```

## Security Recommendations

1. **Use a strong secret key** - At least 32 characters, randomly generated
2. **Restrict CORS origins** - Don't use `"*"` in production
3. **Use HTTPS** - Deploy behind a reverse proxy with SSL
4. **Secure database credentials** - Use environment variables or secrets management
5. **Enable debug only in development** - Never in production

## Next Steps

- [Default Plugin Configurations](default_plugin_configurations.md) - Detailed plugin setup
- [API Usage](api_usage.md) - Learn the API
- [Developing Plugins](developing_plugins.md) - Create custom plugins
