#!/bin/bash

###############################################################################
# Qdrant Shutdown Script
# This script safely stops Qdrant vector database
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
echo "║      Qdrant Vector Database Shutdown Script        ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if Qdrant is running
if ! docker ps | grep -q qdrant-vector-db; then
    echo -e "${YELLOW}⚠ Qdrant is not currently running${NC}"
    exit 0
fi

# Ask for confirmation if data removal is requested
if [ "$1" == "--remove-data" ] || [ "$1" == "-d" ]; then
    echo -e "${RED}⚠️  WARNING: This will DELETE all vector data!${NC}"
    echo -e "Data location: ./data/qdrant"
    echo ""
    read -p "Are you sure? (type 'yes' to confirm): " confirm

    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}Cancelled. No data was deleted.${NC}"
        exit 0
    fi

    echo -e "${YELLOW}Stopping Qdrant and removing data...${NC}"
    docker-compose down -v
    rm -rf data/qdrant/*
    echo -e "${GREEN}✓ Qdrant stopped and data removed${NC}"
else
    echo -e "${YELLOW}Stopping Qdrant (data will be preserved)...${NC}"
    docker-compose down
    echo -e "${GREEN}✓ Qdrant stopped successfully${NC}"
    echo -e "${BLUE}ℹ Data is preserved in: ./data/qdrant${NC}"
fi

echo ""
echo -e "${BLUE}To restart Qdrant:${NC}"
echo -e "   ${YELLOW}./start-qdrant.sh${NC}"
echo ""
