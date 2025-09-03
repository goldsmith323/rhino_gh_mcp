#!/usr/bin/env python3
"""
Rhino/Grasshopper MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with:
- Rhino 3D modeling environment
- Grasshopper parametric design

This server uses an HTTP bridge architecture to communicate with Rhino 8, solving 
Python version compatibility issues between MCP (requires Python 3.10+) and 
Rhino's built-in Python 3.9.

Author: Hossein Zargar
"""

import logging
import sys

# Try to import MCP - if not available, provide helpful error
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: MCP not installed. Please install with: pip install mcp")
    sys.exit(1)

# Import tool modules
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Tools'))
try:
    from rhino_tools import RHINO_TOOLS
    from gh_tools import GRASSHOPPER_TOOLS
    from bridge_client import BRIDGE_URL, get_bridge_status
except ImportError as e:
    print(f"Error importing tool modules: {e}")
    sys.exit(1)

# Initialize MCP server
mcp = FastMCP("Rhino Grasshopper MCP")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rhino_gh_mcp.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def register_tools():
    """Register all tools from tool modules"""
    
    # Register Rhino tools
    for tool_def in RHINO_TOOLS:
        mcp.tool(
            name=tool_def["name"],
            description=tool_def["description"]
        )(tool_def["function"])
        logger.info(f"Registered Rhino tool: {tool_def['name']}")
    
    # Register Grasshopper tools
    for tool_def in GRASSHOPPER_TOOLS:
        mcp.tool(
            name=tool_def["name"], 
            description=tool_def["description"]
        )(tool_def["function"])
        logger.info(f"Registered Grasshopper tool: {tool_def['name']}")

def check_bridge_connection():
    """Check if bridge server is available"""
    try:
        status = get_bridge_status()
        if status.get("success", False):
            logger.info("✓ Bridge server connection verified")
            return True
        else:
            logger.warning("⚠ Bridge server responded but may have issues")
            return False
    except Exception as e:
        logger.warning(f"⚠ Cannot connect to bridge server: {e}")
        return False

if __name__ == "__main__":
    print("Starting Rhino/Grasshopper MCP Server...")
    print(f"Bridge server URL: {BRIDGE_URL}")
    print("This MCP server communicates with Rhino via HTTP bridge.")
    
    # Register all tools
    register_tools()
    
    # Check bridge connection (optional - server will still start)
    bridge_ok = check_bridge_connection()
    if not bridge_ok:
        print("Warning: Bridge server not available. Make sure to start it in Rhino before using tools.")
    
    # Print summary
    total_rhino = len(RHINO_TOOLS)
    total_gh = len(GRASSHOPPER_TOOLS)
    print(f"Registered {total_rhino} Rhino tools and {total_gh} Grasshopper tools")
    
    # Start MCP server
    print("MCP server starting...")
    mcp.run(transport="stdio")