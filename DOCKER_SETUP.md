# 🐳 Qdrant Docker Setup Guide

This guide will help you set up and run Qdrant vector database using Docker for your Agentic RAG Pipeline.

---

## 📋 Prerequisites

- Docker installed ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (usually comes with Docker Desktop)
- At least 2GB of free disk space
- Ports 6333 and 6334 available

---

## 🚀 Quick Start

### 1. Start Qdrant

```bash
# Navigate to project root
cd /home/user/agentic-rag-pipeline

# Start Qdrant in detached mode
docker-compose up -d

# View logs
docker-compose logs -f qdrant
```

### 2. Verify Qdrant is Running

```bash
# Check container status
docker-compose ps

# Test HTTP API
curl http://localhost:6333/collections

# Expected output: {"result":{"collections":[]}}
```

### 3. Check Health Status

```bash
curl http://localhost:6333/health
```

Expected response:
```json
{
  "title": "qdrant - vector search engine",
  "version": "1.x.x"
}
```

---

## 🛠️ Common Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Stop and Remove Data (⚠️ WARNING: Deletes all vectors!)
```bash
docker-compose down -v
```

### View Logs
```bash
# Follow logs in real-time
docker-compose logs -f qdrant

# View last 100 lines
docker-compose logs --tail=100 qdrant
```

### Restart Qdrant
```bash
docker-compose restart qdrant
```

### Check Resource Usage
```bash
docker stats qdrant-vector-db
```

---

## 📊 Qdrant Web UI

Qdrant doesn't have a built-in web UI, but you can access the REST API directly:

```bash
# List all collections
curl http://localhost:6333/collections

# Get collection info
curl http://localhost:6333/collections/knowledge_base

# Check cluster info
curl http://localhost:6333/cluster
```

---

## 🔧 Configuration

### Current Setup

- **HTTP API Port**: 6333 (for REST API)
- **gRPC Port**: 6334 (for high-performance operations)
- **Storage Path**: `./data/qdrant` (persisted on host)
- **Max Request Size**: 100 MB
- **Max Workers**: 4
- **Log Level**: INFO

### Customize Configuration

Edit `docker-compose.yml` environment variables:

```yaml
environment:
  - QDRANT__SERVICE__MAX_REQUEST_SIZE_MB=200  # Increase max request size
  - QDRANT__LOG_LEVEL=DEBUG                   # More verbose logging
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

---

## 📁 Data Persistence

Vector data is stored in: `./data/qdrant/`

This directory is mounted as a volume, so your data persists across container restarts.

### Backup Data

```bash
# Stop Qdrant
docker-compose down

# Create backup
tar -czf qdrant-backup-$(date +%Y%m%d).tar.gz data/qdrant/

# Start Qdrant
docker-compose up -d
```

### Restore Data

```bash
# Stop Qdrant
docker-compose down

# Restore backup
tar -xzf qdrant-backup-YYYYMMDD.tar.gz

# Start Qdrant
docker-compose up -d
```

---

## 🐛 Troubleshooting

### Port Already in Use

If port 6333 or 6334 is already in use:

```bash
# Check what's using the port
lsof -i :6333
lsof -i :6334

# Option 1: Stop the conflicting service
# Option 2: Change port in docker-compose.yml
ports:
  - "6335:6333"  # Map to different host port
```

### Container Won't Start

```bash
# Check logs
docker-compose logs qdrant

# Check Docker daemon status
systemctl status docker

# Restart Docker
sudo systemctl restart docker
```

### Permission Denied on Data Directory

```bash
# Fix permissions
sudo chown -R $(whoami):$(whoami) data/qdrant
chmod -R 755 data/qdrant
```

### Out of Disk Space

```bash
# Check Docker disk usage
docker system df

# Clean up unused containers/images
docker system prune -a

# Remove unused volumes (⚠️ WARNING: May delete data)
docker volume prune
```

---

## 🔗 Integration with RAG System

Your RAG system (`src/rag_components.py`) connects to Qdrant using these settings:

```python
# Default configuration
qdrant_host = "localhost"
qdrant_port = 6333
collection_name = "knowledge_base"
```

If you change ports in `docker-compose.yml`, update `src/rag_components.py` accordingly.

---

## 📈 Monitoring

### Check Collection Stats

```bash
curl http://localhost:6333/collections/knowledge_base
```

Response includes:
- Number of vectors
- Vector size
- Distance metric
- Number of segments

### View Telemetry

```bash
curl http://localhost:6333/telemetry
```

Shows:
- Memory usage
- Query performance
- Storage statistics

---

## 🔐 Security Notes

### Development Setup (Current)

- ✅ Running on localhost only
- ✅ No authentication required
- ❌ Not exposed to internet

### Production Recommendations

1. **Enable API Key Authentication**:
   ```yaml
   environment:
     - QDRANT__SERVICE__API_KEY=your-secret-api-key
   ```

2. **Use HTTPS with Reverse Proxy**:
   - Set up Nginx or Traefik
   - Add SSL certificates

3. **Network Isolation**:
   - Keep Qdrant in private network
   - Only expose through application server

4. **Regular Backups**:
   - Automate backup script
   - Store offsite

---

## 🚦 Testing the Setup

Run this test to verify everything works:

```bash
# Create a test collection
curl -X PUT http://localhost:6333/collections/test \
  -H 'Content-Type: application/json' \
  -d '{
    "vectors": {
      "size": 384,
      "distance": "Cosine"
    }
  }'

# Insert a test vector
curl -X PUT http://localhost:6333/collections/test/points \
  -H 'Content-Type: application/json' \
  -d '{
    "points": [
      {
        "id": 1,
        "vector": [0.1, 0.2, 0.3, ...],
        "payload": {"test": "data"}
      }
    ]
  }'

# Search
curl -X POST http://localhost:6333/collections/test/points/search \
  -H 'Content-Type: application/json' \
  -d '{
    "vector": [0.1, 0.2, 0.3, ...],
    "limit": 5
  }'

# Delete test collection
curl -X DELETE http://localhost:6333/collections/test
```

---

## 📚 Additional Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Qdrant Docker Hub](https://hub.docker.com/r/qdrant/qdrant)
- [Qdrant GitHub](https://github.com/qdrant/qdrant)
- [REST API Reference](https://qdrant.tech/documentation/interfaces/)

---

## 🎯 Next Steps

After Qdrant is running:

1. ✅ Create `.env` file with `OPENAI_API_KEY`
2. ✅ Start your FastAPI server: `cd src && python main_production_with_rag.py`
3. ✅ Upload documents via admin panel: `http://localhost:8000/admin.html`
4. ✅ Test chat widget: `http://localhost:8000`

---

**Questions?** Check the logs first: `docker-compose logs -f qdrant`
