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
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "sliders": []
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
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
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import System
        
        slider_name = data.get('slider_name', '')
        new_value = float(data.get('new_value', 0))
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "slider_name": slider_name,
                "new_value": new_value
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
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

@gh_tool(
    name="get_grasshopper_overview",
    description=(
        "Get an overview of the current Grasshopper definition including file information, "
        "component counts, and general structure. This provides a high-level summary "
        "of what's loaded in Grasshopper.\n\n"
        "**Returns:**\n"
        "Dictionary containing file info, component counts, and document status."
    )
)
async def get_grasshopper_overview() -> Dict[str, Any]:
    """
    Get overview of the current Grasshopper definition via HTTP bridge.
    
    Returns:
        Dict containing file overview information
    """
    
    return call_bridge_api("/grasshopper_overview", {})

@bridge_handler("/grasshopper_overview")
def handle_grasshopper_overview(data):
    """Bridge handler for grasshopper overview requests"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }
        
        # Count different component types
        component_counts = {}
        slider_count = 0
        panel_count = 0
        param_count = 0
        total_objects = 0
        
        for obj in gh_doc.Objects:
            total_objects += 1
            obj_type = type(obj).__name__
            component_counts[obj_type] = component_counts.get(obj_type, 0) + 1
            
            if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                slider_count += 1
            elif isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                panel_count += 1
            elif hasattr(obj, 'Category') and obj.Category == "Params":
                param_count += 1
        
        # Get document properties
        doc_properties = {
            "is_modified": gh_doc.IsModified,
            "is_enabled": gh_doc.Enabled,
            "object_count": total_objects,
            "slider_count": slider_count,
            "panel_count": panel_count,
            "parameter_count": param_count
        }
        
        # Try to get file path if available
        file_path = "Unknown"
        if hasattr(gh_doc, 'FilePath') and gh_doc.FilePath:
            file_path = gh_doc.FilePath
        
        return {
            "success": True,
            "file_path": file_path,
            "document_properties": doc_properties,
            "component_counts": component_counts,
            "summary": f"Document contains {total_objects} total objects including {slider_count} sliders and {panel_count} panels"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error getting overview: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="analyze_grasshopper_sliders",
    description=(
        "Analyze all sliders in the current Grasshopper definition, including their connections "
        "and inferred purposes. This provides detailed information about what each slider controls "
        "based on connected components and naming patterns.\n\n"
        "**Returns:**\n"
        "Dictionary containing detailed slider analysis with connections and purposes."
    )
)
async def analyze_grasshopper_sliders() -> Dict[str, Any]:
    """
    Analyze sliders with connection details and purpose inference via HTTP bridge.
    
    Returns:
        Dict containing detailed slider analysis
    """
    
    return call_bridge_api("/analyze_sliders", {})

@bridge_handler("/analyze_sliders")
def handle_analyze_sliders(data):
    """Bridge handler for slider analysis requests"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
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
                    "type": obj.Slider.Type.ToString(),
                    "connected_components": [],
                    "inferred_purpose": "Unknown",
                    "position": {"x": float(obj.Attributes.Pivot.X), "y": float(obj.Attributes.Pivot.Y)}
                }
                
                # Analyze connections
                if obj.Params.Output.Count > 0:
                    output_param = obj.Params.Output[0]
                    for recipient in output_param.Recipients:
                        component = recipient.Attributes.GetTopLevel.DocObject
                        if component:
                            connected_info = {
                                "component_name": component.NickName or type(component).__name__,
                                "component_type": type(component).__name__,
                                "parameter_name": recipient.NickName or recipient.Name,
                                "parameter_description": recipient.Description if hasattr(recipient, 'Description') else ""
                            }
                            slider_info["connected_components"].append(connected_info)
                
                # Infer purpose based on name and connections
                slider_name_lower = slider_info["name"].lower()
                connected_types = [conn["component_type"] for conn in slider_info["connected_components"]]
                
                if any(keyword in slider_name_lower for keyword in ["width", "w", "x"]):
                    slider_info["inferred_purpose"] = "Width/X-dimension control"
                elif any(keyword in slider_name_lower for keyword in ["height", "h", "y"]):
                    slider_info["inferred_purpose"] = "Height/Y-dimension control"
                elif any(keyword in slider_name_lower for keyword in ["depth", "d", "z"]):
                    slider_info["inferred_purpose"] = "Depth/Z-dimension control"
                elif any(keyword in slider_name_lower for keyword in ["count", "num", "n"]):
                    slider_info["inferred_purpose"] = "Count/quantity control"
                elif any(keyword in slider_name_lower for keyword in ["angle", "rot", "rotation"]):
                    slider_info["inferred_purpose"] = "Angle/rotation control"
                elif any(keyword in slider_name_lower for keyword in ["scale", "size"]):
                    slider_info["inferred_purpose"] = "Scale/size control"
                elif any(keyword in slider_name_lower for keyword in ["offset", "shift"]):
                    slider_info["inferred_purpose"] = "Offset/position control"
                elif "GH_Move" in connected_types or "Transform" in connected_types:
                    slider_info["inferred_purpose"] = "Transformation parameter"
                elif "GH_Divide" in connected_types or "Division" in connected_types:
                    slider_info["inferred_purpose"] = "Division/array parameter"
                elif len(slider_info["connected_components"]) > 0:
                    slider_info["inferred_purpose"] = f"Parameter for {slider_info['connected_components'][0]['component_name']}"
                
                sliders.append(slider_info)
        
        return {
            "success": True,
            "sliders": sliders,
            "count": len(sliders),
            "summary": f"Found {len(sliders)} sliders with connection analysis"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error analyzing sliders: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="get_grasshopper_components",
    description=(
        "Get a comprehensive list of all components in the current Grasshopper definition, "
        "including their types, parameters, and connections. This provides a complete map "
        "of the grasshopper definition structure.\n\n"
        "**Returns:**\n"
        "Dictionary containing all components with their details and connections."
    )
)
async def get_grasshopper_components() -> Dict[str, Any]:
    """
    Get all components in the current Grasshopper definition via HTTP bridge.
    
    Returns:
        Dict containing all component information
    """
    
    return call_bridge_api("/get_components", {})

