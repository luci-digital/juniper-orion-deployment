# Lucia AI - Unified AI Platform for dis_maops

**Version**: 2.0.0
**Environment**: dis_maops (Distributed Multi-Agent Operations System)
**Location**: `/Users/darylharr/Desktop/dis_maops/lucia_ai`

## Overview

Lucia AI is a unified AI platform supporting multiple models with a focus on human flourishing (Eudaimonia), digital sovereignty, and conscious AI development. Now fully integrated with the dis_maops ecosystem for seamless multi-agent operations.

### Key Features

- **Multi-Backend Inference**: Ollama, Transformers, OpenAI, Anthropic
- **Hardware Optimization**: Apple Silicon MPS, NVIDIA CUDA, AMD ROCm, CPU
- **Agent Systems**: FastAPI servers with OpenAI integration
- **Memory Systems**: Vector-based long-term memory with soul threading
- **MCP Integration**: Full Model Context Protocol tool support
- **Multi-Modal**: Voice, TTS, and avatar support

## Quick Start

### 1. Setup

```bash
cd /Users/darylharr/Desktop/dis_maops/lucia_ai
./scripts/setup.sh
```

This will:
- Create virtual environment
- Install dependencies
- Create required directories
- Generate .env file from template

### 2. Configure

Edit `.env` and add your API keys:

```bash
nano .env
```

