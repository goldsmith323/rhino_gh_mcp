"""
Grasshopper Tools - Early Integration

This module contains basic Grasshopper tools extracted from the production codebase.
These are the EXACT same functions used in production, just fewer of them.

Tools are automatically registered using the @gh_tool decorator.
"""

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

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def ensure_file_is_active(file_name: str) -> Dict[str, Any]:
    """
    Helper function to check if a specific Grasshopper file is active.
    For Level 2 (Early Integration), this is a simplified version.

    Args:
        file_name: Name of the .gh file that should be active

    Returns:
        Dict with 'success' boolean and optional 'error' message
    """
    if not file_name:
        return {"success": True}  # No specific file requested, use whatever is active

    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import os

        # Check if requested file is already active
        if Grasshopper.Instances.ActiveCanvas and Grasshopper.Instances.ActiveCanvas.Document:
            active_doc = Grasshopper.Instances.ActiveCanvas.Document
            if active_doc.FilePath:
                active_file_name = os.path.basename(str(active_doc.FilePath))
                if active_file_name.lower() == file_name.lower():
                    return {"success": True}  # Already active

        # File not active - return error asking user to open it
        return {
            "success": False,
            "error": f"File '{file_name}' is not active. Please open the file in Grasshopper first."
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error checking file: {str(e)}",
            "traceback": traceback.format_exc()
        }

# ============================================================================
# GRASSHOPPER TOOLS
# ============================================================================

@gh_tool(
    name="get_active_gh_files",
    description=(
        "Get information about all currently open Grasshopper files. "
        "Returns details about each open document including file paths, "
        "names, and which one is currently active.\n\n"
        "**Returns:**\n"
        "Dictionary containing list of open Grasshopper documents."
    )
)
async def get_active_gh_files() -> Dict[str, Any]:
    """
    Get all currently open Grasshopper files.

    Returns:
        Dict containing information about open files
    """
    return call_bridge_api("/get_active_gh_files", {})

@bridge_handler("/get_active_gh_files")
def handle_get_active_gh_files(data):
    """Bridge handler for getting active .gh files"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import os

        # Get the Grasshopper plugin
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "open_files": []
            }

        open_files = []
        active_doc_path = None

        # Get the active document path
        if Grasshopper.Instances.ActiveCanvas and Grasshopper.Instances.ActiveCanvas.Document:
            active_doc = Grasshopper.Instances.ActiveCanvas.Document
            if active_doc.FilePath:
                active_doc_path = os.path.normpath(str(active_doc.FilePath)).lower()

        # Iterate through ALL open documents using DocumentServer
        doc_server = Grasshopper.Instances.DocumentServer
        if doc_server:
            for doc in doc_server:
                if doc and hasattr(doc, 'FilePath') and doc.FilePath:
                    file_path = str(doc.FilePath)
                    file_name = os.path.basename(file_path)
                    normalized_path = os.path.normpath(file_path).lower()

                    # Check if this is the active document
                    is_active = (active_doc_path is not None and normalized_path == active_doc_path)

                    open_files.append({
                        "name": file_name,
                        "path": file_path,
                        "is_active": is_active,
                        "is_modified": doc.IsModified if hasattr(doc, 'IsModified') else False,
                        "object_count": doc.ObjectCount if hasattr(doc, 'ObjectCount') else 0
                    })

        if len(open_files) == 0:
            return {
                "success": False,
                "error": "No open Grasshopper documents found",
                "open_files": []
            }

        return {
            "success": True,
            "open_files": open_files,
            "count": len(open_files),
            "message": f"Found {len(open_files)} open Grasshopper document(s)"
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error getting active files: {str(e)}",
            "traceback": traceback.format_exc(),
            "open_files": []
        }

@gh_tool(
    name="list_grasshopper_sliders",
    description=(
        "List all available slider components in a specific Grasshopper file. "
        "This tool will activate the specified file (making it visible to the user), "
        "then scan it to find all number slider components and return their names and current values.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, required): Name of the .gh file to list sliders from (e.g., 'Primary Truss Generator.gh')\n"
        "\n**Returns:**\n"
        "Dictionary containing list of sliders with their names and current values."
    )
)
async def list_grasshopper_sliders(file_name: str) -> Dict[str, Any]:
    """
    List all slider components in a specific Grasshopper file via HTTP bridge.

    Args:
        file_name: Name of the .gh file to list sliders from

    Returns:
        Dict containing slider information
    """

    request_data = {
        "file_name": file_name
    }

    return call_bridge_api("/list_sliders", request_data)

@bridge_handler("/list_sliders")
def handle_list_sliders(data):
    """Bridge handler for list sliders requests"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino

        file_name = data.get('file_name', '')

        # Ensure the correct file is active first
        activation_result = ensure_file_is_active(file_name)
        if not activation_result.get("success", False):
            return {
                "success": False,
                "error": activation_result.get("error", "Failed to activate file"),
                "file_name": file_name,
                "sliders": []
            }

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "file_name": file_name,
                "sliders": []
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "file_name": file_name,
                "sliders": []
            }

        sliders = []

        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                slider_info = {
                    "name": obj.NickName or "Unnamed",
                    "current_value": float(str(obj.Slider.Value)),
                    "min_value": float(str(obj.Slider.Minimum)),
                    "max_value": float(str(obj.Slider.Maximum)),
                    "precision": obj.Slider.DecimalPlaces,
                    "type": obj.Slider.Type.ToString()
                }
                sliders.append(slider_info)

        return {
            "success": True,
            "sliders": sliders,
            "count": len(sliders),
            "message": f"Found {len(sliders)} slider components"
        }

    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "sliders": []
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error listing sliders: {str(e)}",
            "traceback": traceback.format_exc(),
            "sliders": []
        }

