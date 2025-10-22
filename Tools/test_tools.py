"""
Test Tools

Simple test tools to verify dynamic discovery system is working correctly.
These tools can be used to test that new .py files are automatically discovered.
"""

import sys
import os
from typing import Dict, Any

# Add parent directory to path to access bridge_client
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MCP'))

from bridge_client import call_bridge_api
from tool_registry import rhino_tool, gh_tool, bridge_handler

# ============================================================================
# DEBUG_MODE Configuration
# ============================================================================
# Note: Test tools intentionally return full information regardless of DEBUG_MODE
# since they are diagnostic tools meant to verify system functionality.

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
except:
    DEBUG_MODE = False

def filter_debug_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter response based on DEBUG_MODE.
    Note: Test tools always return full data for diagnostic purposes.
    This function is provided for consistency but not applied to test handlers.
    """
    # Test tools intentionally bypass filtering
    return response


# ============================================================================
# Test Tool 1: Simple Echo
# ============================================================================

@rhino_tool(
    name="test_echo",
    description="Simple test tool that echoes back a message. Use this to verify the tool discovery system is working."
)
async def test_echo(message: str = "Hello from test_tools.py!") -> Dict[str, Any]:
    """
    Echo a message back through the bridge to verify communication.

    Args:
        message: The message to echo back

    Returns:
        Dict containing the echoed message
    """
    return call_bridge_api("/test_echo", {"message": message})


@bridge_handler("/test_echo")
def handle_test_echo(data):
    """Bridge handler for echo test"""
    message = data.get("message", "No message provided")

    return {
        "success": True,
        "original_message": message,
        "echo": f"Echo: {message}",
        "source": "test_tools.py",
        "handler": "handle_test_echo",
        "message": "Test tool is working correctly!"
    }


# ============================================================================
# Test Tool 2: System Info
# ============================================================================

@rhino_tool(
    name="test_system_info",
    description="Get system information from the Rhino bridge to verify Python environment"
)
async def test_system_info() -> Dict[str, Any]:
    """
    Get Python and system information from Rhino bridge.

    Returns:
        Dict containing system information
    """
    return call_bridge_api("/test_system_info", {})


@bridge_handler("/test_system_info")
def handle_test_system_info(data):
    """Bridge handler for system info test"""
    import sys
    import platform

    return {
        "success": True,
        "python_version": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "source_file": "test_tools.py",
        "handler": "handle_test_system_info",
        "message": "System info retrieved successfully"
    }


# ============================================================================
# Test Tool 3: Grasshopper Availability Check
# ============================================================================

@gh_tool(
    name="test_gh_available",
    description="Test if Grasshopper is available and get basic information"
)
async def test_gh_available() -> Dict[str, Any]:
    """
    Check if Grasshopper is available in Rhino.

    Returns:
        Dict containing Grasshopper availability status
    """
    return call_bridge_api("/test_gh_available", {})


@bridge_handler("/test_gh_available")
def handle_test_gh_available(data):
    """Bridge handler for Grasshopper availability test"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino

        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": True,
                "grasshopper_available": False,
                "message": "Grasshopper plugin not loaded"
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None

        return {
            "success": True,
            "grasshopper_available": True,
            "has_active_document": gh_doc is not None,
            "document_object_count": gh_doc.ObjectCount if gh_doc else 0,
            "source_file": "test_tools.py",
            "message": "Grasshopper is available and working"
        }

    except ImportError as e:
        return {
            "success": True,
            "grasshopper_available": False,
            "error": str(e),
            "message": "Grasshopper not available in this Rhino installation"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error checking Grasshopper availability"
        }


# ============================================================================
# Test Tool 4: Simple Math Operation
# ============================================================================

@rhino_tool(
    name="test_add_numbers",
    description="Simple test tool to add two numbers. Verifies parameter passing."
)
async def test_add_numbers(a: float, b: float) -> Dict[str, Any]:
    """
    Add two numbers together via the bridge.

    Args:
        a: First number
        b: Second number

    Returns:
        Dict containing the sum
    """
    return call_bridge_api("/test_add_numbers", {"a": a, "b": b})


@bridge_handler("/test_add_numbers")
def handle_test_add_numbers(data):
    """Bridge handler for addition test"""
    try:
        a = float(data.get("a", 0))
        b = float(data.get("b", 0))
        result = a + b

        return {
            "success": True,
            "a": a,
            "b": b,
            "sum": result,
            "operation": f"{a} + {b} = {result}",
            "source_file": "test_tools.py",
            "message": "Addition performed successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Error performing addition"
        }


# ============================================================================
# Notes
# ============================================================================

"""
This file demonstrates that the dynamic discovery system works with ANY .py file
in the Tools directory.

To test:
1. Make sure this file exists in Tools/test_tools.py
2. Restart the MCP server (python MCP/main.py)
3. Restart the Rhino bridge (run start_rhino_bridge.py in Rhino)
4. You should see in the MCP server output:
   [DISCOVERY] Found X tool files: ..., test_tools.py, ...
   [DISCOVERY] ✓ Loaded tools from: test_tools.py
   [DISCOVERY] Registered X Rhino tools, Y Grasshopper tools, Z bridge handlers

5. Test the tools:
   - test_echo - Should echo back your message
   - test_system_info - Should return Python/system info from Rhino
   - test_gh_available - Should check if Grasshopper is available
   - test_add_numbers - Should add two numbers

If all tools work, the dynamic discovery system is functioning correctly!

You can delete this file after testing, or keep it for future reference.
"""
