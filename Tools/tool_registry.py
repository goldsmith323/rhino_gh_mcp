"""
Tool Registry and Decorator System

This module provides decorators and auto-discovery functionality for MCP tools.
Developers can simply use @rhino_tool or @gh_tool decorators to register tools
without manually updating registration lists.

Author: Hossein Zargar
"""

import inspect
import importlib
import os
from typing import Dict, Any, List, Callable, Optional
from functools import wraps

# Global registries for discovered tools
_rhino_tools = []
_gh_tools = []
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

def bridge_handler(endpoint: str):
    """
    Decorator to register bridge endpoint handlers automatically.
    
    Usage:
        @bridge_handler("/draw_line")
        def handle_draw_line(data):
            # Bridge endpoint implementation
            return {"success": True, "result": "..."}
    """
    def decorator(func: Callable):
        # Register in global bridge handlers registry
        _bridge_handlers[endpoint] = func
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def discover_tools() -> Dict[str, List[ToolDefinition]]:
    """
    Discover all registered tools by importing tool modules.
    
    This function imports all Python files in the Tools directory,
    which triggers the decorator registration.
    
    Returns:
        Dictionary with 'rhino' and 'grasshopper' tool lists
    """
    # Clear existing registries
    global _rhino_tools, _gh_tools, _bridge_handlers
    _rhino_tools.clear()
    _gh_tools.clear()
    _bridge_handlers.clear()
    
    # Get the Tools directory path
    tools_dir = os.path.dirname(__file__)
    
    # Import all Python modules in Tools directory
    for filename in os.listdir(tools_dir):
        if filename.endswith('.py') and filename != '__init__.py' and filename != 'tool_registry.py':
            module_name = filename[:-3]  # Remove .py extension
            try:
                # Import the module to trigger decorator registration
                # First try with current working directory context
                original_cwd = os.getcwd()
                try:
                    os.chdir(tools_dir)
                    importlib.import_module(module_name)
                    print(f"Discovered tools from: {module_name}")
                except ImportError:
                    # Try with Tools prefix
                    os.chdir(original_cwd)
                    importlib.import_module(f'Tools.{module_name}')
                    print(f"Discovered tools from: {module_name} (Tools prefix)")
                finally:
                    os.chdir(original_cwd)
            except Exception as e:
                print(f"Warning: Could not import {module_name}: {e}")
    
    return {
        'rhino': _rhino_tools,
        'grasshopper': _gh_tools
    }

def get_rhino_tools() -> List[Dict[str, Any]]:
    """Get all registered Rhino tools in MCP format"""
    return [tool.to_dict() for tool in _rhino_tools]

def get_gh_tools() -> List[Dict[str, Any]]:
    """Get all registered Grasshopper tools in MCP format"""
    return [tool.to_dict() for tool in _gh_tools]

def get_all_tools() -> List[Dict[str, Any]]:
    """Get all registered tools in MCP format"""
    return get_rhino_tools() + get_gh_tools()

def get_tool_endpoints() -> List[str]:
    """Get all bridge endpoints needed for registered tools"""
    return list(_bridge_handlers.keys())

def get_bridge_handlers() -> Dict[str, Callable]:
    """Get all registered bridge handlers"""
    return _bridge_handlers.copy()

def get_bridge_handler(endpoint: str) -> Optional[Callable]:
    """Get a specific bridge handler by endpoint"""
    return _bridge_handlers.get(endpoint)