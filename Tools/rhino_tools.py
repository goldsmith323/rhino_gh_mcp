"""
Rhino 3D Tools

This module contains all Rhino-specific MCP tools that communicate with the
Rhino bridge server to execute operations within Rhino 3D.

Tools are automatically registered using the @rhino_tool decorator.

Author: Hossein Zargar
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Import bridge_client from MCP directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MCP'))
from bridge_client import call_bridge_api

# Import the decorator system
try:
    from .tool_registry import rhino_tool
except ImportError:
    # Fallback for direct import
    from tool_registry import rhino_tool

@rhino_tool(
    name="draw_line_rhino",
    description=(
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
    )
)
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

@rhino_tool(
    name="get_rhino_info",
    description=(
        "Get information about the current Rhino session and document. "
        "This tool provides details about the Rhino version, document units, "
        "and current session status."
    )
)
async def get_rhino_info() -> Dict[str, Any]:
    """
    Get information about the current Rhino session via HTTP bridge.
    
    Returns:
        Dict containing Rhino session information
    """
    
    return call_bridge_api("/get_rhino_info", {})

@rhino_tool(
    name="typical_roof_truss_generator",
    description=(
        "Generate a typical roof truss structure in Rhino based on an upper chord line. "
        "This tool creates a complete truss with top chord, bottom chord, and web members.\n\n"
        "**IMPORTANT:** This tool requires explicit user input. Do NOT call with default values. "
        "Always ask the user to specify all required parameters before calling this tool.\n\n"
        "**Required User Input (ASK USER FOR THESE):**\n"
        "1. Upper chord line coordinates (start and end points)\n"
        "2. Truss depth (vertical distance from top to bottom chord)\n"
        "3. Number of divisions/bays\n"
        "4. Truss type (optional - defaults to Pratt)\n\n"
        "**Available Truss Types:**\n"
        "- **Pratt**: Vertical members with diagonals in compression\n"
        "- **Warren**: No verticals, alternating diagonal members\n"
        "- **Vierendeel**: Rectangular panels with moment connections\n"
        "- **Brown**: Similar to Pratt but with different diagonal orientation\n"
        "- **Howe**: Vertical members with diagonals in tension\n"
        "- **Onedir**: Single direction diagonals only\n\n"
        "**Parameters:**\n"
        "- **upper_line_start_x** (float): X-coordinate of upper line start point (ASK USER)\n"
        "- **upper_line_start_y** (float): Y-coordinate of upper line start point (ASK USER)\n"
        "- **upper_line_start_z** (float): Z-coordinate of upper line start point (ASK USER)\n"
        "- **upper_line_end_x** (float): X-coordinate of upper line end point (ASK USER)\n"
        "- **upper_line_end_y** (float): Y-coordinate of upper line end point (ASK USER)\n"
        "- **upper_line_end_z** (float): Z-coordinate of upper line end point (ASK USER)\n"
        "- **truss_depth** (float): Vertical depth of truss (ASK USER)\n"
        "- **num_divisions** (int): Number of truss divisions/bays (ASK USER, minimum 2)\n"
        "- **truss_type** (str): Type of truss (Pratt, Warren, Vierendeel, Brown, Howe, Onedir)\n"
        "- **clear_previous** (bool): Clear previously generated truss objects (default: true)\n"
        "- **truss_plane_direction** (str): Direction of truss plane (default: 'perpendicular')\n"
        "\n**Returns:**\n"
        "Dictionary containing truss generation results, member IDs, and geometry information."
    )
)
async def typical_roof_truss_generator(
    upper_line_start_x: float,
    upper_line_start_y: float,
    upper_line_start_z: float,
    upper_line_end_x: float,
    upper_line_end_y: float,
    upper_line_end_z: float,
    truss_depth: float,
    num_divisions: int,
    truss_type: str = "Pratt",
    clear_previous: bool = True,
    truss_plane_direction: str = "perpendicular"
) -> Dict[str, Any]:
    """
    Generate a typical roof truss structure based on an upper chord line.
    
    IMPORTANT: This tool requires the user to explicitly specify the upper chord line coordinates.
    Do NOT call this tool with default values - always ask the user to define:
    1. The upper chord line (start and end points)  
    2. Truss depth
    3. Number of divisions
    4. Truss type (optional)
    
    Available truss types:
    - Pratt: Vertical members with diagonals in compression
    - Warren: No verticals, alternating diagonal members
    - Vierendeel: Rectangular panels with moment connections
    - Brown: Similar to Pratt but with different diagonal orientation
    - Howe: Vertical members with diagonals in tension
    - Onedir: Single direction diagonals only
    
    Args:
        upper_line_start_x: X-coordinate of upper line start point (REQUIRED from user)
        upper_line_start_y: Y-coordinate of upper line start point (REQUIRED from user)
        upper_line_start_z: Z-coordinate of upper line start point (REQUIRED from user)
        upper_line_end_x: X-coordinate of upper line end point (REQUIRED from user)
        upper_line_end_y: Y-coordinate of upper line end point (REQUIRED from user)
        upper_line_end_z: Z-coordinate of upper line end point (REQUIRED from user)
        truss_depth: Vertical depth of the truss (REQUIRED from user)
        num_divisions: Number of truss divisions/bays (REQUIRED from user, minimum 2)
        truss_type: Type of truss (Pratt, Warren, Vierendeel, Brown, Howe, Onedir)
        clear_previous: Whether to clear previously generated truss objects
        truss_plane_direction: Direction of truss plane ("perpendicular" for auto-perpendicular)
        
    Returns:
        Dict containing truss generation results
    """
    
    request_data = {
        "upper_line_start_x": upper_line_start_x,
        "upper_line_start_y": upper_line_start_y,
        "upper_line_start_z": upper_line_start_z,
        "upper_line_end_x": upper_line_end_x,
        "upper_line_end_y": upper_line_end_y,
        "upper_line_end_z": upper_line_end_z,
        "truss_depth": truss_depth,
        "num_divisions": num_divisions,
        "truss_type": truss_type,
        "clear_previous": clear_previous,
        "truss_plane_direction": truss_plane_direction
    }
    
    return call_bridge_api("/generate_truss", request_data)

# All tools are now automatically registered using the @rhino_tool decorator
# Simply add @rhino_tool decorator to any new function and it will be available in MCP
#
# Future Rhino tools can be added here:
# - draw_curve_rhino
# - create_surface_rhino  
# - extrude_curve_rhino
# - boolean_operations_rhino
# - etc.