@bridge_handler("/get_components")
def handle_get_components(data):
    """Bridge handler for getting all components"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }
        
        components = []
        
        for obj in gh_doc.Objects:
            component_info = {
                "name": obj.NickName or "Unnamed",
                "type": type(obj).__name__,
                "category": obj.Category if hasattr(obj, 'Category') else "Unknown",
                "subcategory": obj.SubCategory if hasattr(obj, 'SubCategory') else "Unknown",
                "position": {"x": float(obj.Attributes.Pivot.X), "y": float(obj.Attributes.Pivot.Y)},
                "inputs": [],
                "outputs": [],
                "is_special": False,
                "special_type": None
            }
            
            # Check for special component types
            if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                component_info["is_special"] = True
                component_info["special_type"] = "NumberSlider"
                component_info["slider_info"] = {
                    "current_value": float(str(obj.Slider.Value)),
                    "min_value": float(str(obj.Slider.Minimum)),
                    "max_value": float(str(obj.Slider.Maximum)),
                    "precision": obj.Slider.DecimalPlaces
                }
            elif isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                component_info["is_special"] = True
                component_info["special_type"] = "Panel"
                component_info["panel_text"] = obj.UserText if hasattr(obj, 'UserText') else ""
            elif isinstance(obj, Grasshopper.Kernel.Special.GH_ValueList):
                component_info["is_special"] = True
                component_info["special_type"] = "ValueList"
                component_info["list_items"] = []
                if hasattr(obj, 'ListItems'):
                    for item in obj.ListItems:
                        component_info["list_items"].append({
                            "name": item.Name,
                            "value": str(item.Value)
                        })
            
            # Get input parameters
            if hasattr(obj, 'Params') and obj.Params.Input:
                for i in range(obj.Params.Input.Count):
                    param = obj.Params.Input[i]
                    param_info = {
                        "name": param.NickName or param.Name,
                        "description": param.Description if hasattr(param, 'Description') else "",
                        "type": type(param).__name__,
                        "optional": param.Optional,
                        "source_count": param.SourceCount
                    }
                    component_info["inputs"].append(param_info)
            
            # Get output parameters
            if hasattr(obj, 'Params') and obj.Params.Output:
                for i in range(obj.Params.Output.Count):
                    param = obj.Params.Output[i]
                    param_info = {
                        "name": param.NickName or param.Name,
                        "description": param.Description if hasattr(param, 'Description') else "",
                        "type": type(param).__name__,
                        "recipient_count": param.Recipients.Count
                    }
                    component_info["outputs"].append(param_info)
            
            components.append(component_info)
        
        # Group components by category
        categories = {}
        for comp in components:
            cat = comp["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(comp["name"])
        
        return {
            "success": True,
            "components": components,
            "total_count": len(components),
            "categories": categories,
            "special_components": [comp for comp in components if comp["is_special"]],
            "summary": f"Found {len(components)} total components across {len(categories)} categories"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error getting components: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="set_multiple_grasshopper_sliders",
    description=(
        "Set multiple Grasshopper slider values at once. This is efficient for batch "
        "updates when you need to change several parameters simultaneously.\n\n"
        "**Parameters:**\n"
        "- **slider_updates** (dict): Dictionary mapping slider names to new values\n"
        "\n**Returns:**\n"
        "Dictionary containing the results of all slider updates."
    )
)
async def set_multiple_grasshopper_sliders(slider_updates: Dict[str, float]) -> Dict[str, Any]:
    """
    Set multiple Grasshopper sliders at once via HTTP bridge.
    
    Args:
        slider_updates: Dictionary mapping slider names to new values
        
    Returns:
        Dict containing batch operation results
    """
    
    request_data = {"slider_updates": slider_updates}
    
    return call_bridge_api("/set_multiple_sliders", request_data)

@bridge_handler("/set_multiple_sliders")
def handle_set_multiple_sliders(data):
    """Bridge handler for setting multiple sliders at once"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import System
        
        slider_updates = data.get('slider_updates', {})
        if not slider_updates:
            return {
                "success": False,
                "error": "No slider updates provided"
            }
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }
        
        # Cache slider components for efficient batch processing
        slider_components = {}
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                slider_name = obj.NickName or "Unnamed"
                slider_components[slider_name] = obj
        
        results = []
        success_count = 0
        
        # Disable solver during batch updates
        gh.DisableSolver()
        
        try:
            for slider_name, new_value in slider_updates.items():
                try:
                    if slider_name in slider_components:
                        obj = slider_components[slider_name]
                        old_value = float(str(obj.Slider.Value))
                        
                        # Clamp value to slider bounds
                        clamped_value = max(float(str(obj.Slider.Minimum)), 
                                          min(float(str(obj.Slider.Maximum)), float(new_value)))
                        
                        obj.Slider.Value = System.Decimal.Parse(str(clamped_value))
                        
                        results.append({
                            "slider_name": slider_name,
                            "success": True,
                            "old_value": old_value,
                            "new_value": float(clamped_value),
                            "clamped": clamped_value != float(new_value)
                        })
                        success_count += 1
                    else:
                        results.append({
                            "slider_name": slider_name,
                            "success": False,
                            "error": f"Slider '{slider_name}' not found"
                        })
                        
                except Exception as e:
                    results.append({
                        "slider_name": slider_name,
                        "success": False,
                        "error": f"Error setting slider: {str(e)}"
                    })
            
            # Re-enable solver and compute solution
            gh.EnableSolver()
            gh_doc.NewSolution(True)
            
        except Exception as e:
            # Ensure solver is re-enabled even if batch update fails
            gh.EnableSolver()
            raise e
        
        return {
            "success": True,
            "results": results,
            "total_updates": len(slider_updates),
            "successful_updates": success_count,
            "failed_updates": len(slider_updates) - success_count,
            "summary": f"Successfully updated {success_count} of {len(slider_updates)} sliders"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error in batch slider update: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="debug_grasshopper_state",
    description=(
        "Get comprehensive debugging information about the current Grasshopper state. "
        "This tool provides detailed information for troubleshooting issues including "
        "plugin status, document state, component errors, and system information.\n\n"
        "**Returns:**\n"
        "Dictionary containing detailed debugging information about Grasshopper state."
    )
)
async def debug_grasshopper_state() -> Dict[str, Any]:
    """
    Get comprehensive debugging information about Grasshopper state via HTTP bridge.
    
    Returns:
        Dict containing detailed debugging information
    """
    
    return call_bridge_api("/debug_state", {})

