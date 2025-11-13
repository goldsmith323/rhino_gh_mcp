"""
Tool Registry and Decorator System

This module provides decorators and auto-discovery functionality for MCP tools.
Developers can simply use @rhino_tool or @gh_tool decorators to register tools
without manually updating registration lists.
"""

import importlib
import os
import sys
from typing import Dict, Any, List, Callable, Optional
from functools import wraps

# Global registries for discovered tools
_rhino_tools = []
_gh_tools = []
_custom_tools = []
_bridge_handlers = {}

class ToolDefinition:
    """Represents a registered tool definition"""
    
    def __init__(self, name: str, description: str, function: Callable, tool_type: str):
        self.name = name
        self.description = description
        self.function = function
        self.tool_type = tool_type
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for MCP registration"""
        return {
            "name": self.name,
            "description": self.description,
            "function": self.function
        }

def rhino_tool(name: str = None, description: str = None):
    """
    Decorator to register Rhino MCP tools automatically.
    
    Usage:
        @rhino_tool(name="my_tool", description="Does something cool")
        async def my_tool_function(param1: float):
            return call_bridge_api("/my_endpoint", {"param1": param1})
    """
    def decorator(func: Callable):
        tool_name = name if name else func.__name__
        tool_description = description if description else f"Rhino tool: {func.__name__}"
        
        # Create tool definition
        tool_def = ToolDefinition(
            name=tool_name,
            description=tool_description,
            function=func,
            tool_type="rhino"
        )
        
        # Register in global registry
        _rhino_tools.append(tool_def)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def gh_tool(name: str = None, description: str = None):
    """
    Decorator to register Grasshopper MCP tools automatically.
    
    Usage:
        @gh_tool(name="my_gh_tool", description="Controls Grasshopper")
        async def my_gh_tool_function(param1: str):
            return call_bridge_api("/my_gh_endpoint", {"param1": param1})
    """
    def decorator(func: Callable):
        tool_name = name if name else func.__name__
        tool_description = description if description else f"Grasshopper tool: {func.__name__}"
        
        # Create tool definition
        tool_def = ToolDefinition(
            name=tool_name,
            description=tool_description,
            function=func,
            tool_type="grasshopper"
        )
        
        # Register in global registry
        _gh_tools.append(tool_def)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def custom_tool(name: str = None, description: str = None):
    """
    Decorator to register custom/generic MCP tools automatically.
    Use for tools that don't specifically require Rhino or Grasshopper.

    Usage:
        @custom_tool(name="my_tool", description="Does something useful")
        async def my_tool_function(param1: str):
            return call_bridge_api("/my_endpoint", {"param1": param1})
    """
    def decorator(func: Callable):
        tool_name = name if name else func.__name__
        tool_description = description if description else f"Custom tool: {func.__name__}"

        # Create tool definition
        tool_def = ToolDefinition(
            name=tool_name,
            description=tool_description,
            function=func,
            tool_type="custom"
        )

        # Register in global registry
        _custom_tools.append(tool_def)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator

def bridge_handler(endpoint: str):
    """
    Decorator to register bridge endpoint handlers automatically with comprehensive error handling.

    Usage:
        @bridge_handler("/draw_line")
        def handle_draw_line(data):
            # Bridge endpoint implementation
            return {"success": True, "result": "..."}
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import traceback
            import sys

            try:
                # Log the handler call for debugging
                print(f"[BRIDGE] Executing handler for endpoint: {endpoint}")
                print(f"[BRIDGE] Handler function: {func.__name__}")
                print(f"[BRIDGE] Request data: {args[0] if args else kwargs}")

                # Execute the actual handler
                result = func(*args, **kwargs)

                # Validate that result is a dictionary
                if not isinstance(result, dict):
                    error_msg = f"Handler {func.__name__} returned non-dict type: {type(result).__name__}"
                    print(f"[BRIDGE ERROR] {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "error_type": "InvalidReturnType",
                        "endpoint": endpoint,
                        "handler_function": func.__name__,
                        "returned_type": str(type(result)),
                        "debug_hint": "Bridge handlers must return a dictionary with at least a 'success' key"
                    }

                # Ensure the result has a success field
                if 'success' not in result:
                    print(f"[BRIDGE WARNING] Handler {func.__name__} returned dict without 'success' field. Adding it.")
                    result['success'] = True

                print(f"[BRIDGE] Handler {func.__name__} completed successfully")
                return result

            except Exception as e:
                # Comprehensive error handling
                error_traceback = traceback.format_exc()
                error_type = type(e).__name__
                error_msg = str(e)

                # Print detailed error to console
                print(f"[BRIDGE ERROR] Exception in handler {func.__name__} for endpoint {endpoint}")
                print(f"[BRIDGE ERROR] Exception type: {error_type}")
                print(f"[BRIDGE ERROR] Exception message: {error_msg}")
                print(f"[BRIDGE ERROR] Request data: {args[0] if args else kwargs}")
                print(f"[BRIDGE ERROR] Full traceback:")
                print(error_traceback)

                # Extract file and line number from traceback
                # Look for any .py file in the Tools directory
                tb_lines = error_traceback.split('\n')
                file_line_info = "Unknown"
                tools_dir = os.path.dirname(__file__)
                for line in tb_lines:
                    if 'File' in line and '.py' in line:
                        # Check if it's a file in the Tools directory
                        if 'Tools' in line or tools_dir in line:
                            file_line_info = line.strip()
                            break

                # Return comprehensive error information
                return {
                    "success": False,
                    "error": f"{error_type}: {error_msg}",
                    "error_type": error_type,
                    "error_message": error_msg,
                    "endpoint": endpoint,
                    "handler_function": func.__name__,
                    "file_line": file_line_info,
                    "traceback": error_traceback,
                    "traceback_lines": tb_lines[-10:],  # Last 10 lines of traceback
                    "request_data": args[0] if args else kwargs,
                    "python_version": sys.version,
                    "debug_hint": "An exception occurred in the bridge handler. See 'traceback' field for full details and check Rhino Python console."
                }

        # Register the wrapped function in the handlers registry
        _bridge_handlers[endpoint] = wrapper
        return wrapper

    return decorator

