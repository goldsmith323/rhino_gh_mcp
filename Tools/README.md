# Tools

This directory contains all the tool definitions organized by category. This is where developers can easily add new functionality.

## Files

- **`rhino_tools.py`** - All Rhino 3D modeling tools (using auto-discovery decorators)
- **`gh_tools.py`** - All Grasshopper parametric tools (using auto-discovery decorators)
- **`tool_registry.py`** - Auto-discovery system with @rhino_tool and @gh_tool decorators

## Current Tools

### Rhino Tools
- **`draw_line_rhino`** - Draw a line between two 3D points
- **`get_rhino_info`** - Get information about the current Rhino session
- **`typical_roof_truss_generator`** - Generate roof trusses (Pratt, Warren, Vierendeel, Brown, Howe, Onedir)

### Grasshopper Tools  
- **`list_grasshopper_sliders`** - List all available slider components
- **`set_grasshopper_slider`** - Change slider values by name

## Adding New Tools (Fully Dynamic System)

**NEW**: Both MCP tools AND bridge endpoints are now automatically discovered using decorators! No manual registration needed anywhere.

### For Rhino Tools

1. **Add the MCP tool** to `rhino_tools.py`:
   ```python
   @rhino_tool(
       name="create_circle_rhino",
       description="Create a circle in Rhino with specified center and radius..."
   )
   async def create_circle_rhino(center_x: float, center_y: float, radius: float):
       return call_bridge_api("/create_circle", {
           "center_x": center_x,
           "center_y": center_y, 
           "radius": radius
       })
   ```

2. **Add the bridge handler** to the same `rhino_tools.py` file:
   ```python
   @bridge_handler("/create_circle")
   def handle_create_circle(data):
       try:
           import rhinoscriptsyntax as rs
           center = [data.get('center_x', 0), data.get('center_y', 0), 0]
           radius = data.get('radius', 1)
           circle_id = rs.AddCircle(center, radius)
           return {"success": True, "circle_id": str(circle_id)}
       except Exception as e:
           return {"success": False, "error": str(e)}
   ```

**That's it!** Both the MCP tool and bridge endpoint are automatically discovered and registered when servers start.

### For Grasshopper Tools

Follow the same pattern but use `@gh_tool` and `@bridge_handler` decorators in `gh_tools.py`.

## Tool Structure (Fully Dynamic)

Each tool now needs:
- **MCP tool function** - Uses `@rhino_tool` or `@gh_tool` decorator for client-side API
- **Bridge handler function** - Uses `@bridge_handler` decorator for server-side execution

**BEFORE** (manual): Function + manual tool registration + manual bridge endpoint registration  
**NOW** (fully dynamic): Just add two decorators to functions - zero manual registration!

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

1. **Add both decorators** following the steps above (MCP tool + bridge handler)
2. **Restart both servers**:
   - Restart MCP server - MCP tools are auto-discovered on startup
   - Restart Rhino bridge server - bridge handlers are auto-discovered on startup
3. **Test in Claude Desktop** with simple commands
4. **Verify bridge endpoints** work with direct HTTP calls to `http://localhost:8080/your_endpoint`

The fully dynamic system makes it incredibly easy to expand functionality - just add two decorators and restart both servers!