@bridge_handler("/debug_state")
def handle_debug_state(data):
    """Bridge handler for debugging state requests"""
    try:
        import clr
        import sys
        import os
        
        debug_info = {
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "clr_version": str(clr.version) if hasattr(clr, 'version') else "Unknown"
            },
            "assemblies_loaded": [],
            "grasshopper_status": {},
            "document_status": {},
            "component_errors": [],
            "warnings": []
        }
        
        # Check loaded assemblies
        try:
            for assembly in clr.References:
                debug_info["assemblies_loaded"].append(str(assembly))
        except Exception as e:
            debug_info["warnings"].append(f"Could not enumerate assemblies: {str(e)}")
        
        try:
            clr.AddReference('Grasshopper')
            clr.AddReference('RhinoCommon')
            import Grasshopper
            import Rhino
            
            # Check Grasshopper plugin status
            gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
            if gh:
                debug_info["grasshopper_status"] = {
                    "plugin_available": True,
                    "plugin_type": str(type(gh)),
                    "is_loaded": True
                }
                
                # Check document status
                if Grasshopper.Instances.ActiveCanvas:
                    gh_doc = Grasshopper.Instances.ActiveCanvas.Document
                    if gh_doc:
                        debug_info["document_status"] = {
                            "document_available": True,
                            "is_modified": gh_doc.IsModified,
                            "is_enabled": gh_doc.Enabled,
                            "object_count": gh_doc.Objects.Count,
                            "file_path": gh_doc.FilePath if hasattr(gh_doc, 'FilePath') and gh_doc.FilePath else "Unsaved",
                            "solver_status": "Unknown"
                        }
                        
                        # Count component types and check for errors
                        component_summary = {}
                        error_count = 0
                        warning_count = 0
                        
                        for obj in gh_doc.Objects:
                            obj_type = type(obj).__name__
                            component_summary[obj_type] = component_summary.get(obj_type, 0) + 1
                            
                            # Check for component runtime messages (errors/warnings)
                            if hasattr(obj, 'RuntimeMessages'):
                                for message in obj.RuntimeMessages:
                                    message_info = {
                                        "component": obj.NickName or obj_type,
                                        "level": str(message.Level),
                                        "message": str(message.Text)
                                    }
                                    
                                    if "Error" in str(message.Level):
                                        error_count += 1
                                        debug_info["component_errors"].append(message_info)
                                    elif "Warning" in str(message.Level):
                                        warning_count += 1
                                        debug_info["warnings"].append(message_info)
                        
                        debug_info["document_status"]["component_summary"] = component_summary
                        debug_info["document_status"]["error_count"] = error_count
                        debug_info["document_status"]["warning_count"] = warning_count
                        
                    else:
                        debug_info["document_status"] = {
                            "document_available": False,
                            "error": "No active Grasshopper document"
                        }
                else:
                    debug_info["document_status"] = {
                        "document_available": False,
                        "error": "No active Grasshopper canvas"
                    }
            else:
                debug_info["grasshopper_status"] = {
                    "plugin_available": False,
                    "error": "Grasshopper plugin not found"
                }
                
        except ImportError as e:
            debug_info["grasshopper_status"] = {
                "plugin_available": False,
                "error": f"Cannot import Grasshopper: {str(e)}"
            }
        except Exception as e:
            debug_info["grasshopper_status"] = {
                "plugin_available": False,
                "error": f"Unexpected error: {str(e)}"
            }
        
        # Add environment info
        debug_info["environment"] = {
            "rhino_version": "Unknown",
            "grasshopper_version": "Unknown"
        }
        
        try:
            import Rhino
            debug_info["environment"]["rhino_version"] = str(Rhino.RhinoApp.Version)
        except:
            pass
            
        try:
            import Grasshopper
            if hasattr(Grasshopper, 'Versioning'):
                debug_info["environment"]["grasshopper_version"] = str(Grasshopper.Versioning.Version)
        except:
            pass
        
        return {
            "success": True,
            "debug_info": debug_info,
            "summary": f"Debug info collected - {len(debug_info['component_errors'])} errors, {len(debug_info['warnings'])} warnings"
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error collecting debug info: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="list_grasshopper_valuelist_components",
    description=(
        "List all ValueList components in the current Grasshopper definition. "
        "ValueList components are dropdown menus that contain predefined options. "
        "This tool returns their names, current selections, and available options.\n\n"
        "**Returns:**\n"
        "Dictionary containing list of ValueList components with their options and current selections."
    )
)
async def list_grasshopper_valuelist_components() -> Dict[str, Any]:
    """
    List all ValueList components in the current Grasshopper definition via HTTP bridge.
    
    Returns:
        Dict containing ValueList information
    """
    
    return call_bridge_api("/list_valuelists", {})

