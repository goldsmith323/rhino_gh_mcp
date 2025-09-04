# MCP Server

This directory contains everything needed to run the MCP server and integrate with Claude Desktop.

## Files

- **`main.py`** - Main MCP server that registers and serves tools
- **`bridge_client.py`** - HTTP client for communicating with Rhino bridge server
- **`requirements.txt`** - Python dependencies for the MCP server
- **`config/`** - Configuration templates and setup guides for Claude Desktop

## Setup

### 1. Install Dependencies (Python 3.10+)
```bash
cd MCP/
pip install -r requirements.txt
```

### 2. Configure Claude Desktop
1. Copy the configuration from `config/mcp_client_config.json`
2. Update the path to point to your `main.py` file
3. Add to Claude Desktop config (see `config/MCP_CLIENT_SETUP.md`)
4. Restart Claude Desktop

### 3. Start MCP Server
```bash
python main.py
```

The server will:
- Auto-discover tools from the `../Tools/` directory using decorators
- Try to connect to the Rhino bridge server at `localhost:8080`
- Register all discovered tools with the MCP protocol
- Wait for requests from Claude Desktop

## Usage

Once configured, you can use these commands in Claude Desktop:
- "Get Rhino information"
- "Draw a line from 0,0,0 to 10,10,5"  
- "Generate a Pratt truss from 0,0,0 to 20,0,0 with depth 3 and 6 divisions"
- "List Grasshopper sliders"
- "Set Width slider to 25"

## Troubleshooting

**Error: "Cannot connect to Rhino Bridge Server"**
- Make sure the Rhino bridge server is running (see `../Rhino/README.md`)
- Check that Rhino is open and the bridge server started successfully

**Error: "MCP not installed"**
- Install dependencies: `pip install -r requirements.txt`
- Make sure you're using Python 3.10 or higher

**Tools not appearing in Claude Desktop**
- Verify Claude Desktop configuration file path and JSON syntax
- Restart Claude Desktop after making config changes
- Check that the path to `main.py` is correct and absolute