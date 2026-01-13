# OpenMark Development Environment

This directory contains development and testing resources for OpenMark.

## Contents

```
dev/
├── docker-compose.yml      # Docker Compose configuration for all services
├── docker/                 # Docker-related configuration files
│   ├── mongo-init/        # MongoDB initialization scripts
│   ├── postgres-init/     # PostgreSQL initialization scripts
│   └── nginx/             # Nginx configuration for PDF serving
├── generate_sample_pdf.py  # Script to generate sample PDF files
└── sample.pdf              # Sample PDF for testing
```

## Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| OpenMark | 8080 | Main application |
| MongoDB | 27017 | NoSQL database |
| Mongo Express | 8081 | MongoDB web UI |
| PostgreSQL | 5432 | SQL database |
| pgAdmin | 8082 | PostgreSQL web UI |
| MinIO | 9000/9001 | S3-compatible storage |
| FTP | 21 | FTP server |
| SFTP | 2222 | SFTP server |
| WebDAV | 8083 | WebDAV server |
| Nginx PDFs | 8084 | HTTP PDF server |

## Quick Start

```bash
# Start all services
docker-compose up -d

# Start only databases
docker-compose up -d mongodb postgres

# Start with web UIs
docker-compose up -d mongodb mongo-express postgres pgadmin

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (clean start)
docker-compose down -v
```

## Default Credentials

### MongoDB
- Admin: `admin` / `adminpassword`
- Mongo Express: `admin` / `admin123`

### PostgreSQL
- Database: `openmark` / `openmarkpassword`
- pgAdmin: `admin@openmark.local` / `admin123`

### MinIO (S3)
- Console: `minioadmin` / `minioadmin123`

### FTP/SFTP/WebDAV
- FTP: `openmark` / `openmarkftp`
- SFTP: `openmark` / `openmarksftp`
- WebDAV: `openmark` / `openmarkwebdav`

## Testing with Different Backends

Create configuration files in the project root for testing:

### config-mongodb.json
```json
{
  "plugins": {
    "authentication": {
      "type": "mongodb",
      "config": {
        "connection_string": "mongodb://admin:adminpassword@localhost:27017/",
        "database": "openmark"
      }
    }
  }
}
```

### config-postgresql.json
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
        "password": "openmarkpassword"
      }
    }
  }
}
```

## Generate Sample PDF

```bash
python3 generate_sample_pdf.py
```

This creates a sample PDF file for testing the PDF viewer functionality.
