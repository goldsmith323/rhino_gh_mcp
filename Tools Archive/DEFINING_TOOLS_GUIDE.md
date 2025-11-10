# Tools Archive Setup Guide

## Quick Start

This archive contains **4 progressive integration levels** to help you learn the MCP Rhino/Grasshopper system step by step.

## Š Integration Levels Overview

| Level | Name | Files | Tools | Rhino Required | GH Required | Purpose |
|-------|------|-------|-------|----------------|-------------|---------|
| **1** | Test Integration | 1 file | 3 tools |  No |  No | Test MCP connection |
| **2** | Early Integration | 2 files | 3 tools |  Yes |  Yes | Test RH+GH connectivity |
| **3** | Intermediate Integration | 2 files | 18 tools |  Yes |  Yes | Single-file operations |
| **4** | Advanced Integration | 2 files | 37+ tools |  Yes |  Yes | Multi-file workflows |

## € How to Use This Archive

### Step 1: Start with Level 1

```bash
# Navigate to Tools directory
cd Tools/

# Copy Level 1 files
cp "Tools Archive/1. Test Integration/custom_tools.py" ./

# Restart Rhino bridge server (in Rhino Python)
# Run: Rhino/start_rhino_bridge.py
```

### Step 2: Test Level 1

Open your MCP client (your MCP client) and try:
```
"Use the hello_world tool"
"Use simple_math to calculate 5 + 3"
"Use echo_message to echo 'Testing MCP!'"
```

If all three work â†’  Move to Level 2

### Step 3: Progress Through Levels

For each level:
1. **Copy files** from that level's folder to `Tools/`
2. **Restart** Rhino bridge server
3. **Read** that level's README.md
4. **Test** the tools described in the README
5. **Verify** everything works before moving to next level

### Windows PowerShell Copy Commands

```powershell
# Level 1
Copy-Item "Tools Archive\1. Test Integration\*.py" -Destination .

# Level 2
Copy-Item "Tools Archive\2. Early Integration\*.py" -Destination .

# Level 3
Copy-Item "Tools Archive\3. Intermediate Integration\*.py" -Destination .

# Level 4
Copy-Item "Tools Archive\4. Advanced Integration\*.py" -Destination .
```

### Linux/Mac Copy Commands

```bash
# Level 1
cp "Tools Archive/1. Test Integration/"*.py ./

# Level 2
cp "Tools Archive/2. Early Integration/"*.py ./

# Level 3
cp "Tools Archive/3. Intermediate Integration/"*.py ./

# Level 4
cp "Tools Archive/4. Advanced Integration/"*.py ./
```

## ‹ What Each Level Tests

### Level 1: Test Integration 
**Files:** `custom_tools.py`
**Tools:**
- `hello_world()` - Verify MCP is working
- `simple_math(a, b, operation)` - Test parameter passing
- `echo_message(message)` - Test string handling

**Success criteria:**
- All 3 tools execute without errors
- No "connection refused" errors
- JSON responses received correctly

---

### Level 2: Early Integration ±
**Files:** `rhino_tools.py`, `gh_tools.py`
**Tools:**
- `draw_line_rhino(...)` - Draw line in Rhino
- `list_grasshopper_sliders(file_name)` - List GH sliders
- `set_grasshopper_slider(file_name, name, value)` - Change slider

**Success criteria:**
- Line appears in Rhino viewport
- Sliders are listed correctly
- Slider values change and GH recomputes

---

### Level 3: Intermediate Integration §
**Files:** `rhino_tools.py` (6 tools), `gh_tools.py` (12+ tools)

**Rhino Tools:**
- All Level 2 tools +
- `get_rhino_info()`, `typical_roof_truss_generator()`, `get_selected_rhino_objects()`, `get_rhino_object_geometry()`, `get_curve_length()`

**Grasshopper Tools:**
- Slider operations (list, set, set_multiple)
- ValueList operations
- Panel operations
- Geometry input/output
- Baking to Rhino
- Component inspection

**Success criteria:**
- Can manipulate multiple sliders at once
- Can transfer geometry Rhino â†” Grasshopper
- Can bake GH results to Rhino layers

---

### Level 4: Advanced Integration €
**Files:** `rhino_tools.py` (6 tools), `gh_tools.py` (31+ tools)

**Everything from Level 3 PLUS:**
- File management (list, open, close, switch between files)
- EML workflow system (multi-file geometry transfer)
- Advanced workflows (execute multi-step sequences)
- Custom Python script execution
- Workflow suggestions
- Grasshopper File Library management

**Success criteria:**
- Can work with multiple GH files simultaneously
- Can transfer geometry between different GH files
- Can execute complex multi-step workflows
- Can manage GH file library

---

## § Troubleshooting

### "Tool not found"
- **Solution:** Copy files to `Tools/` folder (not a subfolder!)
- **Solution:** Restart the Rhino bridge server

### "Bridge client not available"
- **Solution:** Check that `bridge_client.py` exists in `MCP/` folder
- **Solution:** Verify project structure is intact

### "Connection refused"
- **Solution:** Start the Rhino bridge server: run `Rhino/start_rhino_bridge.py` in Rhino
- **Solution:** Verify server shows "Server started on http://localhost:8080"

### "Rhino/Grasshopper not available"
- **Solution:** Make sure Rhino is running (for Level 2+)
- **Solution:** Make sure Grasshopper is open in Rhino (for Level 2+)
- **Solution:** Level 1 doesn't require Rhino/GH

## ¡ Tips for Success

1. **Don't skip levels** - Each level validates that the previous level's infrastructure works
2. **Read the READMEs** - Each level has specific instructions and test cases
3. **Test thoroughly** - Make sure everything works before moving forward
4. **Keep tool_registry.py** - Never delete this file, it's needed at all levels
5. **Restart after copying** - Always restart the bridge server after copying new tool files

## ¯ Final Goal

By the time you complete Level 4, you'll have:
-  A fully functional MCP Rhino/Grasshopper integration
-  37+ tools for parametric design automation
-  Multi-file workflow capabilities
-  Understanding of the entire system architecture
-  Ability to add your own custom tools

## š Additional Resources

- **Main project README:** `../../README.md`
- **MCP documentation:** `../../MCP/README.md`
- **Rhino bridge docs:** `../../Rhino/README.md`
- **Each level's README:** Located in each integration level folder

---

**Need help?** Check the README.md in each integration level folder for detailed instructions and troubleshooting specific to that level.
