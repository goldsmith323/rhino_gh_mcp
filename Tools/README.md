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

## Adding New Tools (Auto-Discovery System)

**NEW**: Tools are now automatically discovered using decorators! No manual registration needed.

### For Rhino Tools

1. **Add the decorated function** to `rhino_tools.py`:
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

2. **Add the corresponding endpoint** to `../Rhino/rhino_bridge_server.py`:
   ```python
   elif endpoint == '/create_circle':
       self.handle_create_circle(request_data)
   ```

**That's it!** The tool is automatically discovered and registered when the MCP server starts.

### For Grasshopper Tools

Follow the same pattern but use `@gh_tool` decorator in `gh_tools.py`.

## Tool Structure (Updated)

Each tool now needs:
- **Decorated async function** - Uses `@rhino_tool` or `@gh_tool` decorator with metadata
- **Bridge endpoint** - Handles the HTTP request in Rhino (if new endpoint needed)

**OLD** (manual registration): Function + separate tool definition in TOOLS list  
**NEW** (auto-discovery): Just add decorator to function - that's it!

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

1. **Add the decorated tool** following the steps above
2. **Restart the MCP server** - tools are auto-discovered on startup
3. **Test in Claude Desktop** with simple commands
4. **Verify bridge endpoints** work with direct HTTP calls

The auto-discovery system makes it even easier to expand functionality - just add a decorator and restart!