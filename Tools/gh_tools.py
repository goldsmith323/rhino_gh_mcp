"""
Grasshopper Tools

This module contains all Grasshopper-specific MCP tools that communicate with the
Rhino bridge server to execute parametric operations within Grasshopper.

Author: Hossein Zargar
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Import bridge_client from MCP directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MCP'))
from bridge_client import call_bridge_api

async def list_grasshopper_sliders() -> Dict[str, Any]:
    """
    List all slider components in the current Grasshopper definition via HTTP bridge.
    
    Returns:
        Dict containing slider information
    """
    
    return call_bridge_api("/list_sliders", {})

async def set_grasshopper_slider(slider_name: str, new_value: float) -> Dict[str, Any]:
    """
    Set the value of a Grasshopper slider by name via HTTP bridge.
    
    Args:
        slider_name: Name of the slider component
        new_value: New value to set
        
    Returns:
        Dict containing operation results
    """
    
    request_data = {
        "slider_name": slider_name,
        "new_value": new_value
    }
    
    return call_bridge_api("/set_slider", request_data)

# Tool definitions for MCP registration
GRASSHOPPER_TOOLS = [
    {
        "name": "list_grasshopper_sliders",
        "description": (
            "List all available slider components in the current Grasshopper definition. "
            "This tool scans the active Grasshopper document to find all number slider components "
            "and returns their names and current values. Use this to discover what sliders "
            "are available for modification.\n\n"
            "**Returns:**\n"
            "Dictionary containing list of sliders with their names and current values."
        ),
        "function": list_grasshopper_sliders
    },
    {
        "name": "set_grasshopper_slider",
        "description": (
            "Change the value of a Grasshopper slider component by name. "
            "This tool finds a slider component with the specified name and updates its value. "
            "Use 'list_grasshopper_sliders' first to see available sliders.\n\n"
            "**Parameters:**\n"
            "- **slider_name** (str): The name/nickname of the slider component to modify\n"
            "- **new_value** (float): The new value to set for the slider\n"
            "\n**Returns:**\n"
            "Dictionary containing the operation status and updated slider information."
        ),
        "function": set_grasshopper_slider
    }
]

# Future Grasshopper tools can be added here:
# - get_grasshopper_components
# - set_grasshopper_toggle  
# - run_grasshopper_solution
# - bake_grasshopper_geometry
# - get_grasshopper_data_tree
# - etc.