# Level 4: Advanced Integration

## Purpose
This is the **complete, production-ready toolset** with all advanced features including:
- Multi-file Grasshopper workflows
- GH File Library management
- EML (External Multi-Link) parameter workflows
- Advanced geometry transfer between files
- Custom Python script execution
- Workflow suggestions and automation

**What's NEW in Level 4:**
- **All 19 tools from Level 3** (single-file operations)
- **PLUS 12 new tools** for multi-file workflows and library management
- **Total: 31 tools** for complete Grasshopper automation

## Prerequisites
-  Level 3 (Intermediate Integration) completed successfully
-  Understanding of Grasshopper workflows
-  Familiarity with the Grasshopper File Library structure

## What's Included

### All Tools from Level 3 (19 tools)
All single-file Grasshopper operations from Level 3 are included

### NEW in Level 4 - GH Library Management Tools (4 tools)
- `list_gh_files()` - List all files in GH Library with metadata
- `open_gh_file(file_name, open_multiple)` - Open files from library
- `open_all_gh_files(file_names)` - Open multiple files at once
- `close_gh_file(file_name, save_changes)` - Close files

### NEW in Level 4 - EML Workflow Tools (5 tools)
- `list_eml_parameters()` - Discover all eml_ prefixed parameters
- `get_eml_parameter_value(parameter_name)` - Read eml_ parameter
- `set_eml_parameter_value(parameter_name, value)` - Write eml_ parameter
- `suggest_eml_connections()` - Auto-suggest parameter connections
- `transfer_eml_geometry_between_files(source_file, source_param, target_file, target_param)` - Transfer geometry

### NEW in Level 4 - Advanced Workflows (4 tools)
- `execute_eml_workflow(workflow_steps)` - Execute multi-step workflows
- `execute_custom_python_script(script_code, inputs)` - Run custom Python in GH
- `suggest_gh_workflow(task_description)` - AI workflow suggestions
- `predict_truss_tonnage(span, depth)` - Tonnage prediction based on polynomial regression model from sample data

**Summary: 19 tools from Level 3 + 13 new tools = 32 total tools**

## Grasshopper File Library Structure

The Advanced Integration works with a **Grasshopper File Library** folder structure:

```
Tools/
├── Grasshopper File Library/
│   ├── metadata.json (defines workflows and file relationships)
│   ├── file1.gh
│   ├── file2.gh
│   └── ...
```

### metadata.json Structure
```json
{
  "library_info": {
    "name": "My GH Library",
    "version": "1.0",
    "description": "Collection of parametric tools"
  },
  "files": [
    {
      "filename": "Primary Generator.gh",
      "description": "Main geometry generator",
      "category": "Generators",
      "inputs": ["base_curve", "height", "divisions"],
      "outputs": ["result_geometry"],
      "workflow_position": 1
    }
  ],
  "workflows": [
    {
      "name": "Complete Generation Workflow",
      "description": "Full parametric workflow",
      "steps": [
        {"file": "file1.gh", "action": "open"},
        {"file": "file1.gh", "action": "set_param", "param": "slider1", "value": 10},
        {"file": "file2.gh", "action": "transfer_geometry"}
      ]
    }
  ]
}
```

## EML (External Multi-Link) System

The EML system enables **geometry transfer between different Grasshopper files** using specially named parameters:

### Naming Convention
- **Outputs:** `eml_output_<name>` - Mark parameters to export geometry
- **Inputs:** `eml_input_<name>` - Mark parameters to receive geometry

### Example Workflow
1. File1.gh has parameter: `eml_output_curves`
2. File2.gh has parameter: `eml_input_curves`
3. Use `transfer_eml_geometry_between_files()` to connect them
4. Geometry flows automatically from File1 → File2

## How to Use

### Step 1: Set Up Grasshopper File Library
1. Create a `Grasshopper File Library` folder in `Tools/`
2. Add your .gh files to this folder
3. Create a `metadata.json` file (optional but recommended)

### Step 2: Copy Files to Tools Folder
```bash
# Replace with Advanced Integration versions (full toolset)
cp "Tools Archive/4Advanced Integration/rhino_tools.py" ../
cp "Tools Archive/4Advanced Integration/gh_tools.py" ../
```

### Step 3: Restart Bridge Server
Restart to discover all advanced tools.

### Step 4: Test Advanced Features

**Test 1 - List Library Files:**
```
"List all Grasshopper files in the library"
```

**Test 2 - Open Multiple Files:**
```
"Open 'Generator.gh' and 'Processor.gh' from the library"
```

**Test 3 - EML Workflow:**
```
"List all eml_ parameters in the active file"
"Transfer geometry from 'Generator.gh' eml_output_curves to 'Processor.gh' eml_input_curves"
```

**Test 4 - Execute Workflow:**
```
"Execute the workflow defined in metadata.json: Complete Generation Workflow"
```

## Success Criteria
 Can manage multiple GH files simultaneously
 Can discover and use EML parameters
 Can transfer geometry between files
 Can execute multi-step workflows
 All file library features working

## Advanced Use Cases

### 1. Multi-File Parametric System
- File 1: Base geometry generator
- File 2: Optimization processor
- File 3: Documentation generator
- Use EML to link them together

### 2. Automated Workflow Execution
- Define workflows in metadata.json
- Execute complete sequences with one command
- Chain multiple operations together

### 3. Custom Python Integration
- Write custom Python scripts
- Execute them in Grasshopper context
- Access all Rhino/GH APIs

## Troubleshooting

**Problem:** "File not found in library"
- **Solution:** Check `Grasshopper File Library` folder exists in `Tools/`
- **Solution:** Verify file name matches exactly (case-sensitive)

**Problem:** "EML parameter not found"
- **Solution:** Parameters must be named with exact prefix: `eml_input_` or `eml_output_`
- **Solution:** Use `list_eml_parameters()` to see all available EML params

**Problem:** "Geometry transfer failed"
- **Solution:** Check geometry types are compatible
- **Solution:** Verify both source and target files are open
- **Solution:** Ensure target file is a valid GH file with the target parameter

## Production Tips

1. **Organize Your Library:** Use subfolders and clear file names
2. **Document Workflows:** Create comprehensive metadata.json
3. **Use EML Consistently:** Standardize parameter naming
4. **Test Incrementally:** Verify each step before chaining workflows
5. **Version Control:** Keep your .gh files in version control

## Next Steps

� **Congratulations!** You now have the complete MCP Rhino/Grasshopper integration toolkit.

### What You Can Build:
- Automated parametric design systems
- Multi-file generative workflows
- AI-driven design exploration
- Automated documentation generation
- Custom design tools and plugins

### Resources:
- Read the full tool documentation in each tool's description
- Check `metadata.json` examples in the library
- Explore EML patterns for your specific use cases
