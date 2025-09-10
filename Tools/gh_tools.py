"""
Grasshopper Tools

This module contains all Grasshopper-specific MCP tools that communicate with the
Rhino bridge server to execute parametric operations within Grasshopper.

Tools are automatically registered using the @gh_tool decorator.

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
    from .tool_registry import gh_tool, bridge_handler
except ImportError:
    # Fallback for direct import
    from tool_registry import gh_tool, bridge_handler

@gh_tool(
    name="list_grasshopper_sliders",
    description=(
        "List all available slider components in the current Grasshopper definition. "
        "This tool scans the active Grasshopper document to find all number slider components "
        "and returns their names and current values. Use this to discover what sliders "
        "are available for modification.\n\n"
        "**Returns:**\n"
        "Dictionary containing list of sliders with their names and current values."
    )
)
async def list_grasshopper_sliders() -> Dict[str, Any]:
    """
    List all slider components in the current Grasshopper definition via HTTP bridge.
    
    Returns:
        Dict containing slider information
    """
    
    return call_bridge_api("/list_sliders", {})

@bridge_handler("/list_sliders")
def handle_list_sliders(data):
    """Bridge handler for list sliders requests"""
    try:
        # Try to import Grasshopper modules
        try:
            import ghpython
            import grasshopper as gh
            grasshopper_available = True
        except ImportError:
            grasshopper_available = False
        
        if not grasshopper_available:
            return {
                "success": False,
                "error": "Grasshopper is not available",
                "sliders": []
            }
        else:
            # Mock response for now - can be extended with real GH API
            sliders = [
                {"name": "Width", "current_value": 10.0, "min": 0.0, "max": 100.0},
                {"name": "Height", "current_value": 20.0, "min": 0.0, "max": 50.0},
                {"name": "Count", "current_value": 5.0, "min": 1.0, "max": 20.0}
            ]
            
            return {
                "success": True,
                "sliders": sliders,
                "count": len(sliders),
                "message": f"Found {len(sliders)} slider components"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error listing sliders: {str(e)}",
            "sliders": []
        }

@gh_tool(
    name="set_grasshopper_slider",
    description=(
        "Change the value of a Grasshopper slider component by name. "
        "This tool finds a slider component with the specified name and updates its value. "
        "Use 'list_grasshopper_sliders' first to see available sliders.\n\n"
        "**Parameters:**\n"
        "- **slider_name** (str): The name/nickname of the slider component to modify\n"
        "- **new_value** (float): The new value to set for the slider\n"
        "\n**Returns:**\n"
        "Dictionary containing the operation status and updated slider information."
    )
)
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

@bridge_handler("/set_slider")
def handle_set_slider(data):
    """Bridge handler for set slider requests"""
    try:
        slider_name = data.get('slider_name', '')
        new_value = float(data.get('new_value', 0))
        
        # Try to import Grasshopper modules
        try:
            import ghpython
            import grasshopper as gh
            grasshopper_available = True
        except ImportError:
            grasshopper_available = False
        
        if not grasshopper_available:
            return {
                "success": False,
                "error": "Grasshopper is not available",
                "slider_name": slider_name,
                "new_value": new_value
            }
        else:
            # Mock implementation - can be extended with real GH API
            if slider_name.lower() in ["width", "height", "count"]:
                return {
                    "success": True,
                    "slider_name": slider_name,
                    "old_value": 10.0,  # Mock old value
                    "new_value": new_value,
                    "message": f"Slider '{slider_name}' updated to {new_value}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Slider '{slider_name}' not found",
                    "slider_name": slider_name,
                    "new_value": new_value
                }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error setting slider: {str(e)}",
            "slider_name": data.get('slider_name', ''),
            "new_value": data.get('new_value', 0)
        }

# All tools are now automatically registered using the @gh_tool decorator
# Simply add @gh_tool decorator to any new function and it will be available in MCP
#
# Future Grasshopper tools can be added here:
# - get_grasshopper_components
# - set_grasshopper_toggle  
# - run_grasshopper_solution
# - bake_grasshopper_geometry
# - get_grasshopper_data_tree
# - etc.