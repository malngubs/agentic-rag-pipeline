# Multi-stage Dockerfile for Agentic RAG Pipeline
# This creates an optimized production-ready container

# Stage 1: Base Python environment with dependencies
FROM python:3.11-slim as base

# Set environment variables for Python optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    libmagic1 \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Development environment
FROM base as development

# Install development dependencies
RUN pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy

# Copy application code
COPY --chown=app:app . .

# Switch to non-root user
USER app

# Expose ports
EXPOSE 8000 9090

# Development command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Stage 3: Production environment
FROM base as production

# Copy only necessary files
COPY --chown=app:app src/ ./src/
COPY --chown=app:app frontend/ ./frontend/
COPY --chown=app:app .env.example .env
COPY --chown=app:app scripts/ ./scripts/

# Create data directories
RUN mkdir -p data/qdrant data/documents data/cache data/logs && \
    chown -R app:app data/

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000 9090

# Production command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Stage 4: Testing environment
FROM development as testing

# Copy test files
COPY --chown=app:app tests/ ./tests/

# Run tests by default
CMD ["pytest", "tests/", "-v", "--cov=src", "--cov-report=html"]

# Default stage
FROM development