@bridge_handler("/list_valuelists")
def handle_list_valuelists(data):
    """Bridge handler for listing ValueList components"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "valuelist_components": []
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "valuelist_components": []
            }
        
        valuelist_components = []
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_ValueList):
                valuelist_info = {
                    "name": obj.NickName or "Unnamed",
                    "current_selection_index": obj.SelectionIndex,
                    "current_selection_name": None,
                    "current_selection_value": None,
                    "list_items": []
                }
                
                # Get all available items
                if hasattr(obj, 'ListItems'):
                    for i, item in enumerate(obj.ListItems):
                        item_info = {
                            "index": i,
                            "name": item.Name,
                            "value": str(item.Value)
                        }
                        valuelist_info["list_items"].append(item_info)
                        
                        # Mark current selection
                        if i == obj.SelectionIndex:
                            valuelist_info["current_selection_name"] = item.Name
                            valuelist_info["current_selection_value"] = str(item.Value)
                
                valuelist_components.append(valuelist_info)
        
        return {
            "success": True,
            "valuelist_components": valuelist_components,
            "count": len(valuelist_components),
            "message": f"Found {len(valuelist_components)} ValueList components"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "valuelist_components": []
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error listing ValueList components: {str(e)}",
            "traceback": traceback.format_exc(),
            "valuelist_components": []
        }

@gh_tool(
    name="set_grasshopper_valuelist_selection",
    description=(
        "Change the selected item in a Grasshopper ValueList component. "
        "This tool finds a ValueList component with the specified name and updates its selection. "
        "Use 'list_grasshopper_valuelist_components' first to see available ValueLists.\n\n"
        "**Parameters:**\n"
        "- **valuelist_name** (str): The name/nickname of the ValueList component to modify\n"
        "- **selection** (str or int): Either the name of the item to select or its index number\n"
        "\n**Returns:**\n"
        "Dictionary containing the operation status and updated ValueList information."
    )
)
async def set_grasshopper_valuelist_selection(valuelist_name: str, selection: str) -> Dict[str, Any]:
    """
    Set the selected item in a Grasshopper ValueList component via HTTP bridge.
    
    Args:
        valuelist_name: Name of the ValueList component
        selection: Name or index of the item to select
        
    Returns:
        Dict containing operation results
    """
    
    request_data = {
        "valuelist_name": valuelist_name,
        "selection": selection
    }
    
    return call_bridge_api("/set_valuelist_selection", request_data)

@bridge_handler("/set_valuelist_selection")
def handle_set_valuelist_selection(data):
    """Bridge handler for setting ValueList selection"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        valuelist_name = data.get('valuelist_name', '')
        selection = data.get('selection', '')
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "valuelist_name": valuelist_name,
                "selection": selection
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "valuelist_name": valuelist_name,
                "selection": selection
            }
        
        # Find the ValueList component
        valuelist_found = False
        old_selection = None
        new_selection_index = None
        new_selection_name = None
        new_selection_value = None
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_ValueList):
                if (obj.NickName or "Unnamed") == valuelist_name:
                    valuelist_found = True
                    old_selection = {
                        "index": obj.SelectionIndex,
                        "name": obj.ListItems[obj.SelectionIndex].Name if obj.SelectionIndex < len(obj.ListItems) else None,
                        "value": str(obj.ListItems[obj.SelectionIndex].Value) if obj.SelectionIndex < len(obj.ListItems) else None
                    }
                    
                    # Try to find the selection by name or index
                    selection_found = False
                    
                    # Try as index first
                    try:
                        index = int(selection)
                        if 0 <= index < len(obj.ListItems):
                            obj.SelectItem(index)
                            new_selection_index = index
                            new_selection_name = obj.ListItems[index].Name
                            new_selection_value = str(obj.ListItems[index].Value)
                            selection_found = True
                    except ValueError:
                        # Not an integer, try as name or value
                        for i, item in enumerate(obj.ListItems):
                            if item.Name == selection or str(item.Value) == selection:
                                obj.SelectItem(i)
                                new_selection_index = i
                                new_selection_name = item.Name
                                new_selection_value = str(item.Value)
                                selection_found = True
                                break
                    
                    if not selection_found:
                        available_options = [f"{i}: {item.Name} ({item.Value})" for i, item in enumerate(obj.ListItems)]
                        return {
                            "success": False,
                            "error": f"Selection '{selection}' not found in ValueList '{valuelist_name}'",
                            "available_options": available_options,
                            "valuelist_name": valuelist_name,
                            "selection": selection
                        }
                    
                    # Trigger solution recompute
                    gh_doc.NewSolution(True)
                    break
        
        if not valuelist_found:
            return {
                "success": False,
                "error": f"ValueList '{valuelist_name}' not found",
                "valuelist_name": valuelist_name,
                "selection": selection
            }
        
        return {
            "success": True,
            "valuelist_name": valuelist_name,
            "old_selection": old_selection,
            "new_selection": {
                "index": new_selection_index,
                "name": new_selection_name,
                "value": new_selection_value
            },
            "message": f"ValueList '{valuelist_name}' updated to '{new_selection_name}'"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "valuelist_name": data.get('valuelist_name', ''),
            "selection": data.get('selection', '')
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error setting ValueList selection: {str(e)}",
            "traceback": traceback.format_exc(),
            "valuelist_name": data.get('valuelist_name', ''),
            "selection": data.get('selection', '')
        }

