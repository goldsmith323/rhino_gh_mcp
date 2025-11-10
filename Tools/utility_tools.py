"""
Utility Tools

Some example tools for performing utility functions
"""

import sys
import os
from typing import Dict, Any

# Add parent directory to path to access bridge_client
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MCP'))

from bridge_client import call_bridge_api

# Import the decorator system
try:
    from .tool_registry import utility_tool, bridge_handler
except ImportError:
    # Fallback for direct import
    from tool_registry import utility_tool, bridge_handler

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

# ============================================================================
# Utility Tool 1: Simple Echo
# ============================================================================

@utility_tool(
    name="test_echo",
    description="Simple test tool that echoes back a message. Use this to verify the tool discovery system is working."
)
async def utility_echo(message: str = "Hello from utility_tools.py!") -> Dict[str, Any]:
    """
    Echo a message back through the bridge to verify communication.

    Args:
        message: The message to echo back

    Returns:
        Dict containing the echoed message
    """
    return call_bridge_api("/utility_echo", {"message": message})


@bridge_handler("/utility_echo")
def handle_utility_echo(data):
    """Bridge handler for echo test"""
    message = data.get("message", "No message provided")

    return {
        "success": True,
        "original_message": message,
        "echo": f"Echo: {message}",
        "source": "utility_tools.py",
        "handler": "handle_utility_echo",
        "message": "Utility tool is working correctly!"
    }


# ============================================================================
# Utility Tool 2: Quantify Volume from Length and assumed cross-section
# ============================================================================
@utility_tool(
    name="quantify_volume",
    description="Calculate the volume of a material given its length and cross-sectional area."
)
async def quantify_volume(length: float, cross_sectional_area: float) -> Dict[str, Any]:
    """
    Calculate the volume of a material. Units for length and area are assumed to be consistent (e.g., feet and square feet).

    Args:
        length: The length of the material
        cross_sectional_area: The cross-sectional area of the material

    Returns:
        Dict containing the calculated volume
    """
    volume = length * cross_sectional_area
    return call_bridge_api("/quantify_volume", {"volume": volume})


@bridge_handler("/quantify_volume")
def handle_quantify_volume(data):
    """Bridge handler for volume calculation"""
    volume = data.get("volume", 0)
    return {
        "success": True,
        "volume": volume,
        "message": f"Calculated volume: {volume:.2f} cubic units."
    }
