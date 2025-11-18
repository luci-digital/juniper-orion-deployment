# 🤖 Get Started with Lucia AI in 3 Steps!

Lucia AI has been consolidated and optimized for dis_maops. Here's how to start using it immediately:

## Step 1: Add Shell Configuration (30 seconds)

Add this ONE line to your shell config:

```bash
echo 'source /Users/darylharr/Desktop/dis_maops/lucia_ai/lucia_shell_config.sh' >> ~/.zshrc
```

Then reload your shell:
```bash
source ~/.zshrc
```

You should see: `🤖 Lucia AI environment loaded`

**What this gives you:**
- 20+ instant aliases (`lucia-start`, `lucia-stop`, `lucia-tail`, etc.)
- 5 helpful functions (`lucia_ask`, `lucia_health`, `lucia_info`, etc.)
- Proper PATH configuration
- Environment variables set

## Step 2: Configure & Setup (2 minutes)

```bash
cd /Users/darylharr/Desktop/dis_maops/lucia_ai

# Edit .env and add at least one API key
nano .env
# Add: OPENAI_API_KEY=sk-... or ANTHROPIC_API_KEY=sk-ant-...
# Or just use Ollama locally (see step 3)

# Run one-time setup
./scripts/setup.sh
```

The setup script will:
- Create Python virtual environment
- Install all dependencies
- Create required directories
- Initialize configurations

## Step 3: Start & Test (1 minute)

### Option A: Use Local Models (Ollama)

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Pull a model and start Lucia
ollama pull mistral
lucia-start

# Test it
lucia_ask "Hello, Lucia! Tell me about consciousness."
```

### Option B: Use Cloud Models (OpenAI/Anthropic)

```bash
# Just start (API keys from .env)
lucia-start

# Test it
lucia_ask "Hello, Lucia! What is AI?"
```

## That's It! 🎉

You now have full Lucia AI capabilities. Try these commands:

```bash
# Quick tests
lucia-status              # Check services
lucia_health              # Full health diagnostic
lucia_ask "prompt here"   # Quick inference

# View logs
lucia-tail                # Live log viewer
lucia-logs                # Navigate to logs

# Development
lucia                     # Navigate to Lucia
lucia-shell               # Dev shell with venv
lucia-config              # Edit configuration

# Help
lucia_info                # Show all commands
```

## Verify Everything Works

Run this comprehensive check:

```bash
lucia_health
```

You should see:
```
✅ Agent Server (8090): Running
✅ OpenAI Agent Server (8091): Running
✅ Ollama: Running
```

## Quick Reference

### Most Used Commands
```bash
lucia-start        # Start all services
lucia-stop         # Stop all services
lucia-status       # Quick health check
lucia-tail         # View logs live
lucia_ask "..."    # Quick inference test
lucia_health       # Full diagnostic
lucia_info         # Show all commands
```

### Aliases Cheat Sheet
```
Service Control:
  lucia-start, lucia-stop, lucia-restart, lucia-setup

Navigation:
  lucia (go to root), lucia-logs, lucia-configs

Monitoring:
  lucia-tail, lucia-tail-agent, lucia-tail-openai, lucia-log

Development:
  lucia-venv, lucia-shell, lucia-python, lucia-pip

Testing:
  lucia-test, lucia-pytest, lucia-test-inference

Quick Access:
  lucia-status, lucia-infer
```

### Functions Cheat Sheet
```
lucia_ask "prompt"     # Quick inference
lucia_health           # Full health check
lucia_restart          # Restart services
lucia_config           # Edit lucia.yaml
lucia_env              # Edit .env
lucia_info             # Show command reference
```

## Documentation

- **Quick Start**: `lucia_ai/QUICKSTART.md`
- **Full Docs**: `lucia_ai/README.md`
- **Migration Plan**: `LUCIA_AI_CONSOLIDATION_PLAN.md`
- **Completion Report**: `LUCIA_CONSOLIDATION_COMPLETE.md`

## Need Help?

```bash
# Show command info
lucia_info

# Check service health
lucia_health

# View logs for errors
lucia-tail

# Check configuration
lucia-config
```

## Advanced: MCP Integration

Lucia AI tools are automatically available in dis_maops MCP server:

- `lucia_infer` - Run AI inference
- `lucia_agent` - Execute agent tasks
- `lucia_memory_store` - Store in vector memory
- `lucia_memory_search` - Search memories

## System Requirements

**Minimum:**
- macOS/Linux (tested on macOS)
- Python 3.8+
- 4GB RAM
- Internet connection (for cloud models)

**Recommended:**
- 16GB+ RAM
- Apple Silicon M1/M2/M3 (for MPS acceleration)
- OR NVIDIA GPU (for CUDA)
- Ollama installed (for local models)

## Troubleshooting

### Services won't start
```bash
lucia-stop
sleep 2
lucia-start
lucia-tail  # Check for errors
```

### Command not found
```bash
# Make sure shell config is loaded
source ~/.zshrc
lucia_info  # Should work now
```

### Import errors
```bash
lucia-venv
pip install -r requirements.txt
```

## What's Next?

1. **Explore backends**: Try Ollama, OpenAI, Anthropic
2. **Test different models**: Mistral, Llama, GPT-4o, Claude
3. **Enable memory**: Start Qdrant for vector memory
4. **Run tests**: `lucia-test` to verify everything
5. **Integrate with dis_maops**: Use MCP tools in your workflows

---

**🚀 You're Ready!**

Lucia AI is now fully operational at `/Users/darylharr/Desktop/dis_maops/lucia_ai`

*For detailed information, run: `lucia_info`*
