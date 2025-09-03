# Rhino Grasshopper MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with Rhino 3D and Grasshopper. Uses an HTTP bridge architecture to solve Python version compatibility between MCP (Python 3.10+) and Rhino's Python 3.9.

**Author:** Hossein Zargar

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
- **`rhino_tools.py`** - All Rhino 3D modeling tools (easy to extend)
- **`gh_tools.py`** - All Grasshopper parametric tools (easy to extend)
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

## 🏗️ Architecture

```
Claude Desktop → MCP Server → HTTP Bridge → Rhino/Grasshopper
```

- **MCP Server** (Python 3.10+) - Handles Claude Desktop communication
- **HTTP Bridge** (Python 3.9) - Runs inside Rhino, executes operations  
- **Tool Modules** - Organized by category for easy expansion

## 🔧 For Developers

### Adding New Tools
- **Rhino tools**: Edit `Tools/rhino_tools.py`
- **Grasshopper tools**: Edit `Tools/gh_tools.py`  
- See `Tools/README.md` for detailed instructions

### Project Benefits
- ✅ **Clean organization** - Each directory has a clear purpose
- ✅ **Easy setup** - Step-by-step guides in each directory  
- ✅ **Developer friendly** - Simple to add new tools
- ✅ **Modular design** - Components can be developed independently

## 📖 Documentation

Each directory contains its own README with specific setup instructions:
- **`MCP/README.md`** - MCP server setup and Claude Desktop integration
- **`Rhino/README.md`** - Rhino bridge server setup and usage
- **`Tools/README.md`** - Tool development and extension guide

## 🧪 Testing

After setup, verify everything works:
1. Bridge server responds: `http://localhost:8080/status`
2. MCP server starts without errors
3. Claude Desktop shows available tools
4. Tools execute successfully

## ⚡ Key Features

- **Python compatibility solved** - HTTP bridge handles version differences
- **Modular architecture** - Clean separation of concerns
- **Easy to extend** - Add tools by editing appropriate module
- **Well documented** - Clear setup guides for each component
- **Production ready** - Tested and working with Claude Desktop

---

**Ready to get started?** Choose your path:
- **User**: Follow `MCP/README.md` then `Rhino/README.md`
- **Developer**: Start with `Tools/README.md` to understand the architecture
