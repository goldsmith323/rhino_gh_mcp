"""
Custom Test Tools

This module contains basic MCP tools for testing the MCP server connection
WITHOUT requiring Rhino or Grasshopper. These tools help verify that:
1. The MCP server is running correctly
2. Tool registration and discovery works
3. Basic Python operations are functioning

Use these tools to test your setup before moving to Rhino/Grasshopper integration.
"""

import sys
import os
from typing import Dict, Any
from datetime import datetime

# Import the decorator system
try:
    from tool_registry import custom_tool
except ImportError:
    # Add parent directory to path for imports
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(parent_dir)
    from tool_registry import custom_tool

@custom_tool(
    name="hello_world",
    description=(
        "A simple hello world tool to test MCP connection. "
        "This tool requires NO Rhino or Grasshopper installation. "
        "It simply returns a success message to verify the MCP server is working.\n\n"
        "**Returns:**\n"
        "Dictionary with success message and timestamp."
    )
)
async def hello_world() -> Dict[str, Any]:
    """
    Simple hello world function to test MCP connectivity.

    Returns:
        Dict containing success status and greeting message
    """
    try:
        return {
            "success": True,
            "message": "Hello from MCP Server! (No Rhino Bridge Required)",
            "timestamp": datetime.now().isoformat(),
            "test_status": "MCP connection is working correctly"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in hello_world: {str(e)}"
        }

@custom_tool(
    name="simple_math",
    description=(
        "Perform basic math operations (add, subtract, multiply, divide). "
        "This tool tests parameter passing and computation without requiring Rhino.\n\n"
        "**Parameters:**\n"
        "- **a** (float): First number\n"
        "- **b** (float): Second number\n"
        "- **operation** (str): Operation to perform (add, subtract, multiply, divide)\n"
        "\n**Returns:**\n"
        "Dictionary with calculation result."
    )
)
async def simple_math(a: float, b: float, operation: str = "add") -> Dict[str, Any]:
    """
    Perform basic math operation on two numbers.

    Args:
        a: First number
        b: Second number
        operation: Operation to perform (add, subtract, multiply, divide)

    Returns:
        Dict containing operation result
    """
    try:
        a = float(a)
        b = float(b)
        operation = operation.lower()

        operations = {
            'add': lambda x, y: x + y,
            'subtract': lambda x, y: x - y,
            'multiply': lambda x, y: x * y,
            'divide': lambda x, y: x / y if y != 0 else None
        }

        if operation not in operations:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}. Use: add, subtract, multiply, divide"
            }

        result = operations[operation](a, b)

        if result is None:
            return {
                "success": False,
                "error": "Division by zero"
            }

        return {
            "success": True,
            "operation": operation,
            "input_a": a,
            "input_b": b,
            "result": result,
            "message": f"{a} {operation} {b} = {result}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error in simple_math: {str(e)}"
        }

@custom_tool(
    name="echo_message",
    description=(
        "Echo back a message with additional metadata. "
        "Tests string parameter passing and JSON response handling.\n\n"
        "**Parameters:**\n"
        "- **message** (str): The message to echo back\n"
        "\n**Returns:**\n"
        "Dictionary with echoed message and metadata."
    )
)
async def echo_message(message: str) -> Dict[str, Any]:
    """
    Echo back a message with metadata.

    Args:
        message: The message to echo

    Returns:
        Dict containing echoed message and metadata
    """
    try:
        return {
            "success": True,
            "original_message": message,
            "echoed_message": message,
            "message_length": len(message),
            "word_count": len(message.split()),
            "message": f"Echo: {message}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Error in echo_message: {str(e)}"
        }

# All tools are automatically registered via decorators
