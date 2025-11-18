#!/bin/bash
# Lucia AI Setup Script for dis_maops

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Lucia AI root
LUCIA_ROOT="/Users/darylharr/Desktop/dis_maops/lucia_ai"
cd "$LUCIA_ROOT"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Lucia AI Setup for dis_maops                         ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓${NC} pip upgraded"

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓${NC} Python dependencies installed"
else
    echo -e "${YELLOW}⚠${NC}  requirements.txt not found, skipping Python dependencies"
fi

# Install Node.js dependencies for OpenAI integration
if [ -d "integrations/openai" ]; then
    echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
    cd integrations/openai
    if [ -f "package.json" ]; then
        npm install > /dev/null 2>&1
        echo -e "${GREEN}✓${NC} Node.js dependencies installed"
    fi
    cd "$LUCIA_ROOT"
fi

# Create required directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p logs data models cache data/personalities
echo -e "${GREEN}✓${NC} Directories created"

# Copy environment template if .env doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.template .env
    echo -e "${GREEN}✓${NC} .env file created"
    echo -e "${YELLOW}⚠${NC}  ${RED}IMPORTANT:${NC} Please edit .env and add your API keys"
else
    echo -e "${GREEN}✓${NC} .env file already exists"
fi

# Initialize vector database (if Qdrant is running)
echo -e "${YELLOW}Checking Qdrant connection...${NC}"
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Qdrant is running"
    echo -e "${YELLOW}Initializing vector store...${NC}"
    python3 -c "
from memory.vector_store import init_qdrant
try:
    init_qdrant()
    print('${GREEN}✓${NC} Vector store initialized')
except Exception as e:
    print('${YELLOW}⚠${NC}  Could not initialize vector store:', str(e))
" 2>/dev/null || echo -e "${YELLOW}⚠${NC}  Vector store initialization skipped"
else
    echo -e "${YELLOW}⚠${NC}  Qdrant not running (optional, start with: docker run -p 6333:6333 qdrant/qdrant)"
fi

# Check Redis connection
echo -e "${YELLOW}Checking Redis connection...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is running"
else
    echo -e "${YELLOW}⚠${NC}  Redis not running (optional, start with: redis-server)"
fi

# Check Ollama
echo -e "${YELLOW}Checking Ollama...${NC}"
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Ollama is running"
else
    echo -e "${YELLOW}⚠${NC}  Ollama not running (start with: ollama serve)"
fi

# Add shell aliases recommendation
echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Setup Complete!                                       ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. ${YELLOW}Edit .env${NC} and add your API keys"
echo -e "  2. ${YELLOW}lucia-start${NC} to start all services"
echo -e "  3. ${YELLOW}lucia-test${NC} to run tests"
echo ""
echo -e "${BLUE}Recommended: Add these aliases to your ~/.zshrc or ~/.bashrc:${NC}"
echo ""
echo -e "${YELLOW}export LUCIA_AI_ROOT=\"$LUCIA_ROOT\"${NC}"
echo -e "${YELLOW}alias lucia-start=\"\$LUCIA_AI_ROOT/scripts/start_lucia.sh\"${NC}"
echo -e "${YELLOW}alias lucia-stop=\"\$LUCIA_AI_ROOT/scripts/stop_lucia.sh\"${NC}"
echo -e "${YELLOW}alias lucia-test=\"\$LUCIA_AI_ROOT/scripts/test_lucia.sh\"${NC}"
echo -e "${YELLOW}alias lucia-logs=\"tail -f \$LUCIA_AI_ROOT/logs/lucia.log\"${NC}"
echo -e "${YELLOW}alias lucia=\"cd \$LUCIA_AI_ROOT\"${NC}"
echo -e "${YELLOW}alias lucia-venv=\"source \$LUCIA_AI_ROOT/.venv/bin/activate\"${NC}"
echo ""
echo -e "${GREEN}✨ Lucia AI is ready!${NC}"
