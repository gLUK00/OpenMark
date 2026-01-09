# Dockerfile for OpenMark
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    FLASK_APP=app \
    FLASK_ENV=production \
    OPENMARK_CUSTOM_PLUGINS_DIR=/app/custom_plugins

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . ./

# Ensure the startup script is executable and set permissions for OpenShift compatibility
RUN chgrp -R 0 /app && \
    chmod -R g=u /app

# Create necessary directories (including custom plugins)
RUN mkdir -p /app/cache /app/data/pdfs /app/custom_plugins/auth /app/custom_plugins/pdf_source /app/custom_plugins/annotations

# Expose port
EXPOSE 8080

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "run:app"]
