# Rhino Bridge Server

This directory contains everything needed to run the HTTP bridge server inside Rhino 8.

## Files

- **`rhino_bridge_server.py`** - HTTP server that runs inside Rhino Python 3.9
- **`start_rhino_bridge.py`** - Easy startup script for Rhino script editor

## Setup

### 1. Open Rhino 8
Make sure you have Rhino 8 with Python 3.9 support installed.

### 2. Start the Bridge Server
1. **Open Script Editor** in Rhino: Tools > Script > Edit
2. **Load and run the startup script:**
   ```python
   exec(open('C:\\path\\to\\rhino_gh_mcp\\Rhino\\start_rhino_bridge.py').read())
   ```
   *(Replace with your actual path)*

3. **Verify it started successfully:**
   You should see output like:
   ```
   ✓ Bridge server started successfully!
   Server is running on: http://localhost:8080
   ```

### 3. Test the Bridge Server
Open a web browser and visit: `http://localhost:8080/status`

You should see a JSON response like:
```json
{
  "status": "running",
  "rhino_available": true,
  "grasshopper_available": false,
  "message": "Rhino Bridge Server is running"
}
```

## Available Endpoints

The bridge server provides these HTTP endpoints:

- **GET `/status`** - Check server status
- **GET `/info`** - Get server information
- **POST `/draw_line`** - Draw a line in Rhino
- **POST `/list_sliders`** - List Grasshopper sliders
- **POST `/set_slider`** - Set Grasshopper slider value
- **POST `/get_rhino_info`** - Get Rhino session info

## Usage

### Command Line Interface
Once started, you can use these commands in Rhino's script editor:
```python
# Check status
bridge_status()

# Stop the server
stop_bridge()

# Start the server again
start_bridge()
```

### Keep Server Running
The bridge server runs in a background thread, so you can:
- Continue using Rhino normally
- Run other Python scripts
- Keep the server active across Rhino sessions

## Troubleshooting

**Error: "Port 8080 already in use"**
- Stop other servers using port 8080
- Or modify the startup script to use a different port

**Error: "Rhino modules not available"**
- Make sure you're running this inside Rhino's script editor
- Ensure Rhino 8 has Python 3.9 support enabled

**Bridge server won't start**
- Check Rhino's Python console for error messages
- Try running `rhino_bridge_server.py` directly to see detailed errors

**Connection refused from MCP server**
- Verify the bridge server is running: check `http://localhost:8080/status`
- Check that no firewall is blocking port 8080