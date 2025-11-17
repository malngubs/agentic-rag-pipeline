#!/bin/bash

###############################################################################
# Qdrant Startup Script
# This script starts Qdrant vector database and verifies it's running
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════╗"
echo "║     Qdrant Vector Database Startup Script         ║"
echo "║          Agentic RAG Pipeline                      ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if Docker is installed
echo -e "${YELLOW}[1/6]${NC} Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed!${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check if Docker Compose is installed
echo -e "${YELLOW}[2/6]${NC} Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed!${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is installed${NC}"

# Check if docker-compose.yml exists
echo -e "${YELLOW}[3/6]${NC} Checking docker-compose.yml..."
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}✗ docker-compose.yml not found!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ docker-compose.yml found${NC}"

# Create data directory if it doesn't exist
echo -e "${YELLOW}[4/6]${NC} Setting up data directories..."
mkdir -p data/qdrant
chmod -R 755 data/qdrant
echo -e "${GREEN}✓ Data directories ready${NC}"

# Check if Qdrant is already running
if docker ps | grep -q qdrant-vector-db; then
    echo -e "${YELLOW}[5/6]${NC} Qdrant is already running. Restarting..."
    docker-compose restart qdrant
else
    echo -e "${YELLOW}[5/6]${NC} Starting Qdrant..."
    docker-compose up -d qdrant
fi

# Wait for Qdrant to be ready
echo -e "${YELLOW}[6/6]${NC} Waiting for Qdrant to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:6333/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Qdrant is ready!${NC}"
        break
    fi

    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        echo -e "${RED}✗ Qdrant failed to start within 30 seconds${NC}"
        echo "Check logs with: docker-compose logs qdrant"
        exit 1
    fi

    echo -n "."
    sleep 1
done

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Qdrant is Running Successfully! 🚀         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📊 Qdrant Information:${NC}"
echo -e "   • HTTP API:  ${GREEN}http://localhost:6333${NC}"
echo -e "   • gRPC API:  ${GREEN}http://localhost:6334${NC}"
echo -e "   • Data Path: ${GREEN}./data/qdrant${NC}"
echo ""
echo -e "${BLUE}🔍 Quick Commands:${NC}"
echo -e "   • View logs:        ${YELLOW}docker-compose logs -f qdrant${NC}"
echo -e "   • Stop Qdrant:      ${YELLOW}docker-compose down${NC}"
echo -e "   • Restart Qdrant:   ${YELLOW}docker-compose restart qdrant${NC}"
echo -e "   • Check status:     ${YELLOW}docker-compose ps${NC}"
echo ""
echo -e "${BLUE}🧪 Test Connection:${NC}"
echo -e "   ${YELLOW}curl http://localhost:6333/collections${NC}"
echo ""
echo -e "${GREEN}✓ Ready for RAG operations!${NC}"
echo ""