@gh_tool(
    name="list_grasshopper_panels",
    description=(
        "List all Panel components in the current Grasshopper definition. "
        "Panel components display text data and can be used for both input and output. "
        "This tool returns their names and current text content.\n\n"
        "**Returns:**\n"
        "Dictionary containing list of Panel components with their text content."
    )
)
async def list_grasshopper_panels() -> Dict[str, Any]:
    """
    List all Panel components in the current Grasshopper definition via HTTP bridge.
    
    Returns:
        Dict containing Panel information
    """
    
    return call_bridge_api("/list_panels", {})

@bridge_handler("/list_panels")
def handle_list_panels(data):
    """Bridge handler for listing Panel components"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "panels": []
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "panels": []
            }
        
        panels = []
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                panel_info = {
                    "name": obj.NickName or "Unnamed",
                    "user_text": obj.UserText if hasattr(obj, 'UserText') else "",
                    "position": {"x": float(obj.Attributes.Pivot.X), "y": float(obj.Attributes.Pivot.Y)},
                    "volatile_data": []
                }
                
                # Try to extract volatile data (computed values)
                try:
                    if hasattr(obj, 'VolatileData') and obj.VolatileData:
                        vd = obj.VolatileData
                        # Try multiple ways to access the data
                        for path in vd.Paths:
                            branch = vd.get_Branch(path)
                            if branch:
                                for i in range(branch.Count):
                                    try:
                                        item = branch[i]
                                        if item is not None:
                                            # Try to get the actual value
                                            if hasattr(item, 'Value'):
                                                panel_info["volatile_data"].append(str(item.Value))
                                            else:
                                                panel_info["volatile_data"].append(str(item))
                                    except Exception:
                                        continue
                    
                    # Also try to get values from input parameters if panel is displaying input data
                    if hasattr(obj, 'Params') and obj.Params.Input and obj.Params.Input.Count > 0:
                        for i in range(obj.Params.Input.Count):
                            input_param = obj.Params.Input[i]
                            if hasattr(input_param, 'VolatileData') and input_param.VolatileData:
                                input_vd = input_param.VolatileData
                                for path in input_vd.Paths:
                                    branch = input_vd.get_Branch(path)
                                    if branch:
                                        for j in range(branch.Count):
                                            try:
                                                item = branch[j]
                                                if item is not None:
                                                    if hasattr(item, 'Value'):
                                                        panel_info["volatile_data"].append(str(item.Value))
                                                    else:
                                                        panel_info["volatile_data"].append(str(item))
                                            except Exception:
                                                continue
                                
                except Exception as e:
                    panel_info["volatile_data_error"] = f"Error extracting data: {str(e)}"
                
                panels.append(panel_info)
        
        return {
            "success": True,
            "panels": panels,
            "count": len(panels),
            "message": f"Found {len(panels)} Panel components"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "panels": []
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error listing Panel components: {str(e)}",
            "traceback": traceback.format_exc(),
            "panels": []
        }

@gh_tool(
    name="set_grasshopper_panel_text",
    description=(
        "Change the text content of a Grasshopper Panel component. "
        "This tool finds a Panel component with the specified name and updates its text. "
        "Use 'list_grasshopper_panels' first to see available Panels.\n\n"
        "**Parameters:**\n"
        "- **panel_name** (str): The name/nickname of the Panel component to modify\n"
        "- **new_text** (str): The new text content to set for the panel\n"
        "\n**Returns:**\n"
        "Dictionary containing the operation status and updated Panel information."
    )
)
async def set_grasshopper_panel_text(panel_name: str, new_text: str) -> Dict[str, Any]:
    """
    Set the text content of a Grasshopper Panel component via HTTP bridge.
    
    Args:
        panel_name: Name of the Panel component
        new_text: New text content to set
        
    Returns:
        Dict containing operation results
    """
    
    request_data = {
        "panel_name": panel_name,
        "new_text": new_text
    }
    
    return call_bridge_api("/set_panel_text", request_data)

@bridge_handler("/set_panel_text")
def handle_set_panel_text(data):
    """Bridge handler for setting Panel text"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        panel_name = data.get('panel_name', '')
        new_text = str(data.get('new_text', ''))
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "panel_name": panel_name,
                "new_text": new_text
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "panel_name": panel_name,
                "new_text": new_text
            }
        
        # Find the Panel component
        panel_found = False
        old_text = None
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                if (obj.NickName or "Unnamed") == panel_name:
                    panel_found = True
                    old_text = obj.UserText if hasattr(obj, 'UserText') else ""
                    
                    # Set the new text
                    obj.UserText = new_text
                    obj.ExpireSolution(True)
                    
                    # Trigger solution recompute
                    gh_doc.NewSolution(True)
                    break
        
        if not panel_found:
            return {
                "success": False,
                "error": f"Panel '{panel_name}' not found",
                "panel_name": panel_name,
                "new_text": new_text
            }
        
        return {
            "success": True,
            "panel_name": panel_name,
            "old_text": old_text,
            "new_text": new_text,
            "message": f"Panel '{panel_name}' text updated"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "panel_name": data.get('panel_name', ''),
            "new_text": data.get('new_text', '')
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error setting Panel text: {str(e)}",
            "traceback": traceback.format_exc(),
            "panel_name": data.get('panel_name', ''),
            "new_text": data.get('new_text', '')
        }

