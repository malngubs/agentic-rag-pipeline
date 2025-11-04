#!/usr/bin/env python3
"""
Production Deployment Configuration
Docker, environment variables, and production settings
"""

import os
from pathlib import Path

def create_dockerfile():
    """Create Dockerfile for containerization"""
    dockerfile_content = """
# Multi-stage build for production
FROM python:3.11-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY frontend/ ./frontend/

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \\
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "src/main_production.py"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    return "Dockerfile"

def create_docker_compose():
    """Create Docker Compose for full stack"""
    compose_content = """
version: '3.8'

services:
  # Main Application
  macrocomm-ai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
      - OLLAMA_HOST=http://ollama:11434
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    depends_on:
      - qdrant
      - ollama
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Vector Database
  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  # Local LLM Service
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    environment:
      - OLLAMA_ORIGINS=*

  # Reverse Proxy (Optional)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - macrocomm-ai
    restart: unless-stopped

volumes:
  qdrant_data:
  ollama_data:

networks:
  default:
    name: macrocomm-network
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(compose_content)
    
    return "docker-compose.yml"

def create_env_template():
    """Create environment variables template"""
    env_content = """
# Production Environment Variables
# Copy to .env and fill in your values

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=info
SECRET_KEY=your-super-secret-key-here
DEBUG=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["https://yourdomain.com"]

# Database Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=optional-api-key

# LLM Configuration
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=llama2
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2048

# Authentication (Optional)
ENABLE_AUTH=false
JWT_SECRET=your-jwt-secret
JWT_EXPIRY_HOURS=24

# File Upload Settings
MAX_FILE_SIZE_MB=10
ALLOWED_FILE_TYPES=["pdf","docx","txt"]
UPLOAD_FOLDER=./data/uploads

# Rate Limiting
RATE_LIMIT_RPM=60
RATE_LIMIT_BURST=10

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
ENABLE_HEALTH_CHECK=true

# SSL/TLS (Production)
SSL_CERT_PATH=/etc/ssl/certs/cert.pem
SSL_KEY_PATH=/etc/ssl/private/key.pem
FORCE_HTTPS=true
"""
    
    with open(".env.template", "w") as f:
        f.write(env_content)
    
    return ".env.template"

def create_production_requirements():
    """Create production requirements.txt"""
    requirements_content = """
# Core FastAPI Dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# AI/ML Dependencies  
ollama==0.1.7
qdrant-client==1.6.9
sentence-transformers==2.2.2
numpy==1.24.3
torch==2.1.0

# Document Processing
PyPDF2==3.0.1
python-docx==0.8.11
openpyxl==3.1.2

# Utility Libraries
aiofiles==23.2.1
httpx==0.25.2
pydantic==2.5.0
pydantic-settings==2.1.0

# Production Dependencies
prometheus-client==0.19.0
structlog==23.2.0
gunicorn==21.2.0
psutil==5.9.6

# Development Dependencies (remove for production)
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements_content)
    
    return "requirements.txt"

def create_nginx_config():
    """Create nginx reverse proxy configuration"""
    nginx_content = """
events {
    worker_connections 1024;
}

http {
    upstream macrocomm_ai {
        server macrocomm-ai:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
    limit_req_zone $binary_remote_addr zone=websocket:10m rate=30r/m;

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/ssl/certs/cert.pem;
        ssl_certificate_key /etc/ssl/certs/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        
        # Security Headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Gzip Compression
        gzip on;
        gzip_types text/plain text/css application/json application/javascript;

        # API Routes
        location /api/ {
            limit_req zone=api burst=10 nodelay;
            proxy_pass http://macrocomm_ai;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket Routes
        location /ws/ {
            limit_req zone=websocket burst=5 nodelay;
            proxy_pass http://macrocomm_ai;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 86400;
        }

        # Static Files
        location /frontend/ {
            proxy_pass http://macrocomm_ai;
            proxy_set_header Host $host;
            expires 7d;
            add_header Cache-Control "public, immutable";
        }

        # Health Check
        location /health {
            proxy_pass http://macrocomm_ai;
            access_log off;
        }

        # Default Route
        location / {
            proxy_pass http://macrocomm_ai;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
"""
    
    with open("nginx.conf", "w") as f:
        f.write(nginx_content)
    
    return "nginx.conf"

if __name__ == "__main__":
    print("🐳 Creating production deployment configuration...")
    
    files_created = []
    files_created.append(create_dockerfile())
    files_created.append(create_docker_compose())
    files_created.append(create_env_template())
    files_created.append(create_production_requirements())
    files_created.append(create_nginx_config())
    
    print(f"✅ Created {len(files_created)} deployment files:")
    for file in files_created:
        print(f"   - {file}")
    
    print("\n🚀 Production deployment ready!")
    print("\n📋 To deploy:")
    print("1. Copy .env.template to .env and configure")
    print("2. Get SSL certificates for production")
    print("3. Run: docker-compose up -d")
    print("4. Access your app at https://yourdomain.com")