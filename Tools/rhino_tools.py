"""
Rhino 3D Tools

This module contains all Rhino-specific MCP tools that communicate with the
Rhino bridge server to execute operations within Rhino 3D.

Author: Hossein Zargar
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Import bridge_client from MCP directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MCP'))
from bridge_client import call_bridge_api

async def draw_line_rhino(
    start_x: float, 
    start_y: float, 
    start_z: float, 
    end_x: float, 
    end_y: float, 
    end_z: float
) -> Dict[str, Any]:
    """
    Draw a line in Rhino between two 3D points via HTTP bridge.
    
    Args:
        start_x: X-coordinate of start point
        start_y: Y-coordinate of start point  
        start_z: Z-coordinate of start point
        end_x: X-coordinate of end point
        end_y: Y-coordinate of end point
        end_z: Z-coordinate of end point
        
    Returns:
        Dict containing line creation results
    """
    
    request_data = {
        "start_x": start_x,
        "start_y": start_y,
        "start_z": start_z,
        "end_x": end_x,
        "end_y": end_y,
        "end_z": end_z
    }
    
    return call_bridge_api("/draw_line", request_data)

async def get_rhino_info() -> Dict[str, Any]:
    """
    Get information about the current Rhino session via HTTP bridge.
    
    Returns:
        Dict containing Rhino session information
    """
    
    return call_bridge_api("/get_rhino_info", {})

# Tool definitions for MCP registration
RHINO_TOOLS = [
    {
        "name": "draw_line_rhino",
        "description": (
            "Draw a line in Rhino 3D space between two points. "
            "This tool creates a line object in the current Rhino document. "
            "Coordinates are specified in Rhino's current units (usually millimeters or inches). "
            "\n\n**Parameters:**\n"
            "- **start_x** (float): X-coordinate of the line start point\n"
            "- **start_y** (float): Y-coordinate of the line start point\n" 
            "- **start_z** (float): Z-coordinate of the line start point\n"
            "- **end_x** (float): X-coordinate of the line end point\n"
            "- **end_y** (float): Y-coordinate of the line end point\n"
            "- **end_z** (float): Z-coordinate of the line end point\n"
            "\n**Returns:**\n"
            "Dictionary containing the line ID and status information."
        ),
        "function": draw_line_rhino
    },
    {
        "name": "get_rhino_info",
        "description": (
            "Get information about the current Rhino session and document. "
            "This tool provides details about the Rhino version, document units, "
            "and current session status."
        ),
        "function": get_rhino_info
    }
]

# Future Rhino tools can be added here:
# - draw_curve_rhino
# - create_surface_rhino  
# - extrude_curve_rhino
# - boolean_operations_rhino
# - etc.