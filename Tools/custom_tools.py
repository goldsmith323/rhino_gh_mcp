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
import csv
import numpy as np

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

# ===================================================================================
# Truss Tonnage Prediction Tool: Predict long-span truss tonnage from span and depth
# ===================================================================================

# Global variable to cache the trained model
_truss_model_cache = None

def _train_truss_model():
    """
    Train polynomial regression model for truss weight prediction.
    Uses numpy for polynomial fitting without sklearn dependency.

    Returns:
        Tuple of (coefficients, polynomial_degree, stats_dict)
    """
    global _truss_model_cache

    if _truss_model_cache is not None:
        return _truss_model_cache

    # Get the CSV file path (same directory as this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, 'truss_data.csv')

    # Load data from CSV
    spans = []
    depths = []
    weights = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                span = float(row['Truss Span (ft)'])
                depth = float(row['Max Truss Depth (ft)'])
                weight = float(row['Weight (tons)'])
                spans.append(span)
                depths.append(depth)
                weights.append(weight)
            except (ValueError, KeyError):
                continue

    # Convert to numpy arrays
    X_span = np.array(spans)
    X_depth = np.array(depths)
    y = np.array(weights)

    # Create polynomial features manually (degree 2)
    # Features: [1, span, depth, span², span*depth, depth²]
    n_samples = len(X_span)
    X_poly = np.zeros((n_samples, 6))
    X_poly[:, 0] = 1  # intercept
    X_poly[:, 1] = X_span  # span
    X_poly[:, 2] = X_depth  # depth
    X_poly[:, 3] = X_span ** 2  # span²
    X_poly[:, 4] = X_span * X_depth  # span * depth
    X_poly[:, 5] = X_depth ** 2  # depth²

    # Solve using least squares: (X^T X)^-1 X^T y
    coefficients = np.linalg.lstsq(X_poly, y, rcond=None)[0]

    # Calculate R² and RMSE for model quality
    predictions = X_poly @ coefficients
    ss_res = np.sum((y - predictions) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    rmse = np.sqrt(np.mean((predictions - y) ** 2))

    stats = {
        'r_squared': r_squared,
        'rmse': rmse,
        'n_samples': n_samples
    }

    _truss_model_cache = (coefficients, stats)
    return coefficients, stats

@custom_tool(
    name="predict_truss_tonnage",
    description=(
        "Predict the weight (tonnage) of a truss based on its span and depth. "
        "This tool uses a polynomial regression model trained on 200 truss examples "
        "to estimate the weight of a truss configuration.\n\n"
        "**Parameters:**\n"
        "- **span** (float): Truss span in feet (typical range: 150-380 ft)\n"
        "- **depth** (float): Maximum truss depth in feet (typical range: 15-36 ft)\n"
        "\n**Returns:**\n"
        "Dictionary with predicted tonnage and model statistics.\n\n"
    )
)
async def predict_truss_tonnage(span: float, depth: float) -> Dict[str, Any]:
    """
    Predict truss weight based on span and depth.

    Args:
        span: Truss span in feet
        depth: Maximum truss depth in feet

    Returns:
        Dict containing predicted tonnage and model information
    """
    try:
        # Validate inputs
        span = float(span)
        depth = float(depth)

        if span <= 0 or depth <= 0:
            return {
                "success": False,
                "error": "Span and depth must be positive values"
            }

        # Check span/depth ratio
        ratio = span / depth

        # Train model (or use cached version)
        coefficients, stats = _train_truss_model()

        # Create polynomial features for prediction
        # Features: [1, span, depth, span², span*depth, depth²]
        X_new = np.array([
            1,
            span,
            depth,
            span ** 2,
            span * depth,
            depth ** 2
        ])

        # Make prediction
        predicted_weight = np.dot(X_new, coefficients)

        result = {
            "success": True,
            "span_ft": span,
            "depth_ft": depth,
            "span_depth_ratio": round(ratio, 2),
            "predicted_weight_tons": round(predicted_weight, 2),
            "model_r_squared": round(stats['r_squared'], 4),
            "model_rmse_tons": round(stats['rmse'], 2),
            "training_samples": stats['n_samples'],
            "message": f"Predicted weight for span={span} ft, depth={depth} ft: {predicted_weight:.2f} tons"
        }

        return result

    except FileNotFoundError:
        return {
            "success": False,
            "error": "CSV file 'truss_data.csv' not found. Ensure it is in the same directory as this script."
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in predict_truss_tonnage: {str(e)}"
        }

# All tools are automatically registered via decorators