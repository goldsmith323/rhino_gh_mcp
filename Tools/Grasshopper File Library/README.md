# Grasshopper File Library

This folder contains Grasshopper (.gh) files that can be opened and managed through the MCP server.

## Purpose

The MCP server automatically detects all `.gh` files in this directory and makes them available for:
- Opening multiple files simultaneously
- Interacting with components in specific files
- Exchanging data between different Grasshopper files
- Managing file-specific operations

## Usage

1. Place your Grasshopper (.gh) files in this directory
2. Use `list_gh_files` to see all available files
3. Use `open_gh_file` to open one or more files
4. Use file-specific tools with the `file_name` parameter to interact with specific files

## EML Convention

For components you want to interact with via MCP, use the `eml_{name}` naming convention:

### Examples:
- **Sliders**: `eml_panel_count`, `eml_beam_length`
- **Panels**: `eml_output_data`, `eml_results`
- **Boolean Toggles**: `eml_enable_feature`, `eml_show_preview`
- **Value Lists**: `eml_material_type`, `eml_section_size`
- **Primitives** (Number, Text, Integer): `eml_data_value`, `eml_label`
- **Geometry Parameters** (Curve, Brep, Line, etc.): `eml_input_curve`, `eml_output_geometry`

The `eml_` prefix allows the MCP system to automatically detect parameters for:
- Cross-file data exchange
- Automated parameter discovery
- Smart suggestions for connecting data between files

## File Organization

You can organize files however you like. All `.gh` files will be discovered recursively.