@gh_tool(
    name="get_grasshopper_panel_data",
    description=(
        "Extract data values from Grasshopper Panel components. "
        "This tool can extract computed values, text content, and other data from panels. "
        "Useful for reading output values like truss weight, calculations, or any data displayed in panels.\n\n"
        "**Parameters:**\n"
        "- **panel_name** (str, optional): Name of a specific panel to read, or leave empty to read all panels\n"
        "\n**Returns:**\n"
        "Dictionary containing panel data including text content and computed values."
    )
)
async def get_grasshopper_panel_data(panel_name: str = "") -> Dict[str, Any]:
    """
    Get data from Grasshopper Panel components via HTTP bridge.
    
    Args:
        panel_name: Name of specific panel to read (optional, reads all if empty)
        
    Returns:
        Dict containing panel data
    """
    
    request_data = {"panel_name": panel_name}
    
    return call_bridge_api("/get_panel_data", request_data)

@bridge_handler("/get_panel_data")
def handle_get_panel_data(data):
    """Bridge handler for getting Panel data"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        panel_name = data.get('panel_name', '')
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }
        
        panel_data = []
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                current_panel_name = obj.NickName or "Unnamed"
                
                # If specific panel requested, skip others
                if panel_name and current_panel_name != panel_name:
                    continue
                
                panel_info = {
                    "name": current_panel_name,
                    "user_text": obj.UserText if hasattr(obj, 'UserText') else "",
                    "volatile_data_text": "",
                    "volatile_data_list": [],
                    "position": {"x": float(obj.Attributes.Pivot.X), "y": float(obj.Attributes.Pivot.Y)},
                    "computed_values": [],
                    "display_text": ""
                }
                
                # Extract volatile data (computed values)
                try:
                    all_values = []
                    
                    if hasattr(obj, 'VolatileData') and obj.VolatileData:
                        vd = obj.VolatileData
                        
                        for path in vd.Paths:
                            branch = vd.get_Branch(path)
                            if branch:
                                for i in range(branch.Count):
                                    try:
                                        item = branch[i]
                                        if item is not None:
                                            # Try to get the actual value
                                            if hasattr(item, 'Value'):
                                                item_str = str(item.Value).replace('"', "'")
                                                all_values.append(item_str)
                                            else:
                                                item_str = str(item).replace('"', "'")
                                                all_values.append(item_str)
                                    except Exception:
                                        continue
                    
                    # Also try to get values from input parameters if panel is displaying input data
                    if hasattr(obj, 'Params') and obj.Params.Input and obj.Params.Input.Count > 0:
                        for i in range(obj.Params.Input.Count):
                            input_param = obj.Params.Input[i]
                            if hasattr(input_param, 'VolatileData') and input_param.VolatileData:
                                input_vd = input_param.VolatileData
                                for path in input_vd.Paths:
                                    branch = input_vd.get_Branch(path)
                                    if branch:
                                        for j in range(branch.Count):
                                            try:
                                                item = branch[j]
                                                if item is not None:
                                                    if hasattr(item, 'Value'):
                                                        item_str = str(item.Value).replace('"', "'")
                                                        all_values.append(item_str)
                                                    else:
                                                        item_str = str(item).replace('"', "'")
                                                        all_values.append(item_str)
                                            except Exception:
                                                continue
                    
                    panel_info["volatile_data_list"] = all_values
                    panel_info["volatile_data_text"] = ','.join(all_values) if all_values else ""
                    panel_info["computed_values"] = all_values
                    
                    # Try to extract display text from the panel itself
                    try:
                        if hasattr(obj, 'ToString'):
                            panel_info["display_text"] = str(obj.ToString())
                    except:
                        pass
                        
                    # Try alternative methods to get the actual displayed content
                    try:
                        if hasattr(obj, 'Properties'):
                            if hasattr(obj.Properties, 'Text'):
                                panel_info["display_text"] = str(obj.Properties.Text)
                    except:
                        pass
                        
                    # Try to get text from the panel's visual representation
                    try:
                        if hasattr(obj, 'GetValue'):
                            value = obj.GetValue(0, 0)  # Try to get first value
                            if value is not None:
                                panel_info["display_text"] = str(value)
                    except:
                        pass
                        
                except Exception as e:
                    panel_info["volatile_data_error"] = f"Could not extract volatile data: {str(e)}"
                
                panel_data.append(panel_info)
        
        if panel_name and not panel_data:
            return {
                "success": False,
                "error": f"Panel '{panel_name}' not found"
            }
        
        return {
            "success": True,
            "panel_data": panel_data,
            "count": len(panel_data),
            "message": f"Retrieved data from {len(panel_data)} panel(s)"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error getting Panel data: {str(e)}",
            "traceback": traceback.format_exc()
        }

# All tools are now automatically registered using the @gh_tool decorator
# Summary of available tools:
# 1. list_grasshopper_sliders - Basic slider listing
# 2. set_grasshopper_slider - Set individual slider value
# 3. get_grasshopper_overview - File overview and component counts
# 4. analyze_grasshopper_sliders - Detailed slider analysis with connections
# 5. get_grasshopper_components - Complete component mapping
# 6. set_multiple_grasshopper_sliders - Batch slider updates
# 7. debug_grasshopper_state - Comprehensive debugging information
# 8. list_grasshopper_valuelist_components - List ValueList components and options
# 9. set_grasshopper_valuelist_selection - Change ValueList selections
# 10. list_grasshopper_panels - List Panel components and text content
# 11. set_grasshopper_panel_text - Update Panel text content
# 12. get_grasshopper_panel_data - Extract data and values from Panels