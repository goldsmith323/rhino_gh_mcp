# Claude Desktop Integration Instructions

## Configuration File Setup

1. **Replace the path placeholder** in `mcp_client_config.json`:
   - Change `REPLACE_WITH_FULL_PATH_TO_PROJECT` to your actual project path
   
2. **Platform-specific path examples:**

   **Windows Example:**
   ```json
   "C:\\Users\\SeyedZ\\Documents\\GitHub\\rhino_gh_mcp\\main.py"
   ```
   
   **macOS/Linux Example:**
   ```json
   "/Users/username/Documents/rhino_gh_mcp/main.py"
   ```

3. **Configuration file locations:**
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

## Complete Working Example

```json
{
  "mcpServers": {
    "Rhino Grasshopper MCP": {
      "command": "python",
      "args": [
        "C:\\Users\\SeyedZ\\Documents\\GitHub\\rhino_gh_mcp\\main.py"
      ],
      "description": "Rhino 3D and Grasshopper parametric design tools"
    }
  }
}
```

## Important Notes

- **This MCP server is designed to run inside Rhino 8**
- You should run this from Rhino's script editor, not from outside Rhino
- After updating the config, restart your MCP client
- The Rhino Grasshopper tools should appear in your available tools

## Alternative Approach

You can also run the server directly from within Rhino's script editor and use it as a standalone service for better integration.