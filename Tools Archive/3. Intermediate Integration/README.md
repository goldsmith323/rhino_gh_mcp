# Level 3: Intermediate Integration

## Purpose
This level provides comprehensive tools for working with **single Grasshopper files**. You'll learn to manipulate sliders, value lists, panels, geometry inputs/outputs, and bake results to Rhino - all focusing on ONE GH file at a time.

**Note:** This level does NOT include:
- Grasshopper File Library management
- EML (External Multi-Link) parameters for multi-file workflows
- Automated workflow execution between files
- Custom Python script execution

Those advanced features are in Level 4 (Advanced Integration).

## Prerequisites
-  Level 2 (Early Integration) completed successfully
-  Comfortable with basic Rhino and Grasshopper operations
-  Understanding of Grasshopper sliders and parameters

## What You'll Learn
-  Advanced slider operations (set multiple at once)
-  ValueList component manipulation
-  Panel reading and writing
-  Geometry input from Rhino to Grasshopper
-  Geometry output from Grasshopper
-  Baking Grasshopper geometry to Rhino
-  Component inspection and analysis

## Tools Included

### Rhino Tools (6 tools)
All current Rhino tools from Level 2, plus:
- `get_rhino_info()` - Get Rhino session information
- `typical_roof_truss_generator()` - Generate truss structures
- `get_selected_rhino_objects()` - Get selected object info
- `get_rhino_object_geometry()` - Extract geometry data
- `get_curve_length()` - Get curve length

### Grasshopper Tools (19 tools)

**File Management (2 tools):**
- `get_active_gh_files()` - See what files are open
- `set_active_gh_file(file_name)` - Switch between open files

**Slider Operations (4 tools):**
- `list_grasshopper_sliders(file_name)`
- `set_grasshopper_slider(file_name, slider_name, value)`
- `set_multiple_grasshopper_sliders(file_name, slider_updates)`
- `analyze_grasshopper_sliders(file_name)` - Detailed analysis with connections

**ValueList Operations (2 tools):**
- `list_grasshopper_valuelist_components(file_name)`
- `set_grasshopper_valuelist_selection(file_name, valuelist_name, selection)`

**Panel Operations (3 tools):**
- `list_grasshopper_panels(file_name)`
- `set_grasshopper_panel_text(file_name, panel_name, new_text)`
- `get_grasshopper_panel_data(file_name, panel_name)`

**Geometry Operations (3 tools):**
- `set_grasshopper_geometry_input(file_name, parameter_name, rhino_object_ids)`
- `extract_grasshopper_geometry_output(file_name, parameter_name)`
- `bake_grasshopper_geometry_to_rhino(file_name, parameter_name, layer_name)`

**Component Analysis (5 tools):**
- `get_grasshopper_components(file_name)` - List all components
- `get_grasshopper_overview(file_name)` - File statistics
- `debug_grasshopper_state(file_name)` - Debugging info
- `analyze_grasshopper_inputs_with_context(file_name)` - Input analysis
- `analyze_grasshopper_outputs_with_context(file_name)` - Output analysis

## How to Use

### Step 1: Prepare a Test GH File
Create a Grasshopper file with:
1. Several number sliders with clear names
2. A ValueList component
3. A Panel component
4. A geometry parameter (like a Curve parameter)
5. Save and open this file in Grasshopper

### Step 2: Copy Files to Tools Folder
```bash
# Replace tool files with Intermediate Integration versions
cp "Tools Archive/3Intermediate Integration/rhino_tools.py" ../
cp "Tools Archive/3Intermediate Integration/gh_tools.py" ../
```

### Step 3: Restart Rhino Bridge
Restart the bridge server to discover the new tools.

### Step 4: Test Advanced Operations

**Test 1 - Multiple Sliders:**
```
"Set multiple sliders: 'width' to 10, 'height' to 20, 'depth' to 5"
```

**Test 2 - ValueList:**
```
"List all value lists in the file, then change the first one to option 2"
```

**Test 3 - Geometry Transfer:**
```
"Get the selected curve from Rhino and feed it to the 'Input Curve' parameter in Grasshopper"
```

**Test 4 - Bake Results:**
```
"Bake the output geometry from 'Result' parameter to a layer called 'Generated'"
```

## Success Criteria
 Can manipulate multiple sliders simultaneously
 Can change ValueList selections
 Can transfer geometry from Rhino to Grasshopper
 Can extract and bake Grasshopper results
 All operations work on the active file

## Next Steps
Once comfortable with single-file operations:
 Move to **Level 4: Advanced Integration** for multi-file workflows and library management