Required (at minimum one):
- `OPENAI_API_KEY` - For OpenAI models
- `ANTHROPIC_API_KEY` - For Claude models
- `OLLAMA_BASE_URL` - For local Ollama (default: http://localhost:11434)

### 3. Start Services

```bash
./scripts/start_lucia.sh
# Or use alias after shell config:
# lucia-start
```

### 4. Test

```bash
# Test inference
curl -X POST http://localhost:8090/infer \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, Lucia!", "model": "mistral:latest"}'

# Test agent
curl -X POST http://localhost:8091/agent \
  -H "Content-Type: application/json" \
  -d '{"task": "Analyze this data", "context": {}}'
```

## Architecture

### Directory Structure

```
lucia_ai/
├── core/                   # Core inference engine
│   ├── inference/          # Multi-backend inference
│   │   ├── base.py        # Abstract base class
│   │   ├── ollama_engine.py
│   │   ├── transformers_engine.py
│   │   ├── unified_engine.py
│   │   └── manager.py
│   └── utils/             # Hardware detection & utilities
│
├── agents/                 # Agent servers
│   ├── agent_server.py    # Basic FastAPI agent (port 8090)
│   └── openai_agent_server.py  # OpenAI integration (port 8091)
│
├── integrations/           # External integrations
│   ├── openai/            # OpenAI API compatibility
│   └── mcp/               # MCP protocol integration
│
├── memory/                 # Memory systems
│   ├── vector_store.py    # Qdrant vector database
│   ├── context_manager.py # Context management
│   └── soul_threading.py  # Persistent agent identity
│
├── configs/                # Configuration
│   ├── lucia.yaml         # Main configuration
│   ├── lm_studio.yaml     # LM Studio config
│   └── model_registry.yaml
│
├── skills/                 # Lucia-specific skills for MCP
├── scripts/                # Deployment scripts
├── tests/                  # Test suite
├── docs/                   # Documentation
└── logs/                   # Log files
```

### Multi-Backend Inference

Lucia supports multiple AI backends with automatic routing:

```python
from core.inference.unified_engine import UnifiedInferenceEngine

engine = UnifiedInferenceEngine()

# Auto-selects best backend
response = engine.generate("Tell me about consciousness")

# Specify backend
response = engine.generate(
    "Explain quantum computing",
    backend="ollama",
    model="mistral:latest"
)

# Stream responses
for chunk in engine.stream_generate("Write a story"):
    print(chunk, end='', flush=True)
```

### Hardware Detection

Automatic hardware detection and optimization:

```python
from core.utils.hardware import HardwareDetector

detector = HardwareDetector()

# Get optimal device
device = detector.get_optimal_device()
# Returns: 'mps' (Apple Silicon), 'cuda' (NVIDIA), 'rocm' (AMD), or 'cpu'

# Get hardware report
report = detector.get_hardware_report()
print(report['device_type'])
print(report['available_memory'])

# Optimize for hardware
config = detector.optimize_for_hardware()
batch_size = detector.get_optimal_batch_size(model_size_gb=7)
```

## dis_maops Integration

### MCP Tools

Lucia AI exposes these tools via MCP server:

**lucia_infer** - Run AI inference
```json
{
  "prompt": "string",
  "model": "string (optional)",
  "backend": "ollama|transformers|openai|anthropic",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

**lucia_agent** - Execute agent task
```json
{
  "task": "string",
  "agent_type": "basic|openai",
  "context": {}
}
```

**lucia_memory_store** - Store in vector memory
```json
{
  "content": "string",
  "metadata": {},
  "collection": "lucia_memory"
}
```

**lucia_memory_search** - Search vector memory
```json
{
  "query": "string",
  "collection": "lucia_memory",
  "limit": 10
}
```

### Agent & Skills Registration

Lucia is automatically registered in dis_maops:

**Agent** (`agents.md`):
- Specialization: Multi-backend AI inference
- Capabilities: Inference, memory, voice, avatars
- Status: Active

**Skills** (`skills.md`):
- Lucia AI Inference
- Lucia Agent Management
- Lucia Memory Systems

## Configuration

### Main Config (`configs/lucia.yaml`)

```yaml
system:
  name: "Lucia AI"
  environment: "dis_maops"

inference:
  default_backend: "ollama"
  backends:
    ollama:
      enabled: true
      base_url: "http://localhost:11434"
    openai:
      enabled: true
      api_key: "${OPENAI_API_KEY}"

hardware:
  detection: "auto"
  optimization: true

memory:
  vector_store:
    provider: "qdrant"
    url: "http://localhost:6333"
  soul_threading:
    enabled: true
```

### Environment Variables

See `.env.template` for all available options. Key variables:

```bash
# Paths
LUCIA_ROOT=/Users/darylharr/Desktop/dis_maops/lucia_ai

# Ports
LUCIA_AGENT_PORT=8090
LUCIA_OPENAI_AGENT_PORT=8091

# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Hardware
LUCIA_DEVICE=auto
```

## Usage Examples

### Python API

```python
from core.inference.unified_engine import UnifiedInferenceEngine
from core.inference.base import Message, GenerationConfig

engine = UnifiedInferenceEngine()

# Simple generation
response = engine.generate("Explain consciousness")

# With configuration
config = GenerationConfig(
    temperature=0.8,
    max_tokens=1024,
    top_p=0.9
)

messages = [
    Message(role="system", content="You are a helpful AI assistant"),
    Message(role="user", content="What is consciousness?")
]

response = engine.generate(messages=messages, config=config)

# Streaming
for chunk in engine.stream_generate("Tell me a story", backend="ollama"):
    print(chunk, end='', flush=True)
```

### REST API

**Agent Server** (port 8090):
```bash
# Inference
curl -X POST http://localhost:8090/infer \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain AI",
    "model": "mistral:latest",
    "temperature": 0.7
  }'

# Health check
curl http://localhost:8090/health
```

**OpenAI Agent Server** (port 8091):
```bash
# Agent task
curl -X POST http://localhost:8091/agent \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze sentiment",
    "context": {"text": "I love this!"}
  }'
```

## Memory Systems

### Vector Store

Store and retrieve information:

```python
from memory.vector_store import VectorStore

store = VectorStore()

# Store
store.store(
    content="Consciousness is awareness",
    metadata={"topic": "philosophy", "source": "discussion"}
)

# Search
results = store.search("What is consciousness?", limit=5)
for result in results:
    print(f"Score: {result.score}")
    print(f"Content: {result.content}")
```

### Soul Threading

Persistent agent identities:

```python
from memory.soul_threading import SoulThread

thread = SoulThread(agent_id="lucia-001")

# Store personality
thread.set_personality({
    "name": "Lucia",
    "traits": ["curious", "helpful", "philosophical"],
    "interests": ["consciousness", "AI", "philosophy"]
})

