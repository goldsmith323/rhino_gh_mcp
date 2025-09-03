"""
Bridge Client

This module handles HTTP communication with the Rhino Bridge Server.
It provides a clean interface for all tool modules to communicate with Rhino.

Author: Hossein Zargar
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
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": f"Cannot connect to Rhino Bridge Server at {BRIDGE_URL}. Make sure the bridge server is running in Rhino."
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request to Rhino Bridge Server timed out"
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Bridge API request failed: {e}")
        return {
            "success": False,
            "error": f"Bridge API request failed: {str(e)}"
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse bridge API response: {e}")
        return {
            "success": False,
            "error": f"Invalid response from bridge server: {str(e)}"
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