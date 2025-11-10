# MCP Server

This directory contains the core MCP server files for Rhino Grasshopper integration with Claude Desktop.

## Files

- **`main.py`** - Main MCP server that registers and serves tools
- **`bridge_client.py`** - HTTP client for communicating with Rhino bridge server
- **`Setup/`** - Environment setup, dependencies, and configuration files

## Quick Start

**📖 For complete setup instructions, see [`Setup/setup_guide.md`](Setup/setup_guide.md)**

### 1. Install UV Package Manager

**Windows:**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Setup Environment

**Windows:**
```cmd
cd MCP\Setup
setup_env.bat
```

**macOS/Linux:**
```bash
cd MCP/Setup
chmod +x setup_env.sh
./setup_env.sh
```

### 3. Configure Claude Desktop

Add this to your `claude_desktop_config.json` (replace `YOUR_REPO_PATH`):

**Windows:**
```json
{
  "mcpServers": {
    "Rhino Grasshopper MCP": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\YOUR_REPO_PATH\\rhino_gh_mcp\\MCP\\Setup",
        "run",
        "python",
        "..\\main.py"
      ]
    }
  }
}
```

**macOS/Linux:**
```json
{
  "mcpServers": {
    "Rhino Grasshopper MCP": {
      "command": "uv",
      "args": [
        "--directory",
        "/YOUR_REPO_PATH/rhino_gh_mcp/MCP/Setup",
        "run",
        "python",
        "../main.py"
      ]
    }
  }
}
```

### 4. Start Rhino Bridge Server
1. Open Rhino 8
2. Follow the guide in `../Rhino/README.md`

### 5. Restart Claude Desktop

## How It Works

When Claude Desktop starts, the MCP server will:
- Auto-discover tools from the `../Tools/` directory using decorators
- Connect to the Rhino bridge server at `localhost:8080`
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