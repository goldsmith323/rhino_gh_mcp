#!/usr/bin/env python
#! python 3
# venv: rhino-gh-mcp-bridge
# r: requests
"""
Rhino HTTP Bridge Server

A lightweight HTTP server that runs inside Rhino Python 3.9 environment.
This bridge receives HTTP requests from the external MCP server and executes
Rhino/Grasshopper operations, returning results via HTTP responses.

This server provides a dynamic HTTP API that automatically discovers and registers
endpoints from tool modules (rhino_tools.py, gh_tools.py).

Note: The script uses a dedicated virtual environment (rhino-gh-mcp-bridge)
to keep dependencies isolated from other Rhino scripts.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import sys
import os

# Add Tools directory to path for dynamic handler discovery
tools_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Tools'))
if tools_path not in sys.path:
    sys.path.append(tools_path)

# Load environment variables for configuration
DEBUG_MODE = False
try:
    # Try to load from .env file in project root
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
                        print(f"DEBUG_MODE loaded from .env: {DEBUG_MODE}")
                        break
    else:
        # Check environment variable as fallback
        DEBUG_MODE = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
        if DEBUG_MODE:
            print(f"DEBUG_MODE loaded from environment: {DEBUG_MODE}")
except Exception as e:
    print(f"Warning: Could not load DEBUG_MODE from .env: {e}")
    DEBUG_MODE = False

print(f"Bridge Server Running with DEBUG_MODE: {DEBUG_MODE}")

# Try to import Rhino modules - these should be available inside Rhino
try:
    import rhinoscriptsyntax
    import Rhino
    RHINO_AVAILABLE = True
    print("Rhino modules loaded successfully")
except ImportError:
    RHINO_AVAILABLE = False
    print("Warning: Rhino modules not available")

# Try to import Grasshopper modules
try:
    import ghpython
    import grasshopper
    GRASSHOPPER_AVAILABLE = True
    print("Grasshopper modules loaded successfully")
except ImportError:
    GRASSHOPPER_AVAILABLE = False
    print("Warning: Grasshopper modules not available")

# Import dynamic handler system
try:
    from tool_registry import discover_tools
    DYNAMIC_HANDLERS_AVAILABLE = True
    print("Dynamic handler system loaded")
except ImportError as e:
    DYNAMIC_HANDLERS_AVAILABLE = False
    print(f"Warning: Dynamic handler system not available: {e}")

# Initialize handlers at module level
_handlers_initialized = False
_dynamic_handlers = {}

def initialize_dynamic_handlers():
    """Initialize dynamic handlers by discovering tools"""
    global _handlers_initialized, _dynamic_handlers
    
    if _handlers_initialized or not DYNAMIC_HANDLERS_AVAILABLE:
        return _dynamic_handlers
    
    try:
        print("Discovering and initializing dynamic handlers...")
        discover_tools()  # This will populate the handler registry
        
        # Get handlers from registry
        from tool_registry import get_bridge_handlers
        handlers = get_bridge_handlers()
        _dynamic_handlers.update(handlers)
        
        print(f"Initialized {len(_dynamic_handlers)} dynamic handlers:")
        for endpoint in sorted(_dynamic_handlers.keys()):
            print(f"  {endpoint}")
        
        _handlers_initialized = True
        return _dynamic_handlers
    except Exception as e:
        print(f"Error initializing dynamic handlers: {e}")
        return _dynamic_handlers

class RhinoBridgeHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Rhino operations"""
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        print(f"[Bridge] {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/status':
            self.send_status_response()
        elif self.path == '/info':
            self.send_info_response()
        else:
            self.send_error_response(404, "Endpoint not found")
    
    def do_POST(self):
        """Handle POST requests for Rhino operations"""
        import traceback
        endpoint = "unknown"
        request_data = None

        try:
            # Initialize dynamic handlers if not done yet
            if not _handlers_initialized:
                initialize_dynamic_handlers()

            # Parse the request path
            parsed_path = urllib.parse.urlparse(self.path)
            endpoint = parsed_path.path

            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
            else:
                request_data = {}

            # Try dynamic handler
            if endpoint in _dynamic_handlers:
                try:
                    handler_func = _dynamic_handlers[endpoint]
                    result = handler_func(request_data)
                    self.send_json_response(result)
                    return
                except Exception as e:
                    # Detailed error logging for handler failures
                    error_traceback = traceback.format_exc()
                    print(f"ERROR: Handler exception for {endpoint}")
                    print(f"Exception type: {type(e).__name__}")
                    print(f"Exception message: {str(e)}")
                    print(f"Request data: {request_data}")
                    print(f"Full traceback:\n{error_traceback}")

                    error_response = {
                        "success": False,
                        "error": f"Handler error: {str(e)}",
                        "error_type": type(e).__name__,
                        "endpoint": endpoint,
                        "traceback": error_traceback,
                        "request_data": request_data,
                        "debug_hint": "An exception occurred in the Rhino bridge handler. Check the Rhino Python console for full traceback."
                    }
                    self.send_json_response(error_response, 500)
                    return

            # If no dynamic handler found, return 404
            available_endpoints = sorted(_dynamic_handlers.keys())
            error_response = {
                "success": False,
                "error": f"Unknown endpoint: {endpoint}",
                "error_type": "EndpointNotFound",
                "endpoint": endpoint,
                "available_endpoints": available_endpoints,
                "debug_hint": f"The endpoint '{endpoint}' is not registered. Check if the handler is properly decorated with @bridge_handler."
            }
            self.send_json_response(error_response, 404)

        except json.JSONDecodeError as e:
            error_traceback = traceback.format_exc()
            print(f"ERROR: JSON decode error for {endpoint}")
            print(f"Traceback:\n{error_traceback}")

            error_response = {
                "success": False,
                "error": "Invalid JSON in request body",
                "error_type": "JSONDecodeError",
                "error_details": str(e),
                "endpoint": endpoint,
                "debug_hint": "The request body is not valid JSON. Check the request formatting."
            }
            self.send_json_response(error_response, 400)

        except Exception as e:
            error_traceback = traceback.format_exc()
            print(f"ERROR: Unexpected server error for {endpoint}")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception message: {str(e)}")
            print(f"Request data: {request_data}")
            print(f"Full traceback:\n{error_traceback}")

            error_response = {
                "success": False,
                "error": f"Internal server error: {str(e)}",
                "error_type": type(e).__name__,
                "endpoint": endpoint,
                "traceback": error_traceback,
                "request_data": request_data,
                "debug_hint": "An unexpected error occurred in the bridge server. Check the Rhino Python console for details."
            }
            self.send_json_response(error_response, 500)
    
    def send_status_response(self):
        """Send server status"""
        status = {
            "status": "running",
            "rhino_available": RHINO_AVAILABLE,
            "grasshopper_available": GRASSHOPPER_AVAILABLE,
            "message": "Rhino Bridge Server is running"
        }
        self.send_json_response(status)
    
    def send_info_response(self):
        """Send server info"""
        # Get dynamic endpoints
        if not _handlers_initialized:
            initialize_dynamic_handlers()
        
        endpoints = [
            {"path": "/status", "method": "GET", "description": "Server status"},
            {"path": "/info", "method": "GET", "description": "Server information"}
        ]
        
        # Add dynamic endpoints
        for endpoint in sorted(_dynamic_handlers.keys()):
            endpoints.append({
                "path": endpoint,
                "method": "POST",
                "description": f"Dynamic handler for {endpoint}"
            })
        
        info = {
            "name": "Rhino HTTP Bridge Server",
            "version": "2.0.0",
            "author": "Hossein Zargar",
            "endpoints": endpoints,
            "dynamic_handlers": len(_dynamic_handlers)
        }
        self.send_json_response(info)
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # Enable CORS
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def send_error_response(self, status_code, message):
        """Send error response"""
        error_data = {
            "success": False,
            "error": message,
            "status_code": status_code
        }
        self.send_json_response(error_data, status_code)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

class RhinoBridgeServer:
    """Rhino Bridge Server manager"""
    
    def __init__(self, host='localhost', port=8080):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
    
    def start(self):
        """Start the HTTP server"""
        try:
            # Initialize dynamic handlers before starting
            initialize_dynamic_handlers()
            
            self.server = HTTPServer((self.host, self.port), RhinoBridgeHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            print(f"Rhino Bridge Server started on http://{self.host}:{self.port}")
            print("Available endpoints:")
            print("  GET  /status       - Server status")
            print("  GET  /info         - Server information")
            
            # Show dynamic endpoints
            if _dynamic_handlers:
                print("Dynamic endpoints:")
                for endpoint in sorted(_dynamic_handlers.keys()):
                    print(f"  POST {endpoint}")
            else:
                print("No dynamic handlers loaded")
            
            print("\nServer is running in background thread...")
            
        except Exception as e:
            print(f"Failed to start server: {e}")
    
    def stop(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            print("Rhino Bridge Server stopped")
    
    def is_running(self):
        """Check if server is running"""
        return self.server_thread and self.server_thread.is_alive()

# Global server instance
bridge_server = None

def start_bridge_server(host='localhost', port=8080):
    """Start the bridge server"""
    global bridge_server
    
    if bridge_server and bridge_server.is_running():
        print("Bridge server is already running")
        return bridge_server
    
    bridge_server = RhinoBridgeServer(host, port)
    bridge_server.start()
    return bridge_server

def stop_bridge_server():
    """Stop the bridge server"""
    global bridge_server
    
    if bridge_server:
        bridge_server.stop()
        bridge_server = None

def get_bridge_server():
    """Get the current bridge server instance"""
    return bridge_server

# Auto-start when run directly in Rhino
if __name__ == "__main__":
    print("Starting Rhino HTTP Bridge Server...")
    start_bridge_server()
    
    # Keep the script running in Rhino
    try:
        import time
        print("Bridge server is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping bridge server...")
        stop_bridge_server()
        print("Bridge server stopped.")