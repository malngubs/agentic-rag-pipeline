#!/bin/bash

###############################################################################
# System Verification Script
# Verifies that all components of the RAG system are properly configured
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════╗"
echo "║    Agentic RAG Pipeline - System Verification      ║"
echo "╚════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

total_checks=0
passed_checks=0
failed_checks=0

# Function to print check result
check_result() {
    local name="$1"
    local status="$2"
    local message="$3"

    total_checks=$((total_checks + 1))

    if [ "$status" == "pass" ]; then
        echo -e "${GREEN}✓${NC} $name"
        [ -n "$message" ] && echo -e "  ${BLUE}→${NC} $message"
        passed_checks=$((passed_checks + 1))
    elif [ "$status" == "warn" ]; then
        echo -e "${YELLOW}⚠${NC} $name"
        [ -n "$message" ] && echo -e "  ${YELLOW}→${NC} $message"
    else
        echo -e "${RED}✗${NC} $name"
        [ -n "$message" ] && echo -e "  ${RED}→${NC} $message"
        failed_checks=$((failed_checks + 1))
    fi
}

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🐳 Docker Environment${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check Docker
if command -v docker &> /dev/null; then
    version=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    check_result "Docker installed" "pass" "Version: $version"
else
    check_result "Docker installed" "fail" "Docker is not installed"
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    version=$(docker-compose --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    check_result "Docker Compose installed" "pass" "Version: $version"
else
    check_result "Docker Compose installed" "fail" "Docker Compose is not installed"
fi

# Check if Qdrant container is running
if docker ps | grep -q qdrant-vector-db; then
    check_result "Qdrant container running" "pass" "Container: qdrant-vector-db"
else
    check_result "Qdrant container running" "fail" "Run: ./start-qdrant.sh"
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🔌 Service Connectivity${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check Qdrant HTTP API
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    version=$(curl -s http://localhost:6333/health | grep -oP '"version":"[^"]+' | cut -d'"' -f4)
    check_result "Qdrant HTTP API (port 6333)" "pass" "Version: $version"
else
    check_result "Qdrant HTTP API (port 6333)" "fail" "Cannot connect to Qdrant"
fi

# Check Qdrant collections
if curl -s http://localhost:6333/collections > /dev/null 2>&1; then
    collections=$(curl -s http://localhost:6333/collections | grep -oP '"collections":\[\K[^]]+' | grep -o '"[^"]*"' | wc -l)
    check_result "Qdrant collections endpoint" "pass" "Collections: $collections"
else
    check_result "Qdrant collections endpoint" "fail" "Cannot access collections"
fi

# Check if FastAPI server is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    check_result "FastAPI server (port 8000)" "pass" "Server is running"
else
    check_result "FastAPI server (port 8000)" "warn" "Server not running (this is OK if not started yet)"
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}📁 File System${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check .env file
if [ -f ".env" ]; then
    if grep -q "OPENAI_API_KEY" .env && ! grep -q "your-openai-api-key-here" .env; then
        check_result ".env file configured" "pass" "OpenAI API key is set"
    else
        check_result ".env file configured" "fail" "OpenAI API key not set in .env"
    fi
else
    check_result ".env file exists" "fail" "Create .env with OPENAI_API_KEY"
fi

# Check docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    check_result "docker-compose.yml exists" "pass"
else
    check_result "docker-compose.yml exists" "fail"
fi

# Check data directory
if [ -d "data/qdrant" ]; then
    size=$(du -sh data/qdrant 2>/dev/null | cut -f1)
    check_result "Qdrant data directory" "pass" "Size: $size"
else
    check_result "Qdrant data directory" "fail" "Directory missing"
fi

# Check source files
if [ -f "src/main_production_with_rag.py" ]; then
    check_result "Main application file" "pass" "src/main_production_with_rag.py"
else
    check_result "Main application file" "fail" "src/main_production_with_rag.py not found"
fi

if [ -f "src/rag_components.py" ]; then
    check_result "RAG components file" "pass" "src/rag_components.py"
else
    check_result "RAG components file" "fail" "src/rag_components.py not found"
fi

# Check static files
if [ -f "static/macrocomm-bubble.js" ]; then
    check_result "Chat widget file" "pass" "static/macrocomm-bubble.js"
else
    check_result "Chat widget file" "fail" "static/macrocomm-bubble.js not found"
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}🐍 Python Environment${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check Python
if command -v python3 &> /dev/null; then
    version=$(python3 --version | grep -oP '\d+\.\d+\.\d+')
    check_result "Python 3 installed" "pass" "Version: $version"
else
    check_result "Python 3 installed" "fail" "Python 3 not found"
fi

# Check pip
if command -v pip3 &> /dev/null; then
    check_result "pip3 installed" "pass"
else
    check_result "pip3 installed" "fail"
fi

# Check requirements file
if [ -f "requirements.txt" ]; then
    packages=$(wc -l < requirements.txt)
    check_result "requirements.txt exists" "pass" "$packages packages listed"
else
    check_result "requirements.txt exists" "warn" "No requirements.txt found"
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}📊 Summary${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "Total Checks:  ${BLUE}$total_checks${NC}"
echo -e "Passed:        ${GREEN}$passed_checks${NC}"
echo -e "Failed:        ${RED}$failed_checks${NC}"
echo ""

# Calculate success rate
if [ $total_checks -gt 0 ]; then
    success_rate=$((passed_checks * 100 / total_checks))

    if [ $failed_checks -eq 0 ]; then
        echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║     ✓ All systems operational! (100%)             ║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${GREEN}🚀 Ready to start your RAG system!${NC}"
        echo ""
        echo -e "${BLUE}Next steps:${NC}"
        echo -e "  1. Start the server:   ${YELLOW}cd src && python main_production_with_rag.py${NC}"
        echo -e "  2. Open admin panel:   ${YELLOW}http://localhost:8000/admin.html${NC}"
        echo -e "  3. Upload documents"
        echo -e "  4. Test the chatbot:   ${YELLOW}http://localhost:8000${NC}"
    elif [ $success_rate -ge 80 ]; then
        echo -e "${YELLOW}╔════════════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║     ⚠ System mostly ready ($success_rate%)                  ║${NC}"
        echo -e "${YELLOW}╚════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${YELLOW}⚠ Some components need attention. Review failed checks above.${NC}"
    else
        echo -e "${RED}╔════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║     ✗ System not ready ($success_rate%)                     ║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${RED}❌ Multiple components are missing or misconfigured.${NC}"
        echo -e "Please fix the failed checks above before proceeding."
    fi
else
    echo -e "${RED}No checks performed${NC}"
fi

echo ""
