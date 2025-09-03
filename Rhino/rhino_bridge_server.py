#!/usr/bin/env python
"""
Rhino HTTP Bridge Server

A lightweight HTTP server that runs inside Rhino Python 3.9 environment.
This bridge receives HTTP requests from the external MCP server and executes
Rhino/Grasshopper operations, returning results via HTTP responses.

This server provides a generic HTTP API that can be extended with new endpoints
as tools are added to the tool modules (rhino_tools.py, gh_tools.py).

Author: Hossein Zargar
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

# Try to import Rhino modules - these should be available inside Rhino
try:
    import rhinoscriptsyntax as rs
    import Rhino
    RHINO_AVAILABLE = True
    print("Rhino modules loaded successfully")
except ImportError:
    RHINO_AVAILABLE = False
    print("Warning: Rhino modules not available")

# Try to import Grasshopper modules
try:
    import ghpython
    import grasshopper as gh
    GRASSHOPPER_AVAILABLE = True
    print("Grasshopper modules loaded successfully")
except ImportError:
    GRASSHOPPER_AVAILABLE = False
    print("Warning: Grasshopper modules not available")

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
        try:
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
            
            # Route to appropriate handler
            if endpoint == '/draw_line':
                self.handle_draw_line(request_data)
            elif endpoint == '/list_sliders':
                self.handle_list_sliders(request_data)
            elif endpoint == '/set_slider':
                self.handle_set_slider(request_data)
            elif endpoint == '/get_rhino_info':
                self.handle_get_rhino_info(request_data)
            else:
                self.send_error_response(404, f"Unknown endpoint: {endpoint}")
                
        except json.JSONDecodeError:
            self.send_error_response(400, "Invalid JSON in request body")
        except Exception as e:
            self.send_error_response(500, f"Internal server error: {str(e)}")
    
    def handle_draw_line(self, data):
        """Handle line drawing requests"""
        try:
            # Extract coordinates
            start_x = float(data.get('start_x', 0))
            start_y = float(data.get('start_y', 0))
            start_z = float(data.get('start_z', 0))
            end_x = float(data.get('end_x', 0))
            end_y = float(data.get('end_y', 0))
            end_z = float(data.get('end_z', 0))
            
            if not RHINO_AVAILABLE:
                response = {
                    "success": False,
                    "error": "Rhino is not available",
                    "line_id": None
                }
            else:
                # Create the line in Rhino
                start_point = [start_x, start_y, start_z]
                end_point = [end_x, end_y, end_z]
                
                line_id = rs.AddLine(start_point, end_point)
                
                if line_id:
                    line_length = rs.CurveLength(line_id)
                    response = {
                        "success": True,
                        "line_id": str(line_id),
                        "start_point": start_point,
                        "end_point": end_point,
                        "length": line_length,
                        "message": f"Line created successfully with length {line_length:.2f}"
                    }
                else:
                    response = {
                        "success": False,
                        "error": "Failed to create line in Rhino",
                        "line_id": None
                    }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(500, f"Error drawing line: {str(e)}")
    
    def handle_list_sliders(self, data):
        """Handle list sliders requests"""
        try:
            if not GRASSHOPPER_AVAILABLE:
                response = {
                    "success": False,
                    "error": "Grasshopper is not available",
                    "sliders": []
                }
            else:
                # Mock response for now - can be extended with real GH API
                sliders = [
                    {"name": "Width", "current_value": 10.0, "min": 0.0, "max": 100.0},
                    {"name": "Height", "current_value": 20.0, "min": 0.0, "max": 50.0},
                    {"name": "Count", "current_value": 5.0, "min": 1.0, "max": 20.0}
                ]
                
                response = {
                    "success": True,
                    "sliders": sliders,
                    "count": len(sliders),
                    "message": f"Found {len(sliders)} slider components"
                }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(500, f"Error listing sliders: {str(e)}")
    
    def handle_set_slider(self, data):
        """Handle set slider requests"""
        try:
            slider_name = data.get('slider_name', '')
            new_value = float(data.get('new_value', 0))
            
            if not GRASSHOPPER_AVAILABLE:
                response = {
                    "success": False,
                    "error": "Grasshopper is not available",
                    "slider_name": slider_name,
                    "new_value": new_value
                }
            else:
                # Mock implementation - can be extended with real GH API
                if slider_name.lower() in ["width", "height", "count"]:
                    response = {
                        "success": True,
                        "slider_name": slider_name,
                        "old_value": 10.0,  # Mock old value
                        "new_value": new_value,
                        "message": f"Slider '{slider_name}' updated to {new_value}"
                    }
                else:
                    response = {
                        "success": False,
                        "error": f"Slider '{slider_name}' not found",
                        "slider_name": slider_name,
                        "new_value": new_value
                    }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(500, f"Error setting slider: {str(e)}")
    
    def handle_get_rhino_info(self, data):
        """Handle get Rhino info requests"""
        try:
            if not RHINO_AVAILABLE:
                response = {
                    "success": False,
                    "error": "Rhino is not available",
                    "info": {}
                }
            else:
                info = {
                    "rhino_available": RHINO_AVAILABLE,
                    "grasshopper_available": GRASSHOPPER_AVAILABLE,
                }
                
                # Try to get Rhino-specific information
                try:
                    info["document_units"] = rs.UnitSystemName(rs.UnitSystem())
                    info["object_count"] = rs.ObjectCount()
                    info["is_command_running"] = rs.IsCommand()
                except Exception as e:
                    info["rhino_error"] = str(e)
                
                response = {
                    "success": True,
                    "info": info,
                    "message": "Rhino information retrieved successfully"
                }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(500, f"Error getting Rhino info: {str(e)}")
    
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
        info = {
            "name": "Rhino HTTP Bridge Server",
            "version": "1.0.0",
            "author": "Hossein Zargar",
            "endpoints": [
                {"path": "/status", "method": "GET", "description": "Server status"},
                {"path": "/info", "method": "GET", "description": "Server information"},
                {"path": "/draw_line", "method": "POST", "description": "Draw a line in Rhino"},
                {"path": "/list_sliders", "method": "POST", "description": "List Grasshopper sliders"},
                {"path": "/set_slider", "method": "POST", "description": "Set Grasshopper slider value"},
                {"path": "/get_rhino_info", "method": "POST", "description": "Get Rhino session info"}
            ]
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
            self.server = HTTPServer((self.host, self.port), RhinoBridgeHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            print(f"Rhino Bridge Server started on http://{self.host}:{self.port}")
            print("Available endpoints:")
            print("  GET  /status       - Server status")
            print("  GET  /info         - Server information")
            print("  POST /draw_line    - Draw a line in Rhino")
            print("  POST /list_sliders - List Grasshopper sliders")
            print("  POST /set_slider   - Set Grasshopper slider value")
            print("  POST /get_rhino_info - Get Rhino session info")
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