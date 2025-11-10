"""
Rhino 3D Tools - Early Integration

This module contains basic Rhino tools extracted from the production codebase.
These are the EXACT same functions used in production, just fewer of them.

Tools are automatically registered using the @rhino_tool decorator.
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
    from .tool_registry import rhino_tool, bridge_handler
except ImportError:
    # Fallback for direct import
    from tool_registry import rhino_tool, bridge_handler

# Get DEBUG_MODE from environment
DEBUG_MODE = False
try:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    env_file = os.path.join(project_root, '.env')

    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() == 'DEBUG_MODE':
                        DEBUG_MODE = value.strip().lower() == 'true'
                        break
    else:
        DEBUG_MODE = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
except:
    DEBUG_MODE = False

def filter_debug_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Filter response based on DEBUG_MODE to save tokens"""
    if DEBUG_MODE:
        return response

    filtered = {}
    essential_keys = [
        'success', 'error', 'message', 'warning',
        'line_id', 'point_count', 'truss_type', 'member_count',
        'version', 'document_name', 'unit_system'
    ]

    for key in essential_keys:
        if key in response:
            filtered[key] = response[key]

    # Include debug info only on errors
    if not response.get('success', True):
        if 'traceback' in response:
            filtered['traceback'] = response['traceback']

    # Copy unhandled keys
    for key, value in response.items():
        if key not in essential_keys and key not in ['traceback']:
            filtered[key] = value

    return filtered

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

@bridge_handler("/draw_line")
def handle_draw_line(data):
    """Bridge handler for line drawing requests"""
    try:
        # Import Rhino modules here since this runs inside Rhino
        import rhinoscriptsyntax as rs

        # Extract coordinates
        start_x = float(data.get('start_x', 0))
        start_y = float(data.get('start_y', 0))
        start_z = float(data.get('start_z', 0))
        end_x = float(data.get('end_x', 0))
        end_y = float(data.get('end_y', 0))
        end_z = float(data.get('end_z', 0))

        # Create the line in Rhino
        start_point = [start_x, start_y, start_z]
        end_point = [end_x, end_y, end_z]

        line_id = rs.AddLine(start_point, end_point)

        if line_id:
            line_length = rs.CurveLength(line_id)
            result = {
                "success": True,
                "line_id": str(line_id),
                "start_point": start_point,
                "end_point": end_point,
                "length": line_length,
                "message": f"Line created successfully with length {line_length:.2f}"
            }
            return filter_debug_response(result)
        else:
            result = {
                "success": False,
                "error": "Failed to create line in Rhino",
                "line_id": None
            }
            return filter_debug_response(result)
    except ImportError:
        result = {
            "success": False,
            "error": "Rhino is not available",
            "line_id": None
        }
        return filter_debug_response(result)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error drawing line: {str(e)}",
            "line_id": None
        }
        return filter_debug_response(result)

# All tools automatically registered via decorators
