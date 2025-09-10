# Rhino Grasshopper MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with Rhino 3D and Grasshopper. Uses an HTTP bridge architecture to solve Python version compatibility between MCP (Python 3.10+) and Rhino's Python 3.9.

## 📁 Project Structure

This repository is organized into three main directories:

### 🔌 **MCP/**
Contains everything needed to run the MCP server and integrate with Claude Desktop:
- **`main.py`** - MCP server that registers and serves tools
- **`bridge_client.py`** - HTTP client for communicating with Rhino
- **`config/`** - Claude Desktop configuration templates and setup guides
- **`requirements.txt`** - Python dependencies for MCP server

### 🦏 **Rhino/**
Contains everything needed to run the HTTP bridge server inside Rhino:
- **`rhino_bridge_server.py`** - Dynamic HTTP server with auto-discovery system
- **`start_rhino_bridge.py`** - Easy startup script for Rhino
- **`README.md`** - Complete guide for setting up and running the bridge

### 🛠️ **Tools/**
Contains all the tool definitions organized by category:
- **`rhino_tools.py`** - Rhino 3D tools with both MCP and bridge handlers
- **`gh_tools.py`** - Grasshopper tools with both MCP and bridge handlers
- **`tool_registry.py`** - Fully dynamic discovery system for both MCP and bridge
- **`README.md`** - Guide for developers to add new tools

## 🚀 Quick Start

### 1. Set Up MCP Server (Python 3.10+)
```bash
cd MCP/
pip install -r requirements.txt
```

### 2. Configure Claude Desktop
Follow the setup guide in `MCP/config/MCP_CLIENT_SETUP.md`

### 3. Start Rhino Bridge Server
1. Open Rhino 8
2. Follow the guide in `Rhino/README.md`

### 4. Start MCP Server
```bash
cd MCP/
python main.py
```

### 5. Test Integration
In Claude Desktop:
- "Get Rhino information"
- "Draw a line from 0,0,0 to 10,10,5"
- "List Grasshopper sliders"

## 🔧 For Developers

### Adding New Tools (Fully Dynamic System)
**NEW**: Both MCP tools AND bridge endpoints are automatically discovered! Add two decorators and everything is handled automatically.

```python
# MCP tool (client-side)
@rhino_tool(name="my_tool", description="Does something awesome")
async def my_tool(param1: float):
    return call_bridge_api("/my_endpoint", {...})

# Bridge handler (server-side)
@bridge_handler("/my_endpoint")
def handle_my_endpoint(data):
    # Rhino/Grasshopper operations here
    return {"success": True, "result": "..."}
```

- **Zero manual registration**: Both MCP and bridge systems auto-discover your tools
- **Single location**: Add both decorators to the same tool file
- **Instant deployment**: Just restart servers and your new tool is available
- See `Tools/README.md` for detailed instructions

## 🧪 Testing

After setup, verify everything works:
1. Bridge server responds: `http://localhost:8080/status`
2. MCP server starts without errors
3. Claude Desktop shows available tools
4. Tools execute successfully
