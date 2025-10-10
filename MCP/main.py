#!/usr/bin/env python3
"""
Rhino/Grasshopper MCP Server

A Model Context Protocol (MCP) server that provides tools for interacting with:
- Rhino 3D modeling environment
- Grasshopper parametric design

This server uses an HTTP bridge architecture to communicate with Rhino 8, solving
Python version compatibility issues between MCP (requires Python 3.10+) and
Rhino's built-in Python 3.9.
"""

import logging
import sys

# Try to import MCP - if not available, provide helpful error
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Error: MCP not installed. Please install with: pip install mcp")
    sys.exit(1)

# Import tool discovery system
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Tools'))
try:
    from tool_registry import discover_tools, get_rhino_tools, get_gh_tools, get_all_tools
except ImportError as e:
    print(f"Error importing tool registry: {e}")
    sys.exit(1)

try:
    from bridge_client import BRIDGE_URL, get_bridge_status
except ImportError as e:
    print(f"Error importing bridge client: {e}")
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
    """Discover and register all tools automatically"""

    # Discover all tools from decorated functions
    print("Discovering tools...")
    discovered = discover_tools()

    # Register Rhino tools
    rhino_tools = get_rhino_tools()
    for tool_def in rhino_tools:
        mcp.tool(
            name=tool_def["name"],
            description=tool_def["description"]
        )(tool_def["function"])
        logger.info(f"Auto-registered Rhino tool: {tool_def['name']}")

    # Register Grasshopper tools
    gh_tools = get_gh_tools()
    for tool_def in gh_tools:
        mcp.tool(
            name=tool_def["name"],
            description=tool_def["description"]
        )(tool_def["function"])
        logger.info(f"Auto-registered Grasshopper tool: {tool_def['name']}")

    return len(rhino_tools), len(gh_tools)

def check_bridge_connection():
    """Check if bridge server is available"""
    try:
        status = get_bridge_status()
        if status.get("status") == "running":
            logger.info("✓ Bridge server connection verified")
            return True
        else:
            logger.warning(f"⚠ Bridge server responded but may have issues: {status}")
            return False
    except Exception as e:
        logger.warning(f"⚠ Cannot connect to bridge server: {e}")
        return False

if __name__ == "__main__":
    print("Starting Rhino/Grasshopper MCP Server...")
    print(f"Bridge server URL: {BRIDGE_URL}")
    print("This MCP server communicates with Rhino via HTTP bridge.")

    # Register all tools using auto-discovery
    total_rhino, total_gh = register_tools()

    # Check bridge connection (optional - server will still start)
    bridge_ok = check_bridge_connection()
    if not bridge_ok:
        print("Warning: Bridge server not available. Make sure to start it in Rhino before using tools.")

    # Print summary
    print(f"Auto-discovered and registered {total_rhino} Rhino tools and {total_gh} Grasshopper tools")

    # Start MCP server
    print("MCP server starting...")
    mcp.run(transport="stdio")