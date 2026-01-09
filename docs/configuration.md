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
