#!/usr/bin/env python
"""
Rhino Bridge Startup Script

This script is designed to be run inside Rhino's script editor to start
the HTTP bridge server. It provides a simple interface to start/stop
the bridge server that communicates with the external MCP server.

Usage:
1. Open Rhino 8
2. Open Script Editor (Tools > PythonScript > Edit)  
3. Load and run this script
4. The bridge server will start and run in background

Author: Hossein Zargar
"""

import sys
import os

# Add the current directory to Python path to import our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from rhino_bridge_server import start_bridge_server, stop_bridge_server, get_bridge_server
    print("Successfully imported Rhino Bridge Server")
except ImportError as e:
    print(f"Error importing bridge server: {e}")
    print("Make sure rhino_bridge_server.py is in the same directory")
    sys.exit(1)

def main():
    """Main function to handle bridge server startup"""
    print("=" * 50)
    print("Rhino/Grasshopper MCP Bridge Server")
    print("Author: Hossein Zargar")
    print("=" * 50)
    
    # Check if server is already running
    existing_server = get_bridge_server()
    if existing_server and existing_server.is_running():
        print("Bridge server is already running!")
        print("To stop the server, run: stop_bridge_server()")
        return existing_server
    
    # Start the server
    try:
        print("Starting bridge server...")
        server = start_bridge_server(host='localhost', port=8080)
        
        if server and server.is_running():
            print("\n✓ Bridge server started successfully!")
            print("Server is running on: http://localhost:8080")
            print("\nAvailable endpoints:")
            print("  GET  /status       - Check server status")
            print("  GET  /info         - Get server information")
            print("  POST /draw_line    - Draw a line in Rhino")
            print("  POST /list_sliders - List Grasshopper sliders")
            print("  POST /set_slider   - Set Grasshopper slider value")
            print("  POST /get_rhino_info - Get Rhino session info")
            
            print("\nThe bridge server is now ready to receive requests from the MCP server.")
            print("You can now start the external MCP server and use it with Claude Desktop.")
            
            print("\nTo stop the server later, run:")
            print("  stop_bridge_server()")
            
            return server
        else:
            print("✗ Failed to start bridge server")
            return None
            
    except Exception as e:
        print(f"✗ Error starting bridge server: {e}")
        return None

def stop():
    """Stop the bridge server"""
    print("Stopping bridge server...")
    stop_bridge_server()
    print("Bridge server stopped.")

def status():
    """Check bridge server status"""
    server = get_bridge_server()
    if server and server.is_running():
        print("✓ Bridge server is running on http://localhost:8080")
    else:
        print("✗ Bridge server is not running")

if __name__ == "__main__":
    # Start the server when script is run
    main()

# Make functions available in Rhino's global scope
globals()['start_bridge'] = main
globals()['stop_bridge'] = stop
globals()['bridge_status'] = status

print("\nQuick commands available:")
print("  start_bridge()  - Start the bridge server")
print("  stop_bridge()   - Stop the bridge server") 
print("  bridge_status() - Check server status")