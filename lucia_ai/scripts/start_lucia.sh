#!/bin/bash
# Start Lucia AI Services

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

LUCIA_ROOT="/Users/darylharr/Desktop/dis_maops/lucia_ai"
cd "$LUCIA_ROOT"

# Load environment
if [ -f ".env" ]; then
    source .env
else
    echo -e "${RED}✗${NC} .env file not found. Run ./scripts/setup.sh first"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Starting Lucia AI Services                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Create PID directory
mkdir -p "$LUCIA_ROOT/pids"

# Start Basic Agent Server
echo -e "${YELLOW}Starting Basic Agent Server (port 8090)...${NC}"
if [ -f "pids/agent_server.pid" ]; then
    echo -e "${YELLOW}⚠${NC}  Agent server may already be running"
else
    cd agents
    python3 agent_server.py > "$LUCIA_ROOT/logs/agent_server.log" 2>&1 &
    echo $! > "$LUCIA_ROOT/pids/agent_server.pid"
    cd "$LUCIA_ROOT"
    echo -e "${GREEN}✓${NC} Agent server started (PID: $(cat pids/agent_server.pid))"
fi

# Start OpenAI Agent Server
echo -e "${YELLOW}Starting OpenAI Agent Server (port 8091)...${NC}"
if [ -f "pids/openai_agent_server.pid" ]; then
    echo -e "${YELLOW}⚠${NC}  OpenAI agent server may already be running"
else
    cd agents
    python3 openai_agent_server.py > "$LUCIA_ROOT/logs/openai_agent_server.log" 2>&1 &
    echo $! > "$LUCIA_ROOT/pids/openai_agent_server.pid"
    cd "$LUCIA_ROOT"
    echo -e "${GREEN}✓${NC} OpenAI agent server started (PID: $(cat pids/openai_agent_server.pid))"
fi

# Start OpenAI Integration Server (if exists)
if [ -d "integrations/openai" ] && [ -f "integrations/openai/server.js" ]; then
    echo -e "${YELLOW}Starting OpenAI Integration Server (port 3000)...${NC}"
    if [ -f "pids/openai_integration.pid" ]; then
        echo -e "${YELLOW}⚠${NC}  OpenAI integration may already be running"
    else
        cd integrations/openai
        npm start > "$LUCIA_ROOT/logs/openai_integration.log" 2>&1 &
        echo $! > "$LUCIA_ROOT/pids/openai_integration.pid"
        cd "$LUCIA_ROOT"
        echo -e "${GREEN}✓${NC} OpenAI integration started (PID: $(cat pids/openai_integration.pid))"
    fi
fi

# Wait a moment for servers to start
sleep 2

# Check health
echo ""
echo -e "${YELLOW}Checking service health...${NC}"

# Check agent server
if curl -s http://localhost:8090/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Agent server is healthy"
else
    echo -e "${RED}✗${NC} Agent server health check failed"
fi

# Check OpenAI agent server
if curl -s http://localhost:8091/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} OpenAI agent server is healthy"
else
    echo -e "${RED}✗${NC} OpenAI agent server health check failed"
fi

# Check OpenAI integration
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} OpenAI integration is healthy"
else
    echo -e "${YELLOW}⚠${NC}  OpenAI integration not available"
fi

echo ""
echo -e "${GREEN}✨ Lucia AI services are running!${NC}"
echo ""
echo -e "${BLUE}Service URLs:${NC}"
echo -e "  Agent Server:         ${YELLOW}http://localhost:8090${NC}"
echo -e "  OpenAI Agent Server:  ${YELLOW}http://localhost:8091${NC}"
echo -e "  OpenAI Integration:   ${YELLOW}http://localhost:3000${NC}"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo -e "  ${YELLOW}lucia-logs${NC} or ${YELLOW}tail -f $LUCIA_ROOT/logs/*.log${NC}"
echo ""
echo -e "${BLUE}Stop services:${NC}"
echo -e "  ${YELLOW}lucia-stop${NC}"
