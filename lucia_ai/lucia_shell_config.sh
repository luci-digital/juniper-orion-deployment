#!/bin/bash
# Lucia AI Shell Configuration
# Add to ~/.zshrc or ~/.bashrc: source /Users/darylharr/Desktop/dis_maops/lucia_ai/lucia_shell_config.sh

# =============================================================================
# Lucia AI Environment
# =============================================================================

export DIS_MAOPS_ROOT="/Users/darylharr/Desktop/dis_maops"
export LUCIA_AI_ROOT="$DIS_MAOPS_ROOT/lucia_ai"

# Add Lucia scripts to PATH
export PATH="$LUCIA_AI_ROOT/scripts:$PATH"

# =============================================================================
# Lucia AI Aliases
# =============================================================================

# Service management
alias lucia-start="$LUCIA_AI_ROOT/scripts/start_lucia.sh"
alias lucia-stop="$LUCIA_AI_ROOT/scripts/stop_lucia.sh"
alias lucia-test="$LUCIA_AI_ROOT/scripts/test_lucia.sh"
alias lucia-setup="$LUCIA_AI_ROOT/scripts/setup.sh"

# Navigation
alias lucia="cd $LUCIA_AI_ROOT"
alias lucia-logs="cd $LUCIA_AI_ROOT/logs"
alias lucia-configs="cd $LUCIA_AI_ROOT/configs"

# Logs and monitoring
alias lucia-tail="tail -f $LUCIA_AI_ROOT/logs/lucia.log"
alias lucia-tail-agent="tail -f $LUCIA_AI_ROOT/logs/agent_server.log"
alias lucia-tail-openai="tail -f $LUCIA_AI_ROOT/logs/openai_agent_server.log"
alias lucia-log="cat $LUCIA_AI_ROOT/logs/lucia.log"

# Virtual environment
alias lucia-venv="source $LUCIA_AI_ROOT/.venv/bin/activate"
alias lucia-deactivate="deactivate"

# Development
alias lucia-shell="lucia && lucia-venv && echo '🤖 Lucia AI Development Shell'"
alias lucia-python="lucia-venv && python3"
alias lucia-pip="lucia-venv && pip"

# Testing
alias lucia-pytest="lucia-venv && cd $LUCIA_AI_ROOT && python -m pytest tests/"
alias lucia-test-inference="lucia-venv && cd $LUCIA_AI_ROOT && python -m pytest tests/test_inference.py -v"
alias lucia-test-agents="lucia-venv && cd $LUCIA_AI_ROOT && python -m pytest tests/test_agents.py -v"

# Quick commands
alias lucia-status="curl -s http://localhost:8090/health && curl -s http://localhost:8091/health && echo '✅ Lucia AI services are healthy'"
alias lucia-infer="curl -X POST http://localhost:8090/infer -H 'Content-Type: application/json' -d"

# =============================================================================
# Lucia AI Functions
# =============================================================================

# Quick inference function
lucia_ask() {
    if [ -z "$1" ]; then
        echo "Usage: lucia_ask \"your prompt here\" [model]"
        return 1
    fi

    local prompt="$1"
    local model="${2:-mistral:latest}"

    curl -s -X POST http://localhost:8090/infer \
        -H "Content-Type: application/json" \
        -d "{\"prompt\": \"$prompt\", \"model\": \"$model\"}" | jq -r '.response'
}

# Check all Lucia services
lucia_health() {
    echo "🔍 Checking Lucia AI services..."
    echo ""

    # Agent Server
    if curl -s http://localhost:8090/health > /dev/null 2>&1; then
        echo "✅ Agent Server (8090): Running"
    else
        echo "❌ Agent Server (8090): Not running"
    fi

    # OpenAI Agent Server
    if curl -s http://localhost:8091/health > /dev/null 2>&1; then
        echo "✅ OpenAI Agent Server (8091): Running"
    else
        echo "❌ OpenAI Agent Server (8091): Not running"
    fi

    # OpenAI Integration
    if curl -s http://localhost:3000/health > /dev/null 2>&1; then
        echo "✅ OpenAI Integration (3000): Running"
    else
        echo "⚠️  OpenAI Integration (3000): Not running (optional)"
    fi

    echo ""

    # Check dependencies
    echo "📦 Checking dependencies..."

    # Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama: Running"
    else
        echo "⚠️  Ollama: Not running (start with: ollama serve)"
    fi

    # Qdrant
    if curl -s http://localhost:6333/health > /dev/null 2>&1; then
        echo "✅ Qdrant: Running"
    else
        echo "⚠️  Qdrant: Not running (optional, start with: docker run -p 6333:6333 qdrant/qdrant)"
    fi

    # Redis
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis: Running"
    else
        echo "⚠️  Redis: Not running (optional, start with: redis-server)"
    fi
}

# Restart Lucia services
lucia_restart() {
    echo "🔄 Restarting Lucia AI services..."
    lucia-stop
    sleep 2
    lucia-start
}

# Edit Lucia configuration
lucia_config() {
    local editor="${EDITOR:-nano}"
    $editor "$LUCIA_AI_ROOT/configs/lucia.yaml"
}

# Edit environment variables
lucia_env() {
    local editor="${EDITOR:-nano}"
    $editor "$LUCIA_AI_ROOT/.env"
}

# Show Lucia AI info
lucia_info() {
    cat << 'LUCIAINFO'
╔═══════════════════════════════════════════════════════════════╗
║                    Lucia AI Platform                          ║
║              Unified AI for dis_maops                         ║
╚═══════════════════════════════════════════════════════════════╝

📍 Location: /Users/darylharr/Desktop/dis_maops/lucia_ai

🚀 Quick Commands:
   lucia-start         Start all Lucia services
   lucia-stop          Stop all Lucia services
   lucia-restart       Restart services
   lucia-health        Check service health
   lucia-status        Quick health check
   lucia-logs          Navigate to logs directory
   lucia-tail          Tail main log file

🔧 Development:
   lucia               Navigate to Lucia root
   lucia-shell         Start development shell
   lucia-venv          Activate Python venv
   lucia-test          Run all tests
   lucia-pytest        Run pytest

📊 Testing:
   lucia_ask "prompt"  Quick inference test
   lucia_health        Full health check

📝 Configuration:
   lucia-config        Edit lucia.yaml
   lucia-env           Edit .env file

📚 Documentation:
   cat $LUCIA_AI_ROOT/README.md
   cat $LUCIA_AI_ROOT/../LUCIA_AI_CONSOLIDATION_PLAN.md

LUCIAINFO
}

# =============================================================================
# Auto-completion (bash/zsh compatible)
# =============================================================================

if [ -n "$ZSH_VERSION" ]; then
    # Zsh completion
    compdef _gnu_generic lucia_ask
elif [ -n "$BASH_VERSION" ]; then
    # Bash completion
    complete -F _command lucia_ask
fi

# =============================================================================
# Initialization Message
# =============================================================================

if [ -t 1 ]; then
    echo "🤖 Lucia AI environment loaded"
    echo "   Type 'lucia_info' for commands"
fi
