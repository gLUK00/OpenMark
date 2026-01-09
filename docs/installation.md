# OpenMark Installation Guide

This guide covers all installation methods for OpenMark.

## Prerequisites

- Python 3.9 or higher
- Docker (optional, for containerized deployment)
- MongoDB (optional, for database storage)
- PostgreSQL (optional, for database storage)

## Quick Start (Development)

1. **Clone the repository**
   ```bash
   git clone https://github.com/gLUK00/OpenMark.git
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

## Docker Deployment (Recommended for Production)

### Using Docker directly

1. **Build the Docker image**
   ```bash
   docker build -t openmark:latest .
   ```

2. **Run with Docker**
   ```bash
   docker run -d -p 5000:5000 -v ./config.json:/app/config.json openmark:latest
   ```

### Using Docker Compose

1. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

### Using Official Docker Image

Pull and run the official image from Docker Hub:

```bash
docker pull gluk46546546/openmark:latest
docker run -d -p 5000:5000 -v ./config.json:/app/config.json gluk46546546/openmark:latest
```

## Docker Compose Examples

### Basic Setup (Local Storage)

```yaml
version: '3.8'

services:
  openmark:
    image: gluk46546546/openmark:latest
    ports:
      - "5000:5000"
    volumes:
      - ./config.json:/app/config.json:ro
      - ./data:/app/data
      - ./cache:/app/cache
    restart: unless-stopped
```

### With MongoDB

```yaml
version: '3.8'

services:
  openmark:
    image: gluk46546546/openmark:latest
    ports:
      - "5000:5000"
    volumes:
      - ./config.json:/app/config.json:ro
      - ./cache:/app/cache
    environment:
      - OPENMARK_SECRET_KEY=your-secret-key-here
    depends_on:
      - mongodb
    restart: unless-stopped

  mongodb:
    image: mongo:6
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped

volumes:
  mongodb_data:
```

### With PostgreSQL

```yaml
version: '3.8'

services:
  openmark:
    image: gluk46546546/openmark:latest
    ports:
      - "5000:5000"
    volumes:
      - ./config.json:/app/config.json:ro
      - ./cache:/app/cache
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=openmark
      - POSTGRES_PASSWORD=your-secure-password
      - POSTGRES_DB=openmark
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### Enterprise Setup (Full Stack)

```yaml
version: '3.8'

services:
  openmark:
    image: gluk46546546/openmark:latest
    ports:
      - "5000:5000"
    volumes:
      - ./config.json:/app/config.json:ro
      - ./cache:/app/cache
      - ./custom_plugins:/app/custom_plugins:ro
    environment:
      - OPENMARK_SECRET_KEY=${SECRET_KEY}
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_USER=openmark
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=openmark
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - openmark
    restart: unless-stopped

volumes:
  postgres_data:
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENMARK_SECRET_KEY` | JWT secret key | From config.json |
| `OPENMARK_CUSTOM_PLUGINS_DIR` | Path to custom plugins | `./custom_plugins` |

## Installing Optional Dependencies

Depending on which plugins you want to use, install additional dependencies:

```bash
# For MongoDB support
pip install pymongo

# For PostgreSQL support
pip install psycopg2-binary

# For AWS S3 support
pip install boto3

# For SFTP support
pip install paramiko

# For CMIS support
pip install cmislib

# For OAuth support
pip install requests

# For SAML support (optional)
pip install python3-saml
```

## Verifying Installation

After starting OpenMark, you can verify the installation by:

1. **Access the web interface**: Navigate to `http://localhost:5000`
2. **Check the health endpoint**: `curl http://localhost:5000/api/health`
3. **View the logs**: Check for any errors in the console or Docker logs

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process using port 5000
lsof -i :5000
# Kill the process or use a different port in config.json
```

**Permission denied on Docker volumes:**
```bash
# Ensure proper permissions
chmod -R 755 ./data ./cache
```

**MongoDB connection refused:**
- Ensure MongoDB is running
- Check the connection string in config.json
- Verify network connectivity between containers

**PostgreSQL authentication failed:**
- Verify username and password in config.json
- Ensure the database exists
- Check PostgreSQL logs for details

## Next Steps

- [Configuration Guide](configuration.md) - Configure OpenMark for your needs
- [API Usage](api_usage.md) - Learn how to integrate with the API
- [Plugin Configuration](default_plugin_configurations.md) - Configure built-in plugins
