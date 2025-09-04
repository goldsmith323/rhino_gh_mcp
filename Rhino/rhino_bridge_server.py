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
            elif endpoint == '/generate_truss':
                self.handle_generate_truss(request_data)
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
    
    def handle_generate_truss(self, data):
        """Handle truss generation requests"""
        try:
            # Extract truss parameters
            upper_line_start_x = float(data.get('upper_line_start_x', 0))
            upper_line_start_y = float(data.get('upper_line_start_y', 0))
            upper_line_start_z = float(data.get('upper_line_start_z', 0))
            upper_line_end_x = float(data.get('upper_line_end_x', 10))
            upper_line_end_y = float(data.get('upper_line_end_y', 0))
            upper_line_end_z = float(data.get('upper_line_end_z', 0))
            truss_depth = float(data.get('truss_depth', 2))
            num_divisions = int(data.get('num_divisions', 4))
            truss_type = data.get('truss_type', 'Pratt')
            clear_previous = data.get('clear_previous', True)
            truss_plane_direction = data.get('truss_plane_direction', 'perpendicular')
            
            if not RHINO_AVAILABLE:
                response = {
                    "success": False,
                    "error": "Rhino is not available",
                    "truss_members": []
                }
            else:
                # Clear previous truss if requested
                if clear_previous:
                    self.clear_previous_trusses()
                
                # Generate truss geometry
                truss_members = self.create_truss_geometry(
                    [upper_line_start_x, upper_line_start_y, upper_line_start_z],
                    [upper_line_end_x, upper_line_end_y, upper_line_end_z],
                    truss_depth,
                    num_divisions,
                    truss_type,
                    truss_plane_direction
                )
                
                if truss_members:
                    response = {
                        "success": True,
                        "truss_members": truss_members,
                        "num_members": len(truss_members),
                        "truss_depth": truss_depth,
                        "num_divisions": num_divisions,
                        "truss_type": truss_type,
                        "message": f"{truss_type} truss created successfully with {len(truss_members)} members"
                    }
                else:
                    response = {
                        "success": False,
                        "error": "Failed to create truss in Rhino",
                        "truss_members": []
                    }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(500, f"Error generating truss: {str(e)}")
    
    def clear_previous_trusses(self):
        """Clear previously generated truss objects"""
        try:
            # Get all objects with "truss" user text
            all_objects = rs.AllObjects()
            if all_objects:
                truss_objects = []
                for obj_id in all_objects:
                    user_text = rs.GetUserText(obj_id, "object_type")
                    if user_text == "truss_member":
                        truss_objects.append(obj_id)
                
                if truss_objects:
                    rs.DeleteObjects(truss_objects)
                    print(f"Cleared {len(truss_objects)} previous truss members")
        except Exception as e:
            print(f"Error clearing previous trusses: {str(e)}")
    
    def create_truss_geometry(self, start_point, end_point, depth, divisions, truss_type, plane_direction):
        """Create the actual truss geometry in Rhino"""
        try:
            truss_members = []
            
            # Calculate truss parameters
            import math
            
            # Vector from start to end of upper chord
            upper_vector = [end_point[0] - start_point[0], 
                          end_point[1] - start_point[1], 
                          end_point[2] - start_point[2]]
            
            # Length of upper chord
            upper_length = math.sqrt(upper_vector[0]**2 + upper_vector[1]**2 + upper_vector[2]**2)
            
            # Normalize upper vector
            if upper_length > 0:
                upper_unit = [v / upper_length for v in upper_vector]
            else:
                upper_unit = [1, 0, 0]
            
            # Calculate perpendicular direction for truss depth
            # For simplicity, we'll use the Z-direction (vertical) for depth
            depth_vector = [0, 0, -depth]  # Truss extends downward
            
            # Generate division points along upper chord
            division_points_top = []
            division_points_bottom = []
            
            for i in range(divisions + 1):
                t = i / divisions
                
                # Top chord points
                top_point = [
                    start_point[0] + t * upper_vector[0],
                    start_point[1] + t * upper_vector[1],
                    start_point[2] + t * upper_vector[2]
                ]
                division_points_top.append(top_point)
                
                # Bottom chord points (offset by depth)
                bottom_point = [
                    top_point[0] + depth_vector[0],
                    top_point[1] + depth_vector[1],
                    top_point[2] + depth_vector[2]
                ]
                division_points_bottom.append(bottom_point)
            
            # Create top chord segments
            for i in range(divisions):
                line_id = rs.AddLine(division_points_top[i], division_points_top[i + 1])
                if line_id:
                    rs.SetUserText(line_id, "object_type", "truss_member")
                    rs.SetUserText(line_id, "member_type", "top_chord")
                    truss_members.append({
                        "id": str(line_id),
                        "type": "top_chord",
                        "start": division_points_top[i],
                        "end": division_points_top[i + 1]
                    })
            
            # Create bottom chord segments
            for i in range(divisions):
                line_id = rs.AddLine(division_points_bottom[i], division_points_bottom[i + 1])
                if line_id:
                    rs.SetUserText(line_id, "object_type", "truss_member")
                    rs.SetUserText(line_id, "member_type", "bottom_chord")
                    truss_members.append({
                        "id": str(line_id),
                        "type": "bottom_chord",
                        "start": division_points_bottom[i],
                        "end": division_points_bottom[i + 1]
                    })
            
            # Create web members based on truss type
            if truss_type.lower() == "pratt":
                # Pratt: Verticals + diagonals in compression
                for i in range(divisions + 1):
                    line_id = rs.AddLine(division_points_top[i], division_points_bottom[i])
                    if line_id:
                        rs.SetUserText(line_id, "object_type", "truss_member")
                        rs.SetUserText(line_id, "member_type", "vertical")
                        truss_members.append({
                            "id": str(line_id),
                            "type": "vertical",
                            "start": division_points_top[i],
                            "end": division_points_bottom[i]
                        })
                
                for i in range(divisions):
                    if i % 2 == 0:  # Alternate diagonals
                        line_id = rs.AddLine(division_points_bottom[i], division_points_top[i + 1])
                    else:
                        line_id = rs.AddLine(division_points_top[i], division_points_bottom[i + 1])
                    
                    if line_id:
                        rs.SetUserText(line_id, "object_type", "truss_member")
                        rs.SetUserText(line_id, "member_type", "diagonal")
                        truss_members.append({
                            "id": str(line_id),
                            "type": "diagonal",
                            "start": division_points_bottom[i] if i % 2 == 0 else division_points_top[i],
                            "end": division_points_top[i + 1] if i % 2 == 0 else division_points_bottom[i + 1]
                        })
            
            elif truss_type.lower() == "warren":
                # Warren: No verticals, alternating diagonals
                for i in range(divisions):
                    if i % 2 == 0:
                        line_id = rs.AddLine(division_points_bottom[i], division_points_top[i + 1])
                        start_pt, end_pt = division_points_bottom[i], division_points_top[i + 1]
                    else:
                        line_id = rs.AddLine(division_points_top[i], division_points_bottom[i + 1])
                        start_pt, end_pt = division_points_top[i], division_points_bottom[i + 1]
                    
                    if line_id:
                        rs.SetUserText(line_id, "object_type", "truss_member")
                        rs.SetUserText(line_id, "member_type", "diagonal")
                        truss_members.append({
                            "id": str(line_id),
                            "type": "diagonal",
                            "start": start_pt,
                            "end": end_pt
                        })
            
            elif truss_type.lower() == "vierendeel":
                # Vierendeel: Only verticals, no diagonals (moment frame)
                for i in range(divisions + 1):
                    line_id = rs.AddLine(division_points_top[i], division_points_bottom[i])
                    if line_id:
                        rs.SetUserText(line_id, "object_type", "truss_member")
                        rs.SetUserText(line_id, "member_type", "vertical")
                        truss_members.append({
                            "id": str(line_id),
                            "type": "vertical",
                            "start": division_points_top[i],
                            "end": division_points_bottom[i]
                        })
            
            elif truss_type.lower() == "howe":
                # Howe: Verticals + diagonals in tension (opposite of Pratt)
                for i in range(divisions + 1):
                    line_id = rs.AddLine(division_points_top[i], division_points_bottom[i])
                    if line_id:
                        rs.SetUserText(line_id, "object_type", "truss_member")
                        rs.SetUserText(line_id, "member_type", "vertical")
                        truss_members.append({
                            "id": str(line_id),
                            "type": "vertical",
                            "start": division_points_top[i],
                            "end": division_points_bottom[i]
                        })
                
                for i in range(divisions):
                    if i % 2 == 0:
                        line_id = rs.AddLine(division_points_top[i], division_points_bottom[i + 1])
                    else:
                        line_id = rs.AddLine(division_points_bottom[i], division_points_top[i + 1])
                    
                    if line_id:
                        rs.SetUserText(line_id, "object_type", "truss_member")
                        rs.SetUserText(line_id, "member_type", "diagonal")
                        truss_members.append({
                            "id": str(line_id),
                            "type": "diagonal",
                            "start": division_points_top[i] if i % 2 == 0 else division_points_bottom[i],
                            "end": division_points_bottom[i + 1] if i % 2 == 0 else division_points_top[i + 1]
                        })
            
            elif truss_type.lower() == "brown":
                # Brown: Similar to Pratt with different diagonal pattern
                for i in range(divisions + 1):
                    line_id = rs.AddLine(division_points_top[i], division_points_bottom[i])
                    if line_id:
                        rs.SetUserText(line_id, "object_type", "truss_member")
                        rs.SetUserText(line_id, "member_type", "vertical")
                        truss_members.append({
                            "id": str(line_id),
                            "type": "vertical",
                            "start": division_points_top[i],
                            "end": division_points_bottom[i]
                        })
                
                for i in range(divisions):
                    # Brown pattern: both diagonals in each bay
                    line_id1 = rs.AddLine(division_points_bottom[i], division_points_top[i + 1])
                    line_id2 = rs.AddLine(division_points_top[i], division_points_bottom[i + 1])
                    
                    for line_id, start_pt, end_pt in [
                        (line_id1, division_points_bottom[i], division_points_top[i + 1]),
                        (line_id2, division_points_top[i], division_points_bottom[i + 1])
                    ]:
                        if line_id:
                            rs.SetUserText(line_id, "object_type", "truss_member")
                            rs.SetUserText(line_id, "member_type", "diagonal")
                            truss_members.append({
                                "id": str(line_id),
                                "type": "diagonal",
                                "start": start_pt,
                                "end": end_pt
                            })
            
            elif truss_type.lower() == "onedir":
                # Onedir: Single direction diagonals only
                for i in range(divisions):
                    line_id = rs.AddLine(division_points_bottom[i], division_points_top[i + 1])
                    if line_id:
                        rs.SetUserText(line_id, "object_type", "truss_member")
                        rs.SetUserText(line_id, "member_type", "diagonal")
                        truss_members.append({
                            "id": str(line_id),
                            "type": "diagonal",
                            "start": division_points_bottom[i],
                            "end": division_points_top[i + 1]
                        })
            
            else:
                # Default to Pratt if unknown type
                for i in range(divisions + 1):
                    line_id = rs.AddLine(division_points_top[i], division_points_bottom[i])
                    if line_id:
                        rs.SetUserText(line_id, "object_type", "truss_member")
                        rs.SetUserText(line_id, "member_type", "vertical")
                        truss_members.append({
                            "id": str(line_id),
                            "type": "vertical",
                            "start": division_points_top[i],
                            "end": division_points_bottom[i]
                        })
                
                for i in range(divisions):
                    if i % 2 == 0:
                        line_id = rs.AddLine(division_points_bottom[i], division_points_top[i + 1])
                    else:
                        line_id = rs.AddLine(division_points_top[i], division_points_bottom[i + 1])
                    
                    if line_id:
                        rs.SetUserText(line_id, "object_type", "truss_member")
                        rs.SetUserText(line_id, "member_type", "diagonal")
                        truss_members.append({
                            "id": str(line_id),
                            "type": "diagonal",
                            "start": division_points_bottom[i] if i % 2 == 0 else division_points_top[i],
                            "end": division_points_top[i + 1] if i % 2 == 0 else division_points_bottom[i + 1]
                        })
            
            return truss_members
            
        except Exception as e:
            print(f"Error in create_truss_geometry: {str(e)}")
            return []
    
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
                {"path": "/get_rhino_info", "method": "POST", "description": "Get Rhino session info"},
                {"path": "/generate_truss", "method": "POST", "description": "Generate typical roof truss structure"}
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
            print("  POST /generate_truss - Generate typical roof truss structure")
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