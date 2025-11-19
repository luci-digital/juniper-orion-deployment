# MCP Server for Maps Chronology Project

This MCP (Model Context Protocol) server exposes all the analysis and processing tools from the dis_maops project as MCP tools that can be used by AI assistants and other MCP clients.

## Installation

1. Install the MCP server dependencies:
```bash
pip install -r mcp_requirements.txt
```

2. Ensure all project dependencies are installed:
```bash
pip install -r requirements.txt
```

## Running the MCP Server

The MCP server communicates via stdio (standard input/output), which is the standard way MCP servers work.

### Direct Execution

```bash
python3 mcp_server.py
```

### With MCP Client (Claude Desktop, Cursor, etc.)

Add the server to your MCP client configuration. For example, in Claude Desktop's `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dis-maops": {
      "command": "python3",
      "args": [
        "/Users/darylharr/Desktop/dis_maops/mcp_server.py"
      ],
      "cwd": "/Users/darylharr/Desktop/dis_maops"
    }
  }
}
```

For Cursor, add to your MCP settings:

```json
{
  "mcpServers": {
    "dis-maops": {
      "command": "python3",
      "args": [
        "/Users/darylharr/Desktop/dis_maops/mcp_server.py"
      ],
      "cwd": "/Users/darylharr/Desktop/dis_maops"
    }
  }
}
```

## Available Tools

The MCP server exposes the following tools:

### 🔬 `luciazeen_analyze` (Intelligent Router)
**NEW**: Multi-purpose intelligent analysis router that automatically detects what type of analysis is needed and routes to the appropriate tool. Uses an "enzyme pattern" to identify patterns and activate analysis pathways.

**Parameters:**
- `query` (string, required): Natural language query describing what you want to analyze
- `file_path` (string, optional): Path to a file to analyze (auto-detects type)
- `auto_execute` (boolean, optional): Automatically execute recommended analysis (default: false)
- `context` (object, optional): Additional context about the analysis request

**Example:**
```json
{
  "tool": "luciazeen_analyze",
  "arguments": {
    "query": "analyze contributors and find anomalies",
    "file_path": "data/enriched_maps.json",
    "auto_execute": false
  }
}
```

See `LUCIAZEEN_README.md` for detailed documentation.

---

### 11. `analyze_doxygen`
**NEW**: Analyze Doxygen documentation projects. Based on [Doxygen internals](https://doxygen.github.io/doxygen-docs/). Analyzes Doxyfile configuration, XML output, HTML output, and documentation coverage.

**Parameters:**
- `project_path` (string, required): Path to the project directory containing Doxygen files
- `output_file` (string, optional): Output JSON file path (default: "doxygen_analysis.json")

**Example:**
```json
{
  "tool": "analyze_doxygen",
  "arguments": {
    "project_path": "/path/to/project",
    "output_file": "doxygen_analysis.json"
  }
}
```

See `DOXYGEN_INTEGRATION.md` for detailed documentation.

---

### 1. `analyze_contributors_advanced`
Perform advanced contributor correlation analysis including:
- Language patterns and usage
- Username type classification
- Coordinated posting dates
- Location/credential matching to topics
- Edit patterns (fixes vs new content)
- Language-to-posting relationships

**Parameters:**
- `enriched_maps_file` (string, optional): Path to enriched maps JSON file (default: "data/enriched_maps.json")
- `generate_report` (boolean, optional): Whether to generate HTML report (default: true)

### 2. `analyze_anomalies`
Analyze data for anomalies and unusual patterns in:
- Dates (future dates, ancient dates)
- Links (highly connected maps)
- Metadata (file sizes, missing dates)
- Geography (unusual region combinations)
- Linguistics (semantic shifts)
- Temporal patterns (large gaps)

**Parameters:** None

### 3. `analyze_expertise`
Analyze if contributors are subject matter experts or task providers based on their contribution patterns.

**Parameters:**
- `advanced_analysis_file` (string, optional): Path to advanced contributor analysis JSON file (default: "data/advanced_contributor_analysis.json")
- `enriched_maps_file` (string, optional): Path to enriched maps JSON file (default: "data/enriched_maps.json")

### 4. `correlate_contributors`
Correlate contributors - analyze authors, uploaders, and their relationships based on shared regions, themes, and temporal overlap.

**Parameters:**
- `enriched_maps_file` (string, optional): Path to enriched maps JSON file (default: "data/enriched_maps.json")
- `generate_html` (boolean, optional): Whether to generate HTML report (default: true)

### 5. `create_luci_project`
Create a Luci_Digital project structure from extracted repository list with filtering and categorization.

**Parameters:**
- `json_file` (string, optional): Path to extracted repositories JSON file (default: "extracted_repos.json")
- `project_path` (string, optional): Path where to create the project (default: "Luci_Digital_Mosh_Spark")

### 6. `extract_maps`
Extract maps and metadata from a saved Wikimedia Commons HTML page.

**Parameters:**
- `html_file` (string, optional): Path to HTML file containing Wikimedia Commons discussion page (default: "User_Enyavar_DiscussingMaps - Wikimedia Commons.html")
- `output_file` (string, optional): Output JSON file path (default: "data/extracted_maps.json")

### 7. `download_images`
Download original high-resolution images from Wikimedia Commons.

**Parameters:**
- `maps_data_file` (string, optional): Path to maps data JSON file (default: "data/extracted_maps.json")
- `download_dir` (string, optional): Directory to save downloaded images (default: "downloads/originals")

### 8. `fetch_metadata`
Fetch additional metadata from Wikimedia Commons API.

**Parameters:**
- `maps_data_file` (string, optional): Path to maps data JSON file (default: "data/extracted_maps.json")
- `output_file` (string, optional): Output JSON file path (default: "data/enriched_maps.json")

### 9. `organize_chronology`
Organize maps chronologically and build inter-related links.

**Parameters:**
- `enriched_maps_file` (string, optional): Path to enriched maps JSON file (default: "data/enriched_maps.json")
- `output_file` (string, optional): Output JSON file path (default: "data/organized_maps.json")

### 10. `generate_output`
Generate HTML output structure including timeline and individual map pages.

**Parameters:**
- `organized_maps_file` (string, optional): Path to organized maps JSON file (default: "data/organized_maps.json")
- `output_dir` (string, optional): Output directory for HTML files (default: "chronology")

### 11. `run_pipeline`
Run the complete pipeline: extract maps, download images, fetch metadata, organize chronologically, and generate output.

**Parameters:**
- `html_file` (string, optional): Path to HTML file containing Wikimedia Commons discussion page (default: "User_Enyavar_DiscussingMaps - Wikimedia Commons.html")
- `skip_downloads` (boolean, optional): Skip image downloads (default: false)
- `skip_metadata` (boolean, optional): Skip metadata fetching (default: false)

## Usage Examples

### Example 1: Analyze Contributors
```python
# Via MCP client
{
  "tool": "analyze_contributors_advanced",
  "arguments": {
    "enriched_maps_file": "data/enriched_maps.json",
    "generate_report": true
  }
}
```

### Example 2: Run Complete Pipeline
```python
# Via MCP client
{
  "tool": "run_pipeline",
  "arguments": {
    "html_file": "User_Enyavar_DiscussingMaps - Wikimedia Commons.html",
    "skip_downloads": false,
    "skip_metadata": false
  }
}
```

### Example 3: Extract Maps Only
```python
# Via MCP client
{
  "tool": "extract_maps",
  "arguments": {
    "html_file": "User_Enyavar_DiscussingMaps - Wikimedia Commons.html",
    "output_file": "data/extracted_maps.json"
  }
}
```

## Output Files

The tools generate various output files in the `data/` and `chronology/` directories:

- `data/extracted_maps.json` - Extracted maps from HTML
- `data/enriched_maps.json` - Maps with API metadata
- `data/organized_maps.json` - Chronologically organized maps
- `data/advanced_contributor_analysis.json` - Advanced contributor analysis
- `data/contributor_analysis.json` - Contributor correlation analysis
- `data/contributor_expertise_analysis.json` - Expertise analysis
- `chronology/index.html` - Main timeline page
- `chronology/maps/` - Individual map pages
- `chronology/advanced_contributor_analysis.html` - Advanced analysis report
- `chronology/contributor_correlations.html` - Contributor network visualization

## Troubleshooting

### Import Errors
If you see import errors, make sure all dependencies are installed:
```bash
pip install -r requirements.txt
pip install -r mcp_requirements.txt
```

### File Not Found Errors
Ensure you're running the server from the project root directory, or adjust file paths in tool calls.

### MCP Connection Issues
- Verify the Python path in your MCP client configuration
- Check that the server script is executable: `chmod +x mcp_server.py`
- Ensure the working directory (`cwd`) is set correctly in the MCP client config

## Development

To extend the MCP server with additional tools:

1. Add the tool definition to the `list_tools()` function
2. Add the tool handler to the `call_tool()` function
3. Import any necessary modules at the top of the file

## License

Same as the main project.

