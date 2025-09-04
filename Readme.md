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
- **`rhino_bridge_server.py`** - HTTP server that runs inside Rhino Python 3.9
- **`start_rhino_bridge.py`** - Easy startup script for Rhino
- **`README.md`** - Complete guide for setting up and running the bridge

### 🛠️ **Tools/**
Contains all the tool definitions organized by category:
- **`rhino_tools.py`** - All Rhino 3D modeling tools (auto-discovery with decorators)
- **`gh_tools.py`** - All Grasshopper parametric tools (auto-discovery with decorators)
- **`tool_registry.py`** - Auto-discovery system using decorators
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

### Adding New Tools (Auto-Discovery System)
**NEW**: Tools are now automatically discovered using decorators! Just add a decorator and your tool is instantly available in MCP.

```python
@rhino_tool(name="my_tool", description="Does something awesome")
async def my_tool(param1: float):
    return call_bridge_api("/my_endpoint", {...})
```

- **Rhino tools**: Add `@rhino_tool` decorator to functions in `Tools/rhino_tools.py`
- **Grasshopper tools**: Add `@gh_tool` decorator to functions in `Tools/gh_tools.py`  
- **Zero configuration**: No manual registration needed - tools are auto-discovered on startup
- See `Tools/README.md` for detailed instructions

## 🧪 Testing

After setup, verify everything works:
1. Bridge server responds: `http://localhost:8080/status`
2. MCP server starts without errors
3. Claude Desktop shows available tools
4. Tools execute successfully