@gh_tool(
    name="set_grasshopper_slider",
    description=(
        "Change the value of a Grasshopper slider component by name in a specific Grasshopper file. "
        "This tool will activate the specified file (making it visible to the user), "
        "then find the slider component and update its value. "
        "Use 'get_active_gh_files' to see all open files and 'list_grasshopper_sliders' to see available sliders.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, required): Name of the .gh file containing the slider (e.g., 'Primary Truss Generator.gh')\n"
        "- **slider_name** (str): The name/nickname of the slider component to modify\n"
        "- **new_value** (float): The new value to set for the slider\n"
        "\n**Returns:**\n"
        "Dictionary containing the operation status and updated slider information."
    )
)
async def set_grasshopper_slider(file_name: str, slider_name: str, new_value: float) -> Dict[str, Any]:
    """
    Set the value of a Grasshopper slider by name via HTTP bridge.

    Args:
        file_name: Name of the .gh file containing the slider
        slider_name: Name of the slider component
        new_value: New value to set

    Returns:
        Dict containing operation results
    """

    request_data = {
        "file_name": file_name,
        "slider_name": slider_name,
        "new_value": new_value
    }

    return call_bridge_api("/set_slider", request_data)

@bridge_handler("/set_slider")
def handle_set_slider(data):
    """Bridge handler for set slider requests"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import System

        file_name = data.get('file_name', '')
        slider_name = data.get('slider_name', '')
        new_value = float(data.get('new_value', 0))

        # Ensure the correct file is active first
        activation_result = ensure_file_is_active(file_name)
        if not activation_result.get("success", False):
            return {
                "success": False,
                "error": activation_result.get("error", "Failed to activate file"),
                "file_name": file_name,
                "slider_name": slider_name,
                "new_value": new_value
            }

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "file_name": file_name,
                "slider_name": slider_name,
                "new_value": new_value
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "file_name": file_name,
                "slider_name": slider_name,
                "new_value": new_value
            }

        # Find the slider component
        slider_found = False
        old_value = None
        clamped_value = new_value

        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                if (obj.NickName or "Unnamed") == slider_name:
                    slider_found = True
                    old_value = float(str(obj.Slider.Value))

                    # Clamp value to slider bounds
                    clamped_value = max(float(str(obj.Slider.Minimum)),
                                      min(float(str(obj.Slider.Maximum)), new_value))

                    # Set the new value
                    obj.Slider.Value = System.Decimal.Parse(str(clamped_value))

                    # Trigger solution recompute
                    gh_doc.NewSolution(True)

                    break

        if not slider_found:
            return {
                "success": False,
                "error": f"Slider '{slider_name}' not found",
                "slider_name": slider_name,
                "new_value": new_value
            }

        return {
            "success": True,
            "slider_name": slider_name,
            "old_value": old_value,
            "new_value": clamped_value,
            "clamped": clamped_value != new_value,
            "message": f"Slider '{slider_name}' updated to {clamped_value}" +
                      (f" (clamped from {new_value})" if clamped_value != new_value else "")
        }

    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "slider_name": data.get('slider_name', ''),
            "new_value": data.get('new_value', 0)
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error setting slider: {str(e)}",
            "traceback": traceback.format_exc(),
            "slider_name": data.get('slider_name', ''),
            "new_value": data.get('new_value', 0)
        }

# All tools automatically registered via decorators
