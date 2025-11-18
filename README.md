# dis_maops - Distributed Multi-Agent Operations System

A comprehensive multi-agent analysis ecosystem with MCP (Model Context Protocol) server integration, featuring intelligent analysis routing and specialized data processing agents.

## System Overview

dis_maops combines:
- **🧠 LuciaZeen**: Intelligent analysis router using "enzyme pattern" for automatic tool selection
- **🤖 Lucia AI**: Unified multi-backend AI platform with inference, agents, and memory systems
- **🔮 MCP Server**: Model Context Protocol server exposing all tools to AI assistants
- **📊 Specialized Agents**: Domain-specific analysis agents for various data types
- **🗺️ Maps Chronology**: Historical cartography analysis and timeline generation
- **🔬 Advanced Analytics**: Contributor analysis, anomaly detection, and correlation mining

## Project Structure

```
dis_maops/
├── agents.md                 # Agent directory and capabilities
├── skills.md                 # Skills matrix and expertise areas
├── lucia_ai/                 # 🤖 Lucia AI Platform (NEW)
│   ├── core/                # Multi-backend inference engine
│   ├── agents/              # FastAPI agent servers
│   ├── memory/              # Vector store & soul threading
│   ├── configs/             # Configuration files
│   ├── scripts/             # Setup and deployment
│   └── README.md            # Lucia AI documentation
├── mcp_tool/                 # MCP server and configuration
│   ├── mcp_server.py        # MCP server implementation
│   ├── mcp_requirements.txt  # MCP-specific dependencies
│   ├── mcp_config_example.json # Example MCP configuration
│   ├── MCP_README.md         # MCP server documentation
│   └── MCP_SETUP.md          # MCP setup instructions
└── projects/                 # Analysis projects and tools
    ├── Maps Chronology Project/
    │   ├── extract_maps.py   # Map extraction from HTML
    │   ├── organize_chronology.py # Chronological organization
    │   ├── generate_output.py # HTML timeline generation
    │   └── data/             # Project data and outputs
    ├── Domain2_Knowledge_Systems_Level10/
    │   ├── api/              # Knowledge systems API
    │   ├── database/         # Database models
    │   └── docs/             # Documentation
    ├── Luci_Digital_Mosh_Spark/
    │   ├── api-clients/      # API client libraries
    │   ├── api-gateway/      # API gateway server
    │   └── repositories/     # Cloned repositories
    ├── alexzedim-repos/      # Repository collection
    └── analysis_tools/       # Additional analysis scripts
        ├── analyze_anomalies.py
        ├── correlate_contributors.py
        └── linguistic_analysis.py
```

## Usage

### 🧠 Intelligent Analysis (LuciaZeen)

Use the intelligent router for automatic analysis:
```bash
cd projects
python3 luciazeen_analyzer.py
# Or query directly: "analyze contributors and find anomalies"
```

### 🤖 MCP Server Integration

Run the MCP server for AI assistant integration:
```bash
cd mcp_tool
pip install -r mcp_requirements.txt
python3 mcp_server.py
```

Configure your AI assistant (Claude Desktop, Cursor) with:
```json
{
  "mcpServers": {
    "dis-maops": {
      "command": "python3",
      "args": ["/path/to/dis_maops/mcp_tool/mcp_server.py"],
      "cwd": "/path/to/dis_maops"
    }
  }
}
```

### 🗺️ Maps Chronology Pipeline

Run the complete maps chronology pipeline:
```bash
cd projects
python3 run_pipeline.py
```

### Step by Step Maps Analysis

1. **Extract maps from HTML:**
   ```bash
   cd projects
   python3 extract_maps.py
   ```

2. **Download original images (optional, may take time):**
   ```bash
   python3 download_images.py
   ```

3. **Fetch metadata from API (optional, may take time):**
   ```bash
   python3 fetch_metadata.py
   ```

4. **Organize chronologically:**
   ```bash
   python3 organize_chronology.py
   ```

5. **Generate output:**
   ```bash
   python3 generate_output.py
   ```

### 🔍 GitHub Organization Analysis (NEW)

Analyze entire GitHub organizations and their repositories:

```bash
# Analyze NSA GitHub organization (85+ repos)
python3 analyze_github_org.py NationalSecurityAgency

# With GitHub token for higher rate limits (optional)
export GITHUB_TOKEN=your_token_here
python3 analyze_github_org.py NationalSecurityAgency
```

**Features:**
- Fetches all repositories for an organization
- Technology stack analysis (languages, licenses, topics)
- Cross-repository contributor analysis
- Repository categorization
- Comprehensive statistics and reports

See `GITHUB_ORG_INTEGRATION.md` for detailed documentation.

## Features

- **Chronological Organization**: Maps are sorted by date (extracted from filenames, captions, and metadata)
- **Inter-Related Links**: Maps are linked by geographic regions, themes, and temporal proximity
- **Citations & Footnotes**: All citations and attribution information is preserved
- **Multilingual Support**: Captions in multiple languages are extracted and displayed
- **Timeline View**: Interactive HTML timeline showing maps organized by year
- **Individual Map Pages**: Each map has its own page with metadata, descriptions, and related maps
- **GitHub Organization Analysis**: Analyze entire GitHub organizations with cross-repository insights (NEW)

## Output

The main output is in the `chronology/` directory:
- `index.html` - Interactive timeline showing all maps chronologically
- `maps/` - Individual folders for each map with images, metadata, and descriptions
- `data/` - JSON files with timeline, links, and metadata

## Statistics

From the current extraction:
- **65 maps** extracted from the HTML page
- **23 maps** have identifiable dates
- **25 maps** have geographic region information
- **32 inter-related links** created between maps
- **21 timeline groups** (by year)

## Notes

- Image downloads and API metadata fetching are optional steps that can take significant time due to rate limiting
- The system works with extracted data even if downloads/metadata fetching are skipped
- All scripts include error handling and progress reporting
- Citations and footnotes are extracted from both HTML content and API metadata

## Dependencies

Install required packages:
```bash
pip3 install -r requirements.txt
```

Required packages:
- beautifulsoup4
- requests
- python-dateutil
- lxml
- html5lib



## 🤖 Lucia AI Platform

**NEW**: Lucia AI has been integrated into dis_maops for unified AI operations!

### Quick Start

```bash
cd lucia_ai
./scripts/setup.sh    # One-time setup
./scripts/start_lucia.sh  # Start services
```

### Features

- **Multi-Backend Inference**: Ollama, Transformers, OpenAI, Anthropic
- **Hardware Optimized**: Apple Silicon MPS, NVIDIA CUDA, AMD ROCm, CPU
- **Agent Servers**: FastAPI agents on ports 8090 (basic) and 8091 (OpenAI)
- **Memory Systems**: Qdrant vector store with persistent agent identities
- **MCP Integration**: Full tool support for dis_maops workflows

### Shell Aliases

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# Lucia AI
export LUCIA_AI_ROOT="/Users/darylharr/Desktop/dis_maops/lucia_ai"
alias lucia-start="$LUCIA_AI_ROOT/scripts/start_lucia.sh"
alias lucia-stop="$LUCIA_AI_ROOT/scripts/stop_lucia.sh"
alias lucia-test="$LUCIA_AI_ROOT/scripts/test_lucia.sh"
alias lucia-logs="tail -f $LUCIA_AI_ROOT/logs/lucia.log"
alias lucia="cd $LUCIA_AI_ROOT"
```

### Documentation

See `lucia_ai/README.md` for complete documentation.

