# Quick Setup Guide for MCP Server

## Prerequisites

1. Python 3.8 or higher
2. All project dependencies installed

## Installation Steps

1. **Install MCP SDK and dependencies:**
   ```bash
   pip install -r mcp_requirements.txt
   pip install -r requirements.txt
   ```

2. **Make the server executable:**
   ```bash
   chmod +x mcp_server.py
   ```

3. **Test the server:**
   ```bash
   python3 mcp_server.py
   ```
   
   The server should start and wait for input via stdio. Press Ctrl+C to exit.

## Configuration for MCP Clients

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

**Note:** Replace `/Users/darylharr/Desktop/dis_maops` with your actual project path.

### Cursor

Edit Cursor's MCP settings (usually in Settings → MCP):

```json
{
  "mcpServers": {
    "dis-maops": {
      "command": "python3",
      "args": [
        "/path/to/dis_maops/mcp_server.py"
      ],
      "cwd": "/path/to/dis_maops"
    }
  }
}
```

### Other MCP Clients

The server uses stdio transport, which is standard for MCP. Configure your client to:
- Command: `python3` (or `python` on Windows)
- Args: `["/path/to/mcp_server.py"]`
- Working directory: `/path/to/dis_maops`

## Verifying Installation

Once configured, your MCP client should list the following tools:
- `analyze_contributors_advanced`
- `analyze_anomalies`
- `analyze_expertise`
- `correlate_contributors`
- `create_luci_project`
- `extract_maps`
- `download_images`
- `fetch_metadata`
- `organize_chronology`
- `generate_output`
- `run_pipeline`

## Troubleshooting

### "MCP SDK not installed" error
```bash
pip install mcp
```

### Import errors for project modules
Make sure you're running from the project root directory and all dependencies are installed:
```bash
cd /Users/darylharr/Desktop/dis_maops
pip install -r requirements.txt
```

### Server not appearing in client
- Check that the path to `mcp_server.py` is correct and absolute
- Verify Python is in your PATH: `which python3`
- Check server logs for errors
- Ensure the `cwd` (working directory) is set correctly

### Permission errors
```bash
chmod +x mcp_server.py
```

## Next Steps

See `MCP_README.md` for detailed documentation on each tool and usage examples.

