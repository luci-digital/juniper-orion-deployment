# Lucia AI Quick Start Guide

Get Lucia AI up and running in dis_maops in 5 minutes!

## 1. Initial Setup (One-Time)

```bash
cd /Users/darylharr/Desktop/dis_maops/lucia_ai
./scripts/setup.sh
```

This will:
- Create Python virtual environment
- Install all dependencies
- Create required directories
- Generate .env file from template

## 2. Configure API Keys

Edit the `.env` file and add at least one API key:

```bash
nano .env
```

Minimum configuration:
```bash
# For local models (recommended for privacy)
OLLAMA_BASE_URL=http://localhost:11434

# OR for cloud models
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## 3. Setup Shell Environment

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# Source Lucia AI configuration
source /Users/darylharr/Desktop/dis_maops/lucia_ai/lucia_shell_config.sh
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

You'll see: `🤖 Lucia AI environment loaded`

## 4. Start Ollama (for local models)

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Pull models
ollama pull mistral
ollama pull llama3.2
ollama pull qwen2.5-coder
```

## 5. Start Lucia AI

```bash
lucia-start
```

Output should show:
```
✅ Agent server started
✅ OpenAI agent server started
✅ Agent server is healthy
✅ OpenAI agent server is healthy
✨ Lucia AI services are running!
```

## 6. Test It!

### Quick Health Check

```bash
lucia-status
```

### Test Inference

```bash
lucia_ask "What is consciousness?"
```

### Full Health Check

```bash
lucia_health
```

### Test via curl

```bash
curl -X POST http://localhost:8090/infer \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain AI in one sentence",
    "model": "mistral:latest",
    "temperature": 0.7
  }'
```

## 7. Useful Commands

```bash
# View logs
lucia-tail

# Restart services
lucia_restart

# Stop services
lucia-stop

# Navigate to Lucia
lucia

# Edit configuration
lucia-config

# Show info
lucia_info

# Run tests
lucia-test
```

## Troubleshooting

### Services won't start

```bash
# Check what's using the ports
lsof -i :8090
lsof -i :8091

# Check logs
lucia-tail

# Try stopping and restarting
lucia-stop
sleep 2
lucia-start
```

### Ollama not connecting

```bash
# Make sure Ollama is running
ollama serve

# Test connection
curl http://localhost:11434/api/tags

# Check .env has correct URL
cat .env | grep OLLAMA
```

### Import errors

```bash
# Activate venv and reinstall
lucia-venv
pip install -r requirements.txt
```

### Missing dependencies

```bash
lucia-setup  # Re-run setup
```

## Optional: Advanced Setup

### Enable Vector Memory (Qdrant)

```bash
docker run -d -p 6333:6333 -v $(pwd)/data/qdrant:/qdrant/storage qdrant/qdrant
```

### Enable Redis Cache

```bash
brew install redis  # macOS
sudo apt install redis-server  # Linux
redis-server
```

### Enable OpenAI Integration

```bash
cd integrations/openai
npm install
npm start
```

## Next Steps

1. **Read Documentation**: `cat README.md`
2. **Configure Models**: Edit `configs/lucia.yaml`
3. **Try Different Backends**: Test Ollama, OpenAI, Anthropic
4. **Explore MCP Integration**: Check dis_maops MCP tools
5. **Run Tests**: `lucia-test`

## Quick Reference Card

```bash
# Setup (one-time)
./scripts/setup.sh

# Daily use
lucia-start              # Start services
lucia-status             # Quick check
lucia_ask "prompt"       # Quick test
lucia-tail               # View logs
lucia-stop               # Stop services

# Development
lucia                    # Navigate to Lucia
lucia-shell              # Dev shell with venv
lucia-test               # Run tests
lucia-config             # Edit config
lucia_health             # Full health check

# Info
lucia_info               # Show all commands
```

## Need Help?

- 📚 Full docs: `lucia_ai/README.md`
- 🔧 Configuration: `lucia_ai/configs/lucia.yaml`
- 📊 Logs: `lucia_ai/logs/`
- 🐛 Troubleshooting: Check logs with `lucia-tail`

---

**🤖 Welcome to Lucia AI!**

*The unified AI platform for human flourishing and digital sovereignty*