def discover_tools() -> Dict[str, List[ToolDefinition]]:
    """
    Discover all registered tools by importing tool modules.

    This function dynamically imports all Python files in the Tools directory,
    which triggers the decorator registration. It handles module reloading to
    ensure new tools are discovered even if the module was previously imported.

    Returns:
        Dictionary with 'rhino' and 'grasshopper' tool lists
    """
    # Clear existing registries
    global _rhino_tools, _gh_tools, _custom_tools, _bridge_handlers
    _rhino_tools.clear()
    _gh_tools.clear()
    _custom_tools.clear()
    _bridge_handlers.clear()

    # Get the Tools directory path
    tools_dir = os.path.dirname(__file__)

    print(f"[DISCOVERY] Scanning Tools directory: {tools_dir}")

    # Import all Python modules in Tools directory
    discovered_files = []
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py') and filename != '__init__.py' and filename != 'tool_registry.py':
            discovered_files.append(filename)

    print(f"[DISCOVERY] Found {len(discovered_files)} tool files: {', '.join(discovered_files)}")

    for filename in discovered_files:
        module_name = filename[:-3]  # Remove .py extension
        try:
            # Import the module to trigger decorator registration
            # Only reload if module was already imported (to get latest changes)
            original_cwd = os.getcwd()
            try:
                os.chdir(tools_dir)

                # Try to import the module
                try:
                    # Check if module is already imported
                    module_already_imported = module_name in sys.modules

                    module = importlib.import_module(module_name)

                    # Only reload if it was already imported
                    if module_already_imported:
                        importlib.reload(module)
                        print(f"[DISCOVERY] Reloaded tools from: {module_name}.py")
                    else:
                        print(f"[DISCOVERY] Loaded tools from: {module_name}.py")
                except ImportError:
                    # Try with Tools prefix
                    os.chdir(original_cwd)
                    full_module_name = f'Tools.{module_name}'
                    module_already_imported = full_module_name in sys.modules

                    module = importlib.import_module(full_module_name)

                    # Only reload if it was already imported
                    if module_already_imported:
                        importlib.reload(module)
                        print(f"[DISCOVERY] Reloaded tools from: {module_name}.py (Tools prefix)")
                    else:
                        print(f"[DISCOVERY] Loaded tools from: {module_name}.py (Tools prefix)")
            finally:
                os.chdir(original_cwd)
        except Exception as e:
            print(f"[DISCOVERY] Warning: Could not import {module_name}.py: {e}")
            import traceback
            print(traceback.format_exc())

    print(f"[DISCOVERY] Registered {len(_rhino_tools)} Rhino tools, {len(_gh_tools)} Grasshopper tools, {len(_custom_tools)} Custom tools, {len(_bridge_handlers)} bridge handlers")

    return {
        'rhino': _rhino_tools,
        'grasshopper': _gh_tools,
        'custom': _custom_tools
    }

def get_rhino_tools() -> List[Dict[str, Any]]:
    """Get all registered Rhino tools in MCP format"""
    return [tool.to_dict() for tool in _rhino_tools]

def get_gh_tools() -> List[Dict[str, Any]]:
    """Get all registered Grasshopper tools in MCP format"""
    return [tool.to_dict() for tool in _gh_tools]

def get_custom_tools() -> List[Dict[str, Any]]:
    """Get all registered custom tools in MCP format"""
    return [tool.to_dict() for tool in _custom_tools]

def get_bridge_handlers() -> Dict[str, Callable]:
    """Get all registered bridge handlers"""
    return _bridge_handlers.copy()