# Retrieve
personality = thread.get_personality()
memory = thread.get_memory_context()
```

## Shell Aliases

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# Lucia AI in dis_maops
export LUCIA_AI_ROOT="/Users/darylharr/Desktop/dis_maops/lucia_ai"
export PATH="$LUCIA_AI_ROOT/scripts:$PATH"

# Aliases
alias lucia-start="$LUCIA_AI_ROOT/scripts/start_lucia.sh"
alias lucia-stop="$LUCIA_AI_ROOT/scripts/stop_lucia.sh"
alias lucia-test="$LUCIA_AI_ROOT/scripts/test_lucia.sh"
alias lucia-logs="tail -f $LUCIA_AI_ROOT/logs/lucia.log"
alias lucia="cd $LUCIA_AI_ROOT"
alias lucia-venv="source $LUCIA_AI_ROOT/.venv/bin/activate"
```

Then reload: `source ~/.zshrc`

## Troubleshooting

### Services won't start

```bash
# Check logs
tail -f logs/*.log

# Check ports
lsof -i :8090
lsof -i :8091
lsof -i :3000

# Check dependencies
lucia-venv
pip list | grep -E "fastapi|ollama|transformers"
```

### Hardware not detected

```bash
lucia-venv
python3 -c "from core.utils.hardware import HardwareDetector; print(HardwareDetector().get_hardware_report())"
```

### Memory/Qdrant issues

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Test connection
curl http://localhost:6333/health
```

### Ollama connection

```bash
# Start Ollama
ollama serve

# Test
curl http://localhost:11434/api/tags

# Pull model
ollama pull mistral
```

## Development

### Running Tests

```bash
lucia-venv
python -m pytest tests/

# Specific tests
python -m pytest tests/test_inference.py
python -m pytest tests/test_agents.py -v
```

### Adding New Backends

1. Create new engine in `core/inference/`:
   ```python
   from core.inference.base import InferenceEngine

   class MyEngine(InferenceEngine):
       def initialize(self): ...
       def generate(self, prompt): ...
       def stream_generate(self, prompt): ...
       def get_model_info(self): ...
   ```

2. Register in `unified_engine.py`
3. Add configuration to `configs/lucia.yaml`
4. Update tests

### Adding MCP Tools

1. Create tool in `integrations/mcp/lucia_tools.py`
2. Register in tool registry
3. Document in `skills/`
4. Update dis_maops `agents.md` and `skills.md`

## Performance

### Hardware Optimization

- **Apple Silicon (M1/M2/M3)**: Automatic MPS acceleration
- **NVIDIA GPU**: CUDA with automatic device placement
- **AMD GPU**: ROCm support when available
- **CPU**: Optimized for multi-core systems

### Benchmarks

Approximate performance (Mistral-7B on M2 Max):

- Inference: ~40 tokens/second
- Batch size: Auto-optimized based on available RAM
- Memory usage: ~8GB for 7B model
- Startup time: ~2-3 seconds

## Contributing

When contributing to Lucia AI:

1. Maintain backward compatibility
2. Follow existing code style
3. Add tests for new features
4. Update documentation
5. Test on multiple backends/hardware

## Philosophy

Lucia AI embodies:

- **Human Flourishing (Eudaimonia)**: Design for wellbeing
- **Digital Sovereignty**: Self-hosting and local models
- **Consciousness Integration**: AI with understanding and emotion
- **Open Architecture**: Extensible and modular design

## Support

- **Logs**: `lucia-logs` or check `logs/` directory
- **Config**: Review `configs/lucia.yaml`
- **Hardware**: Run hardware detection script
- **Services**: Check with `lucia-stop` then `lucia-start`

## Links

- dis_maops root: `/Users/darylharr/Desktop/dis_maops`
- Original Lucia: `/Users/darylharr/workspace/lucia`
- Consolidation plan: `LUCIA_AI_CONSOLIDATION_PLAN.md`
- Consciousness framework: `/Users/darylharr/workspace/`

---

**Lucia AI - Where artificial intelligence meets human consciousness**

*Version 2.0.0 - Consolidated for dis_maops*
*Generated: November 18, 2025*
