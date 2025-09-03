# Tools

This directory contains all the tool definitions organized by category. This is where developers can easily add new functionality.

## Files

- **`rhino_tools.py`** - All Rhino 3D modeling tools
- **`gh_tools.py`** - All Grasshopper parametric tools

## Current Tools

### Rhino Tools
- **`draw_line_rhino`** - Draw a line between two 3D points
- **`get_rhino_info`** - Get information about the current Rhino session

### Grasshopper Tools  
- **`list_grasshopper_sliders`** - List all available slider components
- **`set_grasshopper_slider`** - Change slider values by name

## Adding New Tools

### For Rhino Tools

1. **Add the async function** to `rhino_tools.py`:
   ```python
   async def create_circle_rhino(center_x: float, center_y: float, radius: float):
       return call_bridge_api("/create_circle", {
           "center_x": center_x,
           "center_y": center_y, 
           "radius": radius
       })
   ```

2. **Add the tool definition** to the `RHINO_TOOLS` list:
   ```python
   {
       "name": "create_circle_rhino",
       "description": "Create a circle in Rhino with specified center and radius...",
       "function": create_circle_rhino
   }
   ```

3. **Add the corresponding endpoint** to `../Rhino/rhino_bridge_server.py`:
   ```python
   elif endpoint == '/create_circle':
       self.handle_create_circle(request_data)
   ```

### For Grasshopper Tools

Follow the same pattern but add to `gh_tools.py` and the `GRASSHOPPER_TOOLS` list.

## Tool Structure

Each tool needs:
- **Async function** - Handles the MCP call and communicates with bridge
- **Tool definition** - Provides metadata for MCP registration
- **Bridge endpoint** - Handles the HTTP request in Rhino

## Examples of Future Tools

### Rhino Tools
- `create_curve_rhino` - Create curves from point lists
- `extrude_curve_rhino` - Extrude curves to create surfaces
- `boolean_union_rhino` - Perform boolean operations
- `mesh_from_brep_rhino` - Generate meshes from BREP geometry

### Grasshopper Tools
- `get_grasshopper_components` - List all components in definition
- `set_grasshopper_toggle` - Control boolean toggles
- `run_grasshopper_solution` - Trigger solution recalculation
- `bake_grasshopper_geometry` - Bake geometry to Rhino
- `get_grasshopper_data_tree` - Extract data from outputs

## Best Practices

1. **Descriptive names** - Use clear, specific function names
2. **Type hints** - Always include parameter and return type hints
3. **Error handling** - Handle bridge communication failures gracefully
4. **Documentation** - Provide clear descriptions with parameter details
5. **Validation** - Validate parameters before sending to bridge server

## Testing New Tools

1. **Add the tool** following the steps above
2. **Restart the MCP server** to load new tools
3. **Test in Claude Desktop** with simple commands
4. **Verify bridge endpoints** work with direct HTTP calls

The modular design makes it easy to expand functionality - just edit the appropriate file and restart the MCP server!