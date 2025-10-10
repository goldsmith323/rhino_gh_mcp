"""
Bridge Client

This module handles HTTP communication with the Rhino Bridge Server.
It provides a clean interface for all tool modules to communicate with Rhino.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional

# Configuration for Rhino Bridge Server
BRIDGE_HOST = os.getenv('RHINO_BRIDGE_HOST', 'localhost')
BRIDGE_PORT = int(os.getenv('RHINO_BRIDGE_PORT', '8080'))
BRIDGE_URL = f"http://{BRIDGE_HOST}:{BRIDGE_PORT}"

logger = logging.getLogger(__name__)

def call_bridge_api(endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Make HTTP call to the Rhino Bridge Server.

    Args:
        endpoint: API endpoint (e.g., '/draw_line')
        data: Request payload dictionary

    Returns:
        Dict containing the API response
    """
    response = None
    try:
        url = f"{BRIDGE_URL}{endpoint}"

        if data is None:
            # GET request
            logger.info(f"Making GET request to {url}")
            response = requests.get(url, timeout=10)
        else:
            # POST request
            logger.info(f"Making POST request to {url} with data: {data}")
            response = requests.post(
                url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

        # Log response details for debugging
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")

        response.raise_for_status()
        return response.json()

    except requests.exceptions.ConnectionError as e:
        error_msg = f"Cannot connect to Rhino Bridge Server at {BRIDGE_URL}. Make sure the bridge server is running in Rhino."
        logger.error(f"Connection error: {e}")
        return {
            "success": False,
            "error": error_msg,
            "error_type": "ConnectionError",
            "endpoint": endpoint,
            "bridge_url": BRIDGE_URL
        }
    except requests.exceptions.Timeout as e:
        error_msg = f"Request to Rhino Bridge Server timed out after 10 seconds"
        logger.error(f"Timeout error for {endpoint}: {e}")
        return {
            "success": False,
            "error": error_msg,
            "error_type": "Timeout",
            "endpoint": endpoint,
            "request_data": data
        }
    except requests.exceptions.HTTPError as e:
        # HTTP error (4xx, 5xx)
        status_code = response.status_code if response else "unknown"
        response_text = response.text if response else "No response"
        error_msg = f"HTTP {status_code} error from bridge server"

        logger.error(f"HTTP error for {endpoint}: {e}")
        logger.error(f"Response status: {status_code}")
        logger.error(f"Response body: {response_text[:500]}")  # First 500 chars

        return {
            "success": False,
            "error": error_msg,
            "error_type": "HTTPError",
            "status_code": status_code,
            "endpoint": endpoint,
            "response_body": response_text[:1000],  # Include response for debugging
            "request_data": data
        }
    except requests.exceptions.RequestException as e:
        # Generic request exception
        response_text = response.text if response else "No response"
        logger.error(f"Bridge API request failed for {endpoint}: {e}")
        logger.error(f"Response: {response_text[:500]}")

        return {
            "success": False,
            "error": f"Bridge API request failed: {str(e)}",
            "error_type": "RequestException",
            "endpoint": endpoint,
            "response_body": response_text[:1000] if response_text else None,
            "request_data": data
        }
    except json.JSONDecodeError as e:
        # Failed to parse JSON response
        response_text = response.text if response else ""
        response_status = response.status_code if response else "unknown"

        logger.error(f"Failed to parse JSON response from {endpoint}")
        logger.error(f"JSON decode error: {e}")
        logger.error(f"Response status: {response_status}")
        logger.error(f"Response body (first 500 chars): {response_text[:500]}")
        logger.error(f"Response content-type: {response.headers.get('content-type', 'unknown') if response else 'unknown'}")

        return {
            "success": False,
            "error": f"Bridge API request failed: {str(e)}",
            "error_type": "JSONDecodeError",
            "error_details": {
                "message": str(e),
                "line": e.lineno if hasattr(e, 'lineno') else None,
                "column": e.colno if hasattr(e, 'colno') else None
            },
            "endpoint": endpoint,
            "request_data": data,
            "response_status": response_status,
            "response_body": response_text[:1000],  # First 1000 chars for debugging
            "response_content_type": response.headers.get('content-type', 'unknown') if response else 'unknown',
            "debug_hint": "The bridge server returned a non-JSON response. This may indicate a Python error in the handler or the endpoint doesn't exist."
        }

def get_bridge_status() -> Dict[str, Any]:
    """
    Check the status of the Rhino Bridge Server.
    
    Returns:
        Dict containing bridge server status
    """
    return call_bridge_api("/status")

def get_bridge_info() -> Dict[str, Any]:
    """
    Get information about the Rhino Bridge Server.
    
    Returns:
        Dict containing bridge server information  
    """
    return call_bridge_api("/info")