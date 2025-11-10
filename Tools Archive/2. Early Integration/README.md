# Level 2: Early Integration

## Purpose
This level tests basic connectivity between the MCP server, Rhino 3D, and Grasshopper. You'll verify that the bridge can execute operations inside both Rhino and Grasshopper.

## Prerequisites
-  Level 1 (Test Integration) completed successfully
-  Rhino 3D installed and running
-  Grasshopper plugin loaded in Rhino

## What You'll Test
-  Bridge can communicate with Rhino 3D
-  Bridge can communicate with Grasshopper
-  Can create geometry in Rhino (line drawing)
-  Can list Grasshopper sliders
-  Can modify Grasshopper slider values
-  Grasshopper recomputes when sliders change

## Tools Included

### Rhino Tools (1 tool)
**`draw_line_rhino(start_x, start_y, start_z, end_x, end_y, end_z)`**
- Draw a line in Rhino 3D space
- Tests Rhino connectivity and geometry creation

### Grasshopper Tools (3 tools)
**`get_active_gh_files()`**
- Get information about all currently open Grasshopper files
- Returns file names, paths, and which one is currently active
- No parameters required - automatically detects open files

**`list_grasshopper_sliders(file_name)`**
- List all number sliders in specified GH file
- Returns slider names, current values, and ranges

**`set_grasshopper_slider(file_name, slider_name, new_value)`**
- Change a slider value and trigger recompute
- Tests Grasshopper parameter manipulation

## How to Use

### Step 1: Prepare a Test Grasshopper File
Create a simple .gh file with:
1. A number slider (name it "Test Slider")
2. Set range: 0 to 100
3. Connect it to any component (e.g., a Point component's X input)
4. Save the file and keep it open in Grasshopper

### Step 2: Copy Files to Tools Folder
```bash
# Replace the existing tool files with Early Integration versions
cp "Tools Archive/2Early Integration/rhino_tools.py" ../
cp "Tools Archive/2Early Integration/gh_tools.py" ../
```

### Step 3: Restart Rhino Bridge Server
1. In Rhino, if bridge is running, stop it first
2. Run: `Rhino/start_rhino_bridge.py`
3. Verify you see messages about discovered tools including:
   - `draw_line_rhino`
   - `list_grasshopper_sliders`
   - `set_grasshopper_slider`

### Step 4: Test Rhino Integration
**Test 1 - Draw a Line:**
```
"Use draw_line_rhino to draw a line from (0,0,0) to (10,10,10)"
```
Expected results:
-  Line appears in Rhino viewport
-  Response includes line ID and length (≈17.32)
-  No errors

### Step 5: Test Grasshopper Integration
**Test 2 - Get Active Files:**
```
"Use get_active_gh_files to see what Grasshopper files are open"
```
Expected results:
-  Shows your open .gh file
-  Indicates which file is active (is_active: true)
-  Shows file path and name
-  No errors

**Test 3 - List Sliders:**
```
"Use list_grasshopper_sliders with the file name from step 2 to show all sliders"
```
Expected results:
-  List includes your "Test Slider"
-  Shows current value and min/max range
-  No errors

**Test 4 - Change Slider Value:**
```
"Use set_grasshopper_slider to set 'Test Slider' to 50 in the active file"
```
Expected results:
-  Slider moves to 50 in Grasshopper
-  Connected components update
-  Response shows old value → new value
-  No errors

## Success Criteria
 Line appears in Rhino viewport
 Open Grasshopper files are detected and listed
 Active file is correctly identified
 Sliders are listed correctly
 Slider values change and Grasshopper recomputes
 All operations return success responses

## Troubleshooting

**Problem:** "Rhino is not available"
- **Solution:** Make sure Rhino is running and the bridge script is executed inside Rhino Python
- **Solution:** Check that rhinoscriptsyntax module is available

**Problem:** "Grasshopper is not available"
- **Solution:** Type `Grasshopper` in Rhino command line to launch Grasshopper
- **Solution:** Make sure a .gh file is open before testing

**Problem:** "No active Grasshopper document"
- **Solution:** Open a .gh file in Grasshopper (the one you created in Step 1)

**Problem:** "Slider not found"
- **Solution:** Check the exact name of your slider (case-insensitive but must match)
- **Solution:** Make sure the slider has a nickname/name set

**Problem:** "Value out of range"
- **Solution:** Check the slider's min/max values and use a value within that range

## Next Steps
Once all tests pass successfully:
1.  Your Rhino and Grasshopper connectivity is working
2.  You can manipulate Grasshopper parameters programmatically
3.  Move to **Level 3: Intermediate Integration** for more advanced single-file operations
