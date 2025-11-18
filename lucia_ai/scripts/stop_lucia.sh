#!/bin/bash
# Stop Lucia AI Services

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

LUCIA_ROOT="/Users/darylharr/Desktop/dis_maops/lucia_ai"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Stopping Lucia AI Services                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Stop services
for pidfile in "$LUCIA_ROOT"/pids/*.pid; do
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        SERVICE=$(basename "$pidfile" .pid)

        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${YELLOW}Stopping $SERVICE (PID: $PID)...${NC}"
            kill $PID

            # Wait for graceful shutdown
            for i in {1..10}; do
                if ! ps -p $PID > /dev/null 2>&1; then
                    break
                fi
                sleep 0.5
            done

            # Force kill if still running
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${YELLOW}Force stopping $SERVICE...${NC}"
                kill -9 $PID
            fi

            echo -e "${GREEN}✓${NC} $SERVICE stopped"
        else
            echo -e "${YELLOW}⚠${NC}  $SERVICE not running (stale PID file)"
        fi

        rm "$pidfile"
    fi
done

# Check if all services are stopped
sleep 1
if pgrep -f "lucia.*server.py" > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} Some Lucia processes may still be running"
    echo -e "${YELLOW}Use: ${NC}ps aux | grep lucia"
else
    echo ""
    echo -e "${GREEN}✨ All Lucia AI services stopped${NC}"
fi
