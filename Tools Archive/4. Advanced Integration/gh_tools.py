"""
Grasshopper Tools

This module contains all Grasshopper-specific MCP tools that communicate with the
Rhino bridge server to execute parametric operations within Grasshopper.

Tools are automatically registered using the @gh_tool decorator.
"""

import sys
import os
from typing import Dict, Any

# Import bridge_client from MCP directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MCP'))
from bridge_client import call_bridge_api

# Import the decorator system
try:
    from .tool_registry import gh_tool, bridge_handler
except ImportError:
    # Fallback for direct import
    from tool_registry import gh_tool, bridge_handler

# Get DEBUG_MODE from environment or bridge server
DEBUG_MODE = False
try:
    # Try to load from .env file in project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    env_file = os.path.join(project_root, '.env')

    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key.strip() == 'DEBUG_MODE':
                        DEBUG_MODE = value.strip().lower() == 'true'
                        break
    else:
        DEBUG_MODE = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'
except:
    DEBUG_MODE = False

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def filter_debug_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter response based on DEBUG_MODE setting.
    If DEBUG_MODE is False, removes verbose debugging information to save tokens.

    Always keeps: success, error, message, and essential data
    Removes when DEBUG_MODE=False: debug_log, traceback (unless error), detailed step info
    """
    if DEBUG_MODE:
        return response  # Return everything in debug mode

    # Create filtered response
    filtered = {}

    # Always include these keys
    essential_keys = [
        'success', 'error', 'message', 'warning',
        'file_name', 'file_path', 'parameter_name', 'value',
        'count', 'geometry_count', 'object_count', 'baked_count',
        'files', 'sliders', 'components', 'parameters',
        'geometry_types', 'layer_name', 'results'
    ]

    for key in essential_keys:
        if key in response:
            filtered[key] = response[key]

    # Include debug_log and traceback only if there's an error
    if not response.get('success', True):
        if 'debug_log' in response:
            # Include only last few debug entries for context
            debug_log = response['debug_log']
            if isinstance(debug_log, list) and len(debug_log) > 5:
                filtered['debug_log'] = debug_log[-5:]  # Last 5 entries only
            else:
                filtered['debug_log'] = debug_log
        if 'traceback' in response:
            filtered['traceback'] = response['traceback']

    # Copy any other keys not explicitly handled
    for key, value in response.items():
        if key not in essential_keys and key not in ['debug_log', 'traceback', 'cleared_operations']:
            filtered[key] = value

    return filtered


def ensure_file_is_active(file_name: str) -> Dict[str, Any]:
    """
    Helper function to ensure a specific Grasshopper file is active before performing operations.
    This makes all file interactions explicit and visible to the user.

    Args:
        file_name: Name of the .gh file that should be active

    Returns:
        Dict with 'success' boolean and optional 'error' message
    """
    if not file_name:
        return {"success": True}  # No specific file requested, use whatever is active

    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import os

        # Check if requested file is already active
        if Grasshopper.Instances.ActiveCanvas and Grasshopper.Instances.ActiveCanvas.Document:
            active_doc = Grasshopper.Instances.ActiveCanvas.Document
            if active_doc.FilePath:
                active_file_name = os.path.basename(str(active_doc.FilePath))
                if active_file_name.lower() == file_name.lower():
                    return {"success": True}  # Already active

        # Need to switch to the requested file
        # Call the set_active_gh_file handler directly
        result = handle_set_active_gh_file({"file_name": file_name})

        if not result.get("success", False):
            return {
                "success": False,
                "error": f"Failed to activate file '{file_name}': {result.get('error', 'Unknown error')}"
            }

        return {"success": True}

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error ensuring file is active: {str(e)}",
            "traceback": traceback.format_exc()
        }

# ============================================================================
# FILE MANAGEMENT TOOLS
# ============================================================================

@gh_tool(
    name="list_gh_files",
    description=(
        "List all Grasshopper (.gh) files available in the Grasshopper File Library with their metadata. "
        "This tool scans the 'Tools/Grasshopper File Library' directory and returns "
        "all .gh files with detailed information from metadata.json including descriptions, "
        "inputs, outputs, categories, and workflow relationships.\n\n"
        "**Returns:**\n"
        "Dictionary containing list of available .gh files with their paths, metadata, "
        "and available workflows. Use this to understand what files are available and how they work together."
    )
)
async def list_gh_files() -> Dict[str, Any]:
    """
    List all .gh files in the Grasshopper File Library with metadata.

    Returns:
        Dict containing available files information and metadata
    """
    return call_bridge_api("/list_gh_files", {})

@bridge_handler("/list_gh_files")
def handle_list_gh_files(data):
    """Bridge handler for listing .gh files in the library with metadata"""
    try:
        import os
        import json

        # Get the library path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        library_path = os.path.join(script_dir, "Grasshopper File Library")

        if not os.path.exists(library_path):
            return {
                "success": False,
                "error": f"Grasshopper File Library folder not found at: {library_path}",
                "files": []
            }

        # Load metadata if available
        metadata_path = os.path.join(library_path, "metadata.json")
        metadata = None
        metadata_files = {}

        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    # Create lookup by filename
                    if 'files' in metadata:
                        for file_meta in metadata['files']:
                            metadata_files[file_meta['filename']] = file_meta
            except Exception as e:
                # If metadata fails to load, continue without it
                pass

        # Find all .gh files recursively
        gh_files = []
        for root, dirs, files in os.walk(library_path):
            for file in files:
                if file.lower().endswith('.gh'):
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, library_path)

                    file_info = {
                        "name": file,
                        "relative_path": relative_path,
                        "full_path": full_path,
                        "size_bytes": os.path.getsize(full_path)
                    }

                    # Add metadata if available
                    if file in metadata_files:
                        file_meta = metadata_files[file]
                        file_info["description"] = file_meta.get("description", "")
                        file_info["category"] = file_meta.get("category", "")
                        file_info["tags"] = file_meta.get("tags", [])
                        file_info["inputs"] = file_meta.get("inputs", [])
                        file_info["outputs"] = file_meta.get("outputs", [])
                        file_info["workflow_position"] = file_meta.get("workflow_position")
                        file_info["dependencies"] = file_meta.get("dependencies", [])

                    gh_files.append(file_info)

        result = {
            "success": True,
            "files": gh_files,
            "count": len(gh_files),
            "library_path": library_path,
            "message": f"Found {len(gh_files)} Grasshopper file(s) in library"
        }

        # Include library info and workflows if metadata exists
        if metadata:
            if 'library_info' in metadata:
                result["library_info"] = metadata["library_info"]
            if 'workflows' in metadata:
                result["workflows"] = metadata["workflows"]
                result["workflow_count"] = len(metadata["workflows"])

        return result

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error listing .gh files: {str(e)}",
            "traceback": traceback.format_exc(),
            "files": []
        }

@gh_tool(
    name="open_gh_file",
    description=(
        "Open one or more Grasshopper files from the File Library. "
        "Files can be opened individually or multiple files can be opened at once. "
        "Once opened, you can interact with components in each file by specifying "
        "the file_name parameter in other tools.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str): Name of the .gh file to open (can be just filename or relative path)\n"
        "- **open_multiple** (bool, optional): If True, keeps existing files open. Default False (closes others)\n"
        "\n**Returns:**\n"
        "Dictionary containing the operation status and opened file information."
    )
)
async def open_gh_file(file_name: str, open_multiple: bool = False) -> Dict[str, Any]:
    """
    Open a Grasshopper file from the library.

    Args:
        file_name: Name or relative path of the .gh file to open
        open_multiple: If True, keeps other files open; if False, closes them first

    Returns:
        Dict containing operation results
    """
    request_data = {
        "file_name": file_name,
        "open_multiple": open_multiple
    }

    return call_bridge_api("/open_gh_file", request_data)

@bridge_handler("/open_gh_file")
def handle_open_gh_file(data):
    """Bridge handler for opening .gh files"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import os

        file_name = data.get('file_name', '')
        open_multiple = data.get('open_multiple', False)

        # Get the library path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        library_path = os.path.join(script_dir, "Grasshopper File Library")

        # Find the file
        target_file = None
        for root, dirs, files in os.walk(library_path):
            for file in files:
                if file == file_name or file.lower() == file_name.lower():
                    target_file = os.path.join(root, file)
                    break
                # Also check relative path match
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, library_path)
                if relative_path == file_name or relative_path.lower() == file_name.lower():
                    target_file = full_path
                    break
            if target_file:
                break

        if not target_file:
            return {
                "success": False,
                "error": f"File '{file_name}' not found in Grasshopper File Library",
                "file_name": file_name
            }

        if not os.path.exists(target_file):
            return {
                "success": False,
                "error": f"File path exists in search but not accessible: {target_file}",
                "file_name": file_name
            }

        debug_log = []
        import time

        # Ensure Grasshopper is loaded
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        grasshopper_just_launched = False

        if not gh:
            debug_log.append("Grasshopper not running - launching now...")
            # Try to load Grasshopper
            Rhino.RhinoApp.RunScript("_Grasshopper", False)

            # Wait for Grasshopper to initialize (with timeout)
            max_gh_wait = 15  # 15 attempts × 0.5s = 7.5 seconds
            for i in range(max_gh_wait):
                time.sleep(0.5)
                gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
                if gh:
                    grasshopper_just_launched = True
                    debug_log.append(f"✓ Grasshopper launched successfully after {(i+1)*0.5:.1f}s")
                    break
                debug_log.append(f"Waiting for Grasshopper to launch... ({i+1}/{max_gh_wait})")

            if not gh:
                return {
                    "success": False,
                    "error": "Grasshopper plugin could not be loaded after 7.5 seconds",
                    "file_name": file_name,
                    "debug_log": debug_log
                }
        else:
            debug_log.append("Grasshopper already running")

        debug_log.append(f"Attempting to open: {target_file}")
        debug_log.append(f"File exists: {os.path.exists(target_file)}")
        debug_log.append(f"File size: {os.path.getsize(target_file)} bytes")

        # Close other files if open_multiple is False
        if not open_multiple:
            debug_log.append("Single file mode - will keep existing files open (multi-file mode)")

        # Use gh.OpenDocument API (proper method)
        try:
            debug_log.append("Calling gh.OpenDocument()...")
            gh.OpenDocument(target_file)

            # Wait for document to load (with timeout)
            # Use longer timeout if Grasshopper just launched
            max_attempts = 20 if grasshopper_just_launched else 10
            if grasshopper_just_launched:
                debug_log.append("Using extended timeout (20 attempts) since Grasshopper just launched")

            attempt = 0
            doc_opened = False

            while attempt < max_attempts:
                time.sleep(0.3)  # Wait a bit for loading

                # Check if document is now active
                if Grasshopper.Instances.ActiveCanvas and Grasshopper.Instances.ActiveCanvas.Document:
                    gh_doc = Grasshopper.Instances.ActiveCanvas.Document

                    if gh_doc.FilePath:
                        opened_path = str(gh_doc.FilePath)
                        debug_log.append(f"Attempt {attempt + 1}: Active document is {os.path.basename(opened_path)}")

                        # Check if it's our file (normalize paths for comparison)
                        if os.path.normpath(opened_path).lower() == os.path.normpath(target_file).lower():
                            doc_opened = True
                            debug_log.append(f"✓ Successfully opened and verified: {file_name}")
                            debug_log.append(f"Document has {gh_doc.ObjectCount} objects")
                            break
                    else:
                        debug_log.append(f"Attempt {attempt + 1}: Active document has no FilePath")
                else:
                    debug_log.append(f"Attempt {attempt + 1}: No active canvas/document yet")

                attempt += 1

            if not doc_opened:
                # Check if file is at least in document server (opened but not active)
                doc_server = Grasshopper.Instances.DocumentServer
                found_in_server = False
                if doc_server:
                    for doc in doc_server:
                        if doc and hasattr(doc, 'FilePath') and doc.FilePath:
                            if os.path.normpath(str(doc.FilePath)).lower() == os.path.normpath(target_file).lower():
                                found_in_server = True
                                debug_log.append(f"⚠ File is open in document server but not active")
                                debug_log.append(f"Document has {doc.ObjectCount} objects")
                                break

                if found_in_server:
                    result = {
                        "success": True,
                        "warning": "File opened but may not be the active document",
                        "message": f"Opened '{file_name}' (check Grasshopper window - may need to switch tabs)",
                        "file_name": file_name,
                        "file_path": target_file,
                        "debug_log": debug_log
                    }
                    return filter_debug_response(result)
                else:
                    result = {
                        "success": False,
                        "error": f"File opening timed out or failed - file may have errors or missing plugins",
                        "file_name": file_name,
                        "file_path": target_file,
                        "debug_log": debug_log,
                        "suggestion": "Check Grasshopper window for error messages or missing plugin warnings"
                    }
                    return filter_debug_response(result)

            result = {
                "success": True,
                "message": f"Successfully opened and verified '{file_name}'",
                "file_name": file_name,
                "file_path": target_file,
                "object_count": gh_doc.ObjectCount if doc_opened else None,
                "debug_log": debug_log
            }
            return filter_debug_response(result)

        except Exception as e:
            import traceback
            debug_log.append(f"Exception during opening: {str(e)}")
            debug_log.append(f"Traceback: {traceback.format_exc()[:500]}")

            result = {
                "success": False,
                "error": f"Failed to open file: {str(e)}",
                "file_name": file_name,
                "file_path": target_file,
                "debug_log": debug_log,
                "traceback": traceback.format_exc()
            }
            return filter_debug_response(result)

    except Exception as e:
        import traceback
        result = {
            "success": False,
            "error": f"Error opening .gh file: {str(e)}",
            "traceback": traceback.format_exc(),
            "file_name": data.get('file_name', 'unknown')
        }
        return filter_debug_response(result)

@gh_tool(
    name="get_active_gh_files",
    description=(
        "Get information about all currently open Grasshopper files. "
        "Returns details about each open document including file paths, "
        "names, and which one is currently active.\n\n"
        "**Returns:**\n"
        "Dictionary containing list of open Grasshopper documents."
    )
)
async def get_active_gh_files() -> Dict[str, Any]:
    """
    Get all currently open Grasshopper files.

    Returns:
        Dict containing information about open files
    """
    return call_bridge_api("/get_active_gh_files", {})

@bridge_handler("/get_active_gh_files")
def handle_get_active_gh_files(data):
    """Bridge handler for getting active .gh files"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import os

        # Get the Grasshopper plugin
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "open_files": []
            }

        open_files = []
        active_doc_path = None

        # Get the active document path
        if Grasshopper.Instances.ActiveCanvas and Grasshopper.Instances.ActiveCanvas.Document:
            active_doc = Grasshopper.Instances.ActiveCanvas.Document
            if active_doc.FilePath:
                active_doc_path = os.path.normpath(str(active_doc.FilePath)).lower()

        # Iterate through ALL open documents using DocumentServer
        doc_server = Grasshopper.Instances.DocumentServer
        if doc_server:
            for doc in doc_server:
                if doc and hasattr(doc, 'FilePath') and doc.FilePath:
                    file_path = str(doc.FilePath)
                    file_name = os.path.basename(file_path)
                    normalized_path = os.path.normpath(file_path).lower()

                    # Check if this is the active document
                    is_active = (active_doc_path is not None and normalized_path == active_doc_path)

                    open_files.append({
                        "name": file_name,
                        "path": file_path,
                        "is_active": is_active,
                        "is_modified": doc.IsModified if hasattr(doc, 'IsModified') else False,
                        "object_count": doc.ObjectCount if hasattr(doc, 'ObjectCount') else 0
                    })

        if len(open_files) == 0:
            return {
                "success": False,
                "error": "No open Grasshopper documents found",
                "open_files": []
            }

        return {
            "success": True,
            "open_files": open_files,
            "count": len(open_files),
            "message": f"Found {len(open_files)} open Grasshopper document(s)"
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error getting active files: {str(e)}",
            "traceback": traceback.format_exc(),
            "open_files": []
        }

@gh_tool(
    name="set_active_gh_file",
    description=(
        "Set a specific Grasshopper file as active/focused. Use this to switch between multiple "
        "open Grasshopper documents.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, required): Name of the .gh file to make active (e.g., 'Primary Truss Generator.gh')\n"
        "\n**Returns:**\n"
        "Dictionary indicating success or failure of switching the active document."
    )
)
async def set_active_gh_file(file_name: str) -> Dict[str, Any]:
    """
    Set a specific open Grasshopper file as the active document.

    Args:
        file_name: Name of the .gh file to activate

    Returns:
        Dict containing operation results
    """
    request_data = {
        "file_name": file_name
    }

    return call_bridge_api("/set_active_gh_file", request_data)

@bridge_handler("/set_active_gh_file")
def handle_set_active_gh_file(data):
    """Bridge handler for setting active .gh file - using simple OpenDocument approach"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import os
        import time

        file_name = data.get('file_name', '')
        if not file_name:
            return {
                "success": False,
                "error": "No file name provided"
            }

        # Get the Grasshopper plugin
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }

        # Find the document in DocumentServer to get its full path
        doc_server = Grasshopper.Instances.DocumentServer
        target_doc = None
        target_path = None

        if doc_server:
            for doc in doc_server:
                if doc and hasattr(doc, 'FilePath') and doc.FilePath:
                    current_file_name = os.path.basename(str(doc.FilePath))
                    if current_file_name.lower() == file_name.lower():
                        target_doc = doc
                        target_path = str(doc.FilePath)
                        break

        if not target_doc or not target_path:
            return {
                "success": False,
                "error": f"Document '{file_name}' not found in open documents. Make sure it's already open."
            }

        # Check if already active
        if Grasshopper.Instances.ActiveCanvas and Grasshopper.Instances.ActiveCanvas.Document == target_doc:
            return {
                "success": True,
                "message": f"'{file_name}' is already active",
                "file_name": file_name,
                "file_path": target_path,
                "method": "AlreadyActive"
            }

        # THE SIMPLE APPROACH: Call gh.OpenDocument() on the already-open file
        # This will switch to the existing document instead of opening a duplicate
        try:
            # Call OpenDocument on the file that's already open
            gh.OpenDocument(target_path)

            # Give it a moment to switch
            time.sleep(0.3)

            # Verify the switch worked
            if Grasshopper.Instances.ActiveCanvas and Grasshopper.Instances.ActiveCanvas.Document:
                active_doc = Grasshopper.Instances.ActiveCanvas.Document
                if active_doc == target_doc or (active_doc.FilePath and os.path.normpath(str(active_doc.FilePath)).lower() == os.path.normpath(target_path).lower()):
                    return {
                        "success": True,
                        "message": f"Successfully switched to '{file_name}' using OpenDocument",
                        "file_name": file_name,
                        "file_path": target_path,
                        "method": "OpenDocument"
                    }

            # If we get here, something didn't work as expected
            return {
                "success": False,
                "error": f"OpenDocument was called but '{file_name}' is not the active document",
                "file_name": file_name,
                "file_path": target_path,
                "current_active": os.path.basename(str(Grasshopper.Instances.ActiveCanvas.Document.FilePath)) if Grasshopper.Instances.ActiveCanvas and Grasshopper.Instances.ActiveCanvas.Document and Grasshopper.Instances.ActiveCanvas.Document.FilePath else "Unknown"
            }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": f"Error calling OpenDocument: {str(e)}",
                "traceback": traceback.format_exc(),
                "file_name": file_name,
                "file_path": target_path
            }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error setting active file: {str(e)}",
            "traceback": traceback.format_exc()
        }


@gh_tool(
    name="open_all_gh_files",
    description=(
        "Open all Grasshopper files from the library at once. This will launch Grasshopper if "
        "not already running, then open all .gh files found in the Grasshopper File Library.\n\n"
        "**Parameters:**\n"
        "- **file_names** (list, optional): Specific files to open. If not provided, opens all files in library.\n"
        "\n**Returns:**\n"
        "Dictionary containing results for each file opened."
    )
)
async def open_all_gh_files(file_names=None) -> Dict[str, Any]:
    """
    Open all (or specified) Grasshopper files.

    Args:
        file_names: Optional list of specific filenames to open

    Returns:
        Dict containing open results for each file
    """
    request_data = {
        "file_names": file_names
    }

    return call_bridge_api("/open_all_gh_files", request_data)

@bridge_handler("/open_all_gh_files")
def handle_open_all_gh_files(data):
    """Bridge handler for opening multiple .gh files"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import os

        file_names = data.get('file_names', None)
        import time

        overall_debug_log = []

        # Ensure Grasshopper is loaded
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        grasshopper_just_launched = False

        if not gh:
            overall_debug_log.append("Grasshopper not running - launching now...")
            # Try to load Grasshopper
            Rhino.RhinoApp.RunScript("_Grasshopper", False)

            # Wait for Grasshopper to initialize (with timeout)
            max_gh_wait = 15  # 15 attempts × 0.5s = 7.5 seconds
            for i in range(max_gh_wait):
                time.sleep(0.5)
                gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
                if gh:
                    grasshopper_just_launched = True
                    overall_debug_log.append(f"✓ Grasshopper launched successfully after {(i+1)*0.5:.1f}s")
                    break
                overall_debug_log.append(f"Waiting for Grasshopper to launch... ({i+1}/{max_gh_wait})")

            if not gh:
                return {
                    "success": False,
                    "error": "Grasshopper plugin could not be loaded after 7.5 seconds",
                    "debug_log": overall_debug_log
                }
        else:
            overall_debug_log.append("Grasshopper already running")

        # Get the library path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        library_path = os.path.join(script_dir, "Grasshopper File Library")

        # Get all .gh files if no specific files requested
        if not file_names:
            file_names = []
            for root, dirs, files in os.walk(library_path):
                for file in files:
                    if file.lower().endswith('.gh'):
                        file_names.append(file)

        if not file_names:
            return {
                "success": False,
                "error": "No .gh files found in library"
            }

        # Open each file with verification
        results = []

        # Use longer timeout if Grasshopper just launched
        base_max_attempts = 12 if grasshopper_just_launched else 8
        if grasshopper_just_launched:
            overall_debug_log.append(f"Using extended timeout ({base_max_attempts} attempts per file) since Grasshopper just launched")

        for file_name in file_names:
            debug_log = []
            debug_log.append(f"Processing: {file_name}")

            # Find the file
            target_file = None
            for root, dirs, files in os.walk(library_path):
                for file in files:
                    if file.lower() == file_name.lower():
                        target_file = os.path.join(root, file)
                        break
                if target_file:
                    break

            if not target_file:
                debug_log.append(f"File not found in library")
                results.append({
                    "file_name": file_name,
                    "success": False,
                    "error": f"File not found: {file_name}",
                    "debug_log": debug_log
                })
                overall_debug_log.extend(debug_log)
                continue

            debug_log.append(f"Found file: {target_file}")
            debug_log.append(f"File size: {os.path.getsize(target_file)} bytes")

            # Use gh.OpenDocument API
            try:
                debug_log.append("Calling gh.OpenDocument()...")
                gh.OpenDocument(target_file)

                # Wait for document to load
                max_attempts = base_max_attempts
                attempt = 0
                doc_opened = False

                while attempt < max_attempts:
                    time.sleep(0.3)

                    # Check if document loaded
                    doc_server = Grasshopper.Instances.DocumentServer
                    if doc_server:
                        for doc in doc_server:
                            if doc and hasattr(doc, 'FilePath') and doc.FilePath:
                                if os.path.normpath(str(doc.FilePath)).lower() == os.path.normpath(target_file).lower():
                                    doc_opened = True
                                    debug_log.append(f"✓ Verified opened: {file_name} ({doc.ObjectCount} objects)")
                                    break

                    if doc_opened:
                        break

                    attempt += 1

                if doc_opened:
                    results.append({
                        "file_name": file_name,
                        "file_path": target_file,
                        "success": True,
                        "message": f"Opened {file_name}",
                        "debug_log": debug_log
                    })
                else:
                    debug_log.append(f"⚠ Timeout - file may have errors or missing plugins")
                    results.append({
                        "file_name": file_name,
                        "file_path": target_file,
                        "success": False,
                        "error": f"Opening timed out or failed",
                        "debug_log": debug_log
                    })

                overall_debug_log.extend(debug_log)

            except Exception as e:
                import traceback
                debug_log.append(f"Exception: {str(e)}")
                debug_log.append(f"Traceback: {traceback.format_exc()[:300]}")
                results.append({
                    "file_name": file_name,
                    "success": False,
                    "error": str(e),
                    "debug_log": debug_log
                })
                overall_debug_log.extend(debug_log)

        success_count = sum(1 for r in results if r.get('success', False))

        result = {
            "success": True,
            "files_opened": success_count,
            "total_files": len(file_names),
            "results": results,
            "overall_debug_log": overall_debug_log,
            "message": f"Opened {success_count} of {len(file_names)} file(s)"
        }
        return filter_debug_response(result)

    except Exception as e:
        import traceback
        result = {
            "success": False,
            "error": f"Error opening files: {str(e)}",
            "traceback": traceback.format_exc()
        }
        return filter_debug_response(result)

@gh_tool(
    name="close_gh_file",
    description=(
        "Close a specific Grasshopper file by name. "
        "If the file has unsaved changes, you can specify whether to save or discard them.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str): Name of the .gh file to close\n"
        "- **save_changes** (bool, optional): If True, saves changes before closing. Default False\n"
        "\n**Returns:**\n"
        "Dictionary containing the operation status."
    )
)
async def close_gh_file(file_name: str, save_changes: bool = False) -> Dict[str, Any]:
    """
    Close a Grasshopper file.

    Args:
        file_name: Name of the .gh file to close
        save_changes: Whether to save changes before closing

    Returns:
        Dict containing operation results
    """
    request_data = {
        "file_name": file_name,
        "save_changes": save_changes
    }

    return call_bridge_api("/close_gh_file", request_data)

@bridge_handler("/close_gh_file")
def handle_close_gh_file(data):
    """Bridge handler for closing .gh files"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import os

        file_name = data.get('file_name', '')
        save_changes = data.get('save_changes', False)

        # Get the Grasshopper plugin
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }

        # Get the active document
        if not Grasshopper.Instances.ActiveCanvas:
            return {
                "success": False,
                "error": "No active Grasshopper document"
            }

        active_doc = Grasshopper.Instances.ActiveCanvas.Document
        if not active_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document"
            }

        # Check if this is the file to close
        current_path = str(active_doc.FilePath) if active_doc.FilePath else ""
        current_name = os.path.basename(current_path) if current_path else "Untitled"

        if current_name.lower() != file_name.lower() and file_name.lower() != "untitled":
            return {
                "success": False,
                "error": f"File '{file_name}' is not the active document. Currently active: '{current_name}'"
            }

        # Save if requested
        if save_changes and active_doc.IsModified:
            if active_doc.FilePath:
                success = active_doc.Write(active_doc.FilePath)
                if not success:
                    return {
                        "success": False,
                        "error": "Failed to save file before closing"
                    }

        # Close using Rhino command
        Rhino.RhinoApp.RunScript("_GrasshopperClose", False)

        return {
            "success": True,
            "message": f"Closed Grasshopper file: {file_name}",
            "file_name": file_name,
            "changes_saved": save_changes
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error closing file: {str(e)}",
            "traceback": traceback.format_exc()
        }

# ============================================================================
# EML PARAMETER DISCOVERY AND MANAGEMENT
# ============================================================================

@gh_tool(
    name="list_eml_parameters",
    description=(
        "Discover all EML (eml_) prefixed parameters in the active Grasshopper file. "
        "The eml_ naming convention is used to mark components for automated interaction "
        "and cross-file data exchange. This tool finds all components with names starting "
        "with 'eml_' including:\n\n"
        "- **Sliders**: Number sliders for numeric input\n"
        "- **Panels**: Text panels for output or input\n"
        "- **Boolean Toggles**: True/False switches\n"
        "- **Value Lists**: Dropdown selection components\n"
        "- **Number Primitives**: Number containers\n"
        "- **Text Primitives**: Text containers\n"
        "- **Integer Primitives**: Integer containers\n"
        "- **Geometry Parameters**: Curve, Brep, Line, Surface, Point, etc.\n\n"
        "Each parameter includes metadata about its type, current value, direction (input/output), "
        "and connection status to help with cross-file data exchange.\n\n"
        "**Returns:**\n"
        "Dictionary containing categorized lists of all eml_ parameters."
    )
)
async def list_eml_parameters() -> Dict[str, Any]:
    """
    List all eml_ prefixed parameters in the Grasshopper document.

    Returns:
        Dict containing categorized eml_ parameters
    """
    return call_bridge_api("/list_eml_parameters", {})

@bridge_handler("/list_eml_parameters")
def handle_list_eml_parameters(data):
    """Bridge handler for discovering all eml_ prefixed parameters"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }

        # Storage for categorized parameters
        eml_params = {
            "sliders": [],
            "panels": [],
            "boolean_toggles": [],
            "value_lists": [],
            "number_primitives": [],
            "text_primitives": [],
            "integer_primitives": [],
            "geometry_params": []
        }

        # Scan all objects in the document
        for obj in gh_doc.Objects:
            try:
                nick_name = obj.NickName or ""
                if not nick_name.lower().startswith("eml_"):
                    continue

                # Get common properties
                obj_guid = str(obj.InstanceGuid)
                has_sources = hasattr(obj, 'SourceCount') and obj.SourceCount > 0
                has_recipients = hasattr(obj, 'Recipients') and obj.Recipients.Count > 0

                # Determine direction
                if has_sources and has_recipients:
                    direction = "passthrough"
                elif has_sources:
                    direction = "output"
                elif has_recipients:
                    direction = "input"
                else:
                    direction = "isolated"

                base_info = {
                    "name": nick_name,
                    "guid": obj_guid,
                    "direction": direction,
                    "has_sources": has_sources,
                    "has_recipients": has_recipients,
                    "description": obj.Description if hasattr(obj, 'Description') else ""
                }

                # 1. Number Sliders
                if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                    eml_params["sliders"].append({
                        **base_info,
                        "current_value": float(str(obj.Slider.Value)),
                        "min_value": float(str(obj.Slider.Minimum)),
                        "max_value": float(str(obj.Slider.Maximum)),
                        "precision": obj.Slider.DecimalPlaces,
                        "slider_type": obj.Slider.Type.ToString()
                    })

                # 2. Panels
                elif isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                    panel_text = ""
                    if hasattr(obj, 'Properties') and hasattr(obj.Properties, 'UserText'):
                        panel_text = str(obj.Properties.UserText)

                    eml_params["panels"].append({
                        **base_info,
                        "text": panel_text,
                        "multiline": obj.Properties.Multiline if hasattr(obj, 'Properties') else True
                    })

                # 3. Boolean Toggles
                elif isinstance(obj, Grasshopper.Kernel.Special.GH_BooleanToggle):
                    eml_params["boolean_toggles"].append({
                        **base_info,
                        "value": bool(obj.Value) if hasattr(obj, 'Value') else False
                    })

                # 4. Value Lists
                elif isinstance(obj, Grasshopper.Kernel.Special.GH_ValueList):
                    selected_items = []
                    all_items = []

                    if hasattr(obj, 'ListItems'):
                        for item in obj.ListItems:
                            item_name = str(item.Name) if hasattr(item, 'Name') else str(item)
                            all_items.append(item_name)
                            if hasattr(item, 'Selected') and item.Selected:
                                selected_items.append(item_name)

                    eml_params["value_lists"].append({
                        **base_info,
                        "selected_items": selected_items,
                        "all_items": all_items
                    })

                # 5. Number Primitives
                elif type(obj).__name__ == 'GH_NumberParameter' or 'Param_Number' in type(obj).__name__:
                    values = []
                    if hasattr(obj, 'VolatileData'):
                        for branch in obj.VolatileData.Branches:
                            for item in branch:
                                try:
                                    values.append(float(str(item)))
                                except:
                                    pass

                    eml_params["number_primitives"].append({
                        **base_info,
                        "type": "Number",
                        "values": values,
                        "value_count": len(values)
                    })

                # 6. Integer Primitives
                elif type(obj).__name__ == 'GH_IntegerParameter' or 'Param_Integer' in type(obj).__name__:
                    values = []
                    if hasattr(obj, 'VolatileData'):
                        for branch in obj.VolatileData.Branches:
                            for item in branch:
                                try:
                                    values.append(int(str(item)))
                                except:
                                    pass

                    eml_params["integer_primitives"].append({
                        **base_info,
                        "type": "Integer",
                        "values": values,
                        "value_count": len(values)
                    })

                # 7. Text/String Primitives
                elif type(obj).__name__ == 'GH_StringParameter' or 'Param_String' in type(obj).__name__:
                    values = []
                    if hasattr(obj, 'VolatileData'):
                        for branch in obj.VolatileData.Branches:
                            for item in branch:
                                values.append(str(item))

                    eml_params["text_primitives"].append({
                        **base_info,
                        "type": "Text",
                        "values": values,
                        "value_count": len(values)
                    })

                # 8. Geometry Parameters
                elif any(geom_type in type(obj).__name__ for geom_type in [
                    'Param_Curve', 'Param_Surface', 'Param_Brep', 'Param_Geometry',
                    'Param_Line', 'Param_Circle', 'Param_Arc', 'Param_Point',
                    'Param_Mesh', 'Param_Plane', 'Param_Vector'
                ]):
                    geom_count = 0
                    if hasattr(obj, 'VolatileDataCount'):
                        geom_count = obj.VolatileDataCount

                    eml_params["geometry_params"].append({
                        **base_info,
                        "geometry_type": type(obj).__name__.replace('Param_', '').replace('GH_', ''),
                        "geometry_count": geom_count,
                        "has_geometry": geom_count > 0
                    })

            except Exception as e:
                # Skip components that cause errors
                continue

        # Calculate totals
        total_count = sum(len(v) for v in eml_params.values())

        return {
            "success": True,
            "eml_parameters": eml_params,
            "summary": {
                "total_count": total_count,
                "sliders": len(eml_params["sliders"]),
                "panels": len(eml_params["panels"]),
                "boolean_toggles": len(eml_params["boolean_toggles"]),
                "value_lists": len(eml_params["value_lists"]),
                "number_primitives": len(eml_params["number_primitives"]),
                "text_primitives": len(eml_params["text_primitives"]),
                "integer_primitives": len(eml_params["integer_primitives"]),
                "geometry_params": len(eml_params["geometry_params"])
            },
            "message": f"Found {total_count} eml_ prefixed parameters"
        }

    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error discovering eml_ parameters: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="get_eml_parameter_value",
    description=(
        "Get the current value(s) from any eml_ prefixed parameter. "
        "Works with all parameter types including sliders, panels, toggles, primitives, "
        "and geometry parameters. For geometry parameters, returns metadata about the "
        "geometry rather than the actual geometry data.\n\n"
        "**Parameters:**\n"
        "- **parameter_name** (str): The name of the eml_ parameter (e.g., 'eml_panel_count')\n"
        "\n**Returns:**\n"
        "Dictionary containing the parameter value(s) and metadata."
    )
)
async def get_eml_parameter_value(parameter_name: str) -> Dict[str, Any]:
    """
    Get value from an eml_ parameter.

    Args:
        parameter_name: Name of the eml_ parameter

    Returns:
        Dict containing parameter value and metadata
    """
    request_data = {
        "parameter_name": parameter_name
    }

    return call_bridge_api("/get_eml_parameter_value", request_data)

@bridge_handler("/get_eml_parameter_value")
def handle_get_eml_parameter_value(data):
    """Bridge handler for getting eml_ parameter values"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino

        parameter_name = data.get('parameter_name', '')

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }

        # Find the parameter
        for obj in gh_doc.Objects:
            nick_name = obj.NickName or ""
            if nick_name.lower() == parameter_name.lower():
                # Slider
                if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                    return {
                        "success": True,
                        "parameter_name": nick_name,
                        "type": "slider",
                        "value": float(str(obj.Slider.Value))
                    }

                # Panel
                elif isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                    panel_text = ""
                    if hasattr(obj, 'Properties') and hasattr(obj.Properties, 'UserText'):
                        panel_text = str(obj.Properties.UserText)
                    return {
                        "success": True,
                        "parameter_name": nick_name,
                        "type": "panel",
                        "value": panel_text
                    }

                # Boolean Toggle
                elif isinstance(obj, Grasshopper.Kernel.Special.GH_BooleanToggle):
                    return {
                        "success": True,
                        "parameter_name": nick_name,
                        "type": "boolean_toggle",
                        "value": bool(obj.Value) if hasattr(obj, 'Value') else False
                    }

                # Value List
                elif isinstance(obj, Grasshopper.Kernel.Special.GH_ValueList):
                    selected_items = []
                    if hasattr(obj, 'ListItems'):
                        for item in obj.ListItems:
                            if hasattr(item, 'Selected') and item.Selected:
                                selected_items.append(str(item.Name) if hasattr(item, 'Name') else str(item))
                    return {
                        "success": True,
                        "parameter_name": nick_name,
                        "type": "value_list",
                        "value": selected_items
                    }

                # Primitives (Number, Integer, Text)
                elif hasattr(obj, 'VolatileData'):
                    values = []
                    for branch in obj.VolatileData.Branches:
                        for item in branch:
                            values.append(str(item))

                    param_type = "unknown"
                    if 'Number' in type(obj).__name__:
                        param_type = "number"
                        values = [float(v) for v in values]
                    elif 'Integer' in type(obj).__name__:
                        param_type = "integer"
                        values = [int(v) for v in values]
                    elif 'String' in type(obj).__name__:
                        param_type = "text"
                    elif any(g in type(obj).__name__ for g in ['Curve', 'Brep', 'Surface', 'Point', 'Line']):
                        param_type = "geometry"
                        values = [f"{type(item).__name__}" for item in obj.VolatileData.AllData(True)]

                    return {
                        "success": True,
                        "parameter_name": nick_name,
                        "type": param_type,
                        "values": values,
                        "value_count": len(values)
                    }

        return {
            "success": False,
            "error": f"Parameter '{parameter_name}' not found",
            "parameter_name": parameter_name
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error getting parameter value: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="set_eml_parameter_value",
    description=(
        "Set the value of any eml_ prefixed parameter. "
        "Supports sliders, panels, boolean toggles, value lists, and primitive parameters. "
        "For geometry parameters, use the existing set_grasshopper_geometry_input tool.\n\n"
        "**Parameters:**\n"
        "- **parameter_name** (str): The name of the eml_ parameter\n"
        "- **value** (any): The value to set (type depends on parameter type)\n"
        "  - Slider: float/int\n"
        "  - Panel: string\n"
        "  - Boolean: true/false\n"
        "  - Value List: string (item name)\n"
        "  - Number/Integer: float/int\n"
        "  - Text: string\n"
        "\n**Returns:**\n"
        "Dictionary containing the operation status."
    )
)
async def set_eml_parameter_value(parameter_name: str, value: Any) -> Dict[str, Any]:
    """
    Set value for an eml_ parameter.

    Args:
        parameter_name: Name of the eml_ parameter
        value: Value to set

    Returns:
        Dict containing operation results
    """
    request_data = {
        "parameter_name": parameter_name,
        "value": value
    }

    return call_bridge_api("/set_eml_parameter_value", request_data)

@bridge_handler("/set_eml_parameter_value")
def handle_set_eml_parameter_value(data):
    """Bridge handler for setting eml_ parameter values"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import System

        parameter_name = data.get('parameter_name', '')
        value = data.get('value')

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }

        # Find and set the parameter
        for obj in gh_doc.Objects:
            nick_name = obj.NickName or ""
            if nick_name.lower() == parameter_name.lower():
                # Slider
                if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                    new_value = float(value)
                    clamped_value = max(float(str(obj.Slider.Minimum)),
                                      min(float(str(obj.Slider.Maximum)), new_value))
                    obj.Slider.Value = System.Decimal.Parse(str(clamped_value))
                    gh_doc.NewSolution(True)
                    return {
                        "success": True,
                        "parameter_name": nick_name,
                        "type": "slider",
                        "old_value": None,
                        "new_value": clamped_value
                    }

                # Panel
                elif isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                    if hasattr(obj, 'Properties'):
                        obj.Properties.UserText = str(value)
                    gh_doc.NewSolution(True)
                    return {
                        "success": True,
                        "parameter_name": nick_name,
                        "type": "panel",
                        "new_value": str(value)
                    }

                # Boolean Toggle
                elif isinstance(obj, Grasshopper.Kernel.Special.GH_BooleanToggle):
                    obj.Value = bool(value)
                    gh_doc.NewSolution(True)
                    return {
                        "success": True,
                        "parameter_name": nick_name,
                        "type": "boolean_toggle",
                        "new_value": bool(value)
                    }

                # Value List
                elif isinstance(obj, Grasshopper.Kernel.Special.GH_ValueList):
                    if hasattr(obj, 'ListItems'):
                        for item in obj.ListItems:
                            item_name = str(item.Name) if hasattr(item, 'Name') else str(item)
                            if item_name.lower() == str(value).lower():
                                item.Selected = True
                            else:
                                item.Selected = False
                    gh_doc.NewSolution(True)
                    return {
                        "success": True,
                        "parameter_name": nick_name,
                        "type": "value_list",
                        "new_value": str(value)
                    }

                # For primitives, we can't directly set values as they receive from upstream
                else:
                    return {
                        "success": False,
                        "error": f"Parameter type '{type(obj).__name__}' does not support direct value setting (primitives receive values from connected components)",
                        "parameter_name": nick_name
                    }

        return {
            "success": False,
            "error": f"Parameter '{parameter_name}' not found",
            "parameter_name": parameter_name
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error setting parameter value: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="suggest_eml_connections",
    description=(
        "Analyze eml_ parameters in the current Grasshopper file and suggest potential "
        "data connections between them. This tool identifies output parameters that could "
        "feed into input parameters based on type compatibility and naming patterns. "
        "Particularly useful for understanding data flow and setting up cross-file data exchange.\n\n"
        "The tool categorizes parameters by direction:\n"
        "- **Outputs**: Parameters with data that could be extracted\n"
        "- **Inputs**: Parameters waiting for data input\n"
        "- **Isolated**: Parameters with no connections\n\n"
        "It then suggests compatible connections based on data types.\n\n"
        "**Returns:**\n"
        "Dictionary containing parameter categorization and suggested connections."
    )
)
async def suggest_eml_connections() -> Dict[str, Any]:
    """
    Analyze and suggest connections between eml_ parameters.

    Returns:
        Dict containing connection suggestions
    """
    return call_bridge_api("/suggest_eml_connections", {})

@bridge_handler("/suggest_eml_connections")
def handle_suggest_eml_connections(data):
    """Bridge handler for suggesting eml_ parameter connections"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }

        # Get file information
        file_path = str(gh_doc.FilePath) if gh_doc.FilePath else "Untitled"
        file_name = os.path.basename(file_path) if file_path != "Untitled" else "Untitled"

        # Categorize parameters
        outputs = []  # Has data, could export
        inputs = []   # Waiting for data
        isolated = [] # No connections

        for obj in gh_doc.Objects:
            try:
                nick_name = obj.NickName or ""
                if not nick_name.lower().startswith("eml_"):
                    continue

                obj_guid = str(obj.InstanceGuid)
                has_sources = hasattr(obj, 'SourceCount') and obj.SourceCount > 0
                has_recipients = hasattr(obj, 'Recipients') and obj.Recipients.Count > 0
                has_data = False
                data_count = 0

                # Check for data
                if hasattr(obj, 'VolatileDataCount'):
                    data_count = obj.VolatileDataCount
                    has_data = data_count > 0

                # Determine parameter type
                param_type = "unknown"
                if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                    param_type = "slider_number"
                    has_data = True
                elif isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                    param_type = "panel_text"
                elif isinstance(obj, Grasshopper.Kernel.Special.GH_BooleanToggle):
                    param_type = "boolean"
                    has_data = True
                elif isinstance(obj, Grasshopper.Kernel.Special.GH_ValueList):
                    param_type = "value_list"
                    has_data = True
                elif 'Number' in type(obj).__name__:
                    param_type = "number"
                elif 'Integer' in type(obj).__name__:
                    param_type = "integer"
                elif 'String' in type(obj).__name__:
                    param_type = "text"
                elif 'Curve' in type(obj).__name__:
                    param_type = "curve"
                elif 'Brep' in type(obj).__name__:
                    param_type = "brep"
                elif 'Surface' in type(obj).__name__:
                    param_type = "surface"
                elif 'Point' in type(obj).__name__:
                    param_type = "point"
                elif 'Line' in type(obj).__name__:
                    param_type = "line"
                elif 'Mesh' in type(obj).__name__:
                    param_type = "mesh"

                param_info = {
                    "name": nick_name,
                    "type": param_type,
                    "guid": obj_guid,
                    "has_data": has_data,
                    "data_count": data_count
                }

                # Categorize by connection status
                if has_sources and not has_recipients:
                    # Has input but no output = terminal/output
                    if has_data:
                        outputs.append(param_info)
                    else:
                        isolated.append(param_info)
                elif has_recipients and not has_sources:
                    # Has output but no input = source/input
                    if has_data:
                        outputs.append(param_info)
                    else:
                        inputs.append(param_info)
                elif not has_sources and not has_recipients:
                    # No connections
                    if has_data:
                        outputs.append(param_info)
                    else:
                        isolated.append(param_info)
                else:
                    # Has both = passthrough
                    if has_data:
                        outputs.append(param_info)

            except Exception as e:
                continue

        # Suggest connections based on type compatibility
        suggestions = []
        for output_param in outputs:
            for input_param in inputs:
                # Check type compatibility
                compatible = False
                reason = ""

                output_type = output_param["type"]
                input_type = input_param["type"]

                # Exact type match
                if output_type == input_type:
                    compatible = True
                    reason = f"Exact type match: {output_type}"

                # Numeric compatibility
                elif output_type in ["slider_number", "number", "integer"] and input_type in ["number", "integer"]:
                    compatible = True
                    reason = "Numeric types are compatible"

                # Text compatibility
                elif output_type in ["panel_text", "text", "value_list"] and input_type in ["text", "panel_text"]:
                    compatible = True
                    reason = "Text types are compatible"

                # Geometry compatibility (broader)
                elif output_type in ["curve", "line"] and input_type in ["curve", "geometry"]:
                    compatible = True
                    reason = f"{output_type.capitalize()} can be used as curve input"
                elif output_type in ["brep", "surface"] and input_type in ["brep", "surface", "geometry"]:
                    compatible = True
                    reason = f"{output_type.capitalize()} can be used as surface/brep input"

                # Name similarity (suggests intent)
                name_similarity = 0
                output_words = output_param["name"].lower().replace("eml_", "").split("_")
                input_words = input_param["name"].lower().replace("eml_", "").split("_")
                common_words = set(output_words) & set(input_words)
                if common_words:
                    name_similarity = len(common_words) / max(len(output_words), len(input_words))
                    if name_similarity > 0.3:
                        compatible = True
                        reason += f" (names suggest related purpose: {', '.join(common_words)})"

                if compatible:
                    suggestions.append({
                        "from_parameter": output_param["name"],
                        "from_type": output_type,
                        "to_parameter": input_param["name"],
                        "to_type": input_type,
                        "reason": reason,
                        "confidence": "high" if output_type == input_type else "medium"
                    })

        return {
            "success": True,
            "file_name": file_name,
            "file_path": file_path,
            "outputs": outputs,
            "inputs": inputs,
            "isolated": isolated,
            "suggestions": suggestions,
            "summary": {
                "total_eml_params": len(outputs) + len(inputs) + len(isolated),
                "output_params": len(outputs),
                "input_params": len(inputs),
                "isolated_params": len(isolated),
                "suggested_connections": len(suggestions)
            },
            "message": f"Analyzed {len(outputs) + len(inputs) + len(isolated)} eml_ parameters and found {len(suggestions)} potential connections"
        }

    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error analyzing connections: {str(e)}",
            "traceback": traceback.format_exc()
        }

# ============================================================================
# EXISTING GRASSHOPPER TOOLS
# ============================================================================

@gh_tool(
    name="list_grasshopper_sliders",
    description=(
        "List all available slider components in a specific Grasshopper file. "
        "This tool will activate the specified file (making it visible to the user), "
        "then scan it to find all number slider components and return their names and current values.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, required): Name of the .gh file to list sliders from (e.g., 'Primary Truss Generator.gh')\n"
        "\n**Returns:**\n"
        "Dictionary containing list of sliders with their names and current values."
    )
)
async def list_grasshopper_sliders(file_name: str) -> Dict[str, Any]:
    """
    List all slider components in a specific Grasshopper file via HTTP bridge.

    Args:
        file_name: Name of the .gh file to list sliders from

    Returns:
        Dict containing slider information
    """

    request_data = {
        "file_name": file_name
    }

    return call_bridge_api("/list_sliders", request_data)

@bridge_handler("/list_sliders")
def handle_list_sliders(data):
    """Bridge handler for list sliders requests"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino

        file_name = data.get('file_name', '')

        # Ensure the correct file is active first
        activation_result = ensure_file_is_active(file_name)
        if not activation_result.get("success", False):
            return {
                "success": False,
                "error": activation_result.get("error", "Failed to activate file"),
                "file_name": file_name,
                "sliders": []
            }

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "file_name": file_name,
                "sliders": []
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "file_name": file_name,
                "sliders": []
            }
        
        sliders = []
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                slider_info = {
                    "name": obj.NickName or "Unnamed",
                    "current_value": float(str(obj.Slider.Value)),
                    "min_value": float(str(obj.Slider.Minimum)),
                    "max_value": float(str(obj.Slider.Maximum)),
                    "precision": obj.Slider.DecimalPlaces,
                    "type": obj.Slider.Type.ToString()
                }
                sliders.append(slider_info)
        
        return {
            "success": True,
            "sliders": sliders,
            "count": len(sliders),
            "message": f"Found {len(sliders)} slider components"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "sliders": []
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error listing sliders: {str(e)}",
            "traceback": traceback.format_exc(),
            "sliders": []
        }

@gh_tool(
    name="set_grasshopper_slider",
    description=(
        "Change the value of a Grasshopper slider component by name in a specific Grasshopper file. "
        "This tool will activate the specified file (making it visible to the user), "
        "then find the slider component and update its value. "
        "Use 'get_active_gh_files' to see all open files and 'list_grasshopper_sliders' to see available sliders.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, required): Name of the .gh file containing the slider (e.g., 'Primary Truss Generator.gh')\n"
        "- **slider_name** (str): The name/nickname of the slider component to modify\n"
        "- **new_value** (float): The new value to set for the slider\n"
        "\n**Returns:**\n"
        "Dictionary containing the operation status and updated slider information."
    )
)
async def set_grasshopper_slider(file_name: str, slider_name: str, new_value: float) -> Dict[str, Any]:
    """
    Set the value of a Grasshopper slider by name via HTTP bridge.

    Args:
        file_name: Name of the .gh file containing the slider
        slider_name: Name of the slider component
        new_value: New value to set

    Returns:
        Dict containing operation results
    """

    request_data = {
        "file_name": file_name,
        "slider_name": slider_name,
        "new_value": new_value
    }

    return call_bridge_api("/set_slider", request_data)

@bridge_handler("/set_slider")
def handle_set_slider(data):
    """Bridge handler for set slider requests"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import System

        file_name = data.get('file_name', '')
        slider_name = data.get('slider_name', '')
        new_value = float(data.get('new_value', 0))

        # Ensure the correct file is active first
        activation_result = ensure_file_is_active(file_name)
        if not activation_result.get("success", False):
            return {
                "success": False,
                "error": activation_result.get("error", "Failed to activate file"),
                "file_name": file_name,
                "slider_name": slider_name,
                "new_value": new_value
            }

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "file_name": file_name,
                "slider_name": slider_name,
                "new_value": new_value
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "file_name": file_name,
                "slider_name": slider_name,
                "new_value": new_value
            }
        
        # Find the slider component
        slider_found = False
        old_value = None
        clamped_value = new_value
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                if (obj.NickName or "Unnamed") == slider_name:
                    slider_found = True
                    old_value = float(str(obj.Slider.Value))
                    
                    # Clamp value to slider bounds
                    clamped_value = max(float(str(obj.Slider.Minimum)), 
                                      min(float(str(obj.Slider.Maximum)), new_value))
                    
                    # Set the new value
                    obj.Slider.Value = System.Decimal.Parse(str(clamped_value))
                    
                    # Trigger solution recompute
                    gh_doc.NewSolution(True)
                    
                    break
        
        if not slider_found:
            return {
                "success": False,
                "error": f"Slider '{slider_name}' not found",
                "slider_name": slider_name,
                "new_value": new_value
            }
        
        return {
            "success": True,
            "slider_name": slider_name,
            "old_value": old_value,
            "new_value": clamped_value,
            "clamped": clamped_value != new_value,
            "message": f"Slider '{slider_name}' updated to {clamped_value}" + 
                      (f" (clamped from {new_value})" if clamped_value != new_value else "")
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "slider_name": data.get('slider_name', ''),
            "new_value": data.get('new_value', 0)
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error setting slider: {str(e)}",
            "traceback": traceback.format_exc(),
            "slider_name": data.get('slider_name', ''),
            "new_value": data.get('new_value', 0)
        }

@gh_tool(
    name="get_grasshopper_overview",
    description=(
        "Get an overview of the current Grasshopper definition including file information, "
        "component counts, and general structure. This provides a high-level summary "
        "of what's loaded in Grasshopper.\n\n"
        "**Returns:**\n"
        "Dictionary containing file info, component counts, and document status."
    )
)
async def get_grasshopper_overview() -> Dict[str, Any]:
    """
    Get overview of the current Grasshopper definition via HTTP bridge.
    
    Returns:
        Dict containing file overview information
    """
    
    return call_bridge_api("/grasshopper_overview", {})

@bridge_handler("/grasshopper_overview")
def handle_grasshopper_overview(data):
    """Bridge handler for grasshopper overview requests"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }
        
        # Count different component types
        component_counts = {}
        slider_count = 0
        panel_count = 0
        param_count = 0
        total_objects = 0
        
        for obj in gh_doc.Objects:
            total_objects += 1
            obj_type = type(obj).__name__
            component_counts[obj_type] = component_counts.get(obj_type, 0) + 1
            
            if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                slider_count += 1
            elif isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                panel_count += 1
            elif hasattr(obj, 'Category') and obj.Category == "Params":
                param_count += 1
        
        # Get document properties
        doc_properties = {
            "is_modified": gh_doc.IsModified,
            "is_enabled": gh_doc.Enabled,
            "object_count": total_objects,
            "slider_count": slider_count,
            "panel_count": panel_count,
            "parameter_count": param_count
        }
        
        # Try to get file path if available
        file_path = "Unknown"
        if hasattr(gh_doc, 'FilePath') and gh_doc.FilePath:
            file_path = gh_doc.FilePath
        
        return {
            "success": True,
            "file_path": file_path,
            "document_properties": doc_properties,
            "component_counts": component_counts,
            "summary": f"Document contains {total_objects} total objects including {slider_count} sliders and {panel_count} panels"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error getting overview: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="analyze_grasshopper_sliders",
    description=(
        "Analyze all sliders in the current Grasshopper definition, including their connections "
        "and inferred purposes. This provides detailed information about what each slider controls "
        "based on connected components and naming patterns.\n\n"
        "**Returns:**\n"
        "Dictionary containing detailed slider analysis with connections and purposes."
    )
)
async def analyze_grasshopper_sliders() -> Dict[str, Any]:
    """
    Analyze sliders with connection details and purpose inference via HTTP bridge.
    
    Returns:
        Dict containing detailed slider analysis
    """
    
    return call_bridge_api("/analyze_sliders", {})

@bridge_handler("/analyze_sliders")
def handle_analyze_sliders(data):
    """Bridge handler for slider analysis requests"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }
        
        sliders = []
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                slider_info = {
                    "name": obj.NickName or "Unnamed",
                    "current_value": float(str(obj.Slider.Value)),
                    "min_value": float(str(obj.Slider.Minimum)),
                    "max_value": float(str(obj.Slider.Maximum)),
                    "precision": obj.Slider.DecimalPlaces,
                    "type": obj.Slider.Type.ToString(),
                    "connected_components": [],
                    "inferred_purpose": "Unknown",
                    "position": {"x": float(obj.Attributes.Pivot.X), "y": float(obj.Attributes.Pivot.Y)}
                }
                
                # Analyze connections - Sliders have Recipients directly, not through Params
                try:
                    if hasattr(obj, 'Recipients') and obj.Recipients.Count > 0:
                        for recipient in obj.Recipients:
                            try:
                                component = recipient.Attributes.GetTopLevel.DocObject if hasattr(recipient.Attributes, 'GetTopLevel') else None
                                if component:
                                    connected_info = {
                                        "component_name": component.NickName or type(component).__name__,
                                        "component_type": type(component).__name__,
                                        "parameter_name": recipient.NickName or recipient.Name if hasattr(recipient, 'NickName') else "Unknown",
                                        "parameter_description": recipient.Description if hasattr(recipient, 'Description') else ""
                                    }
                                    slider_info["connected_components"].append(connected_info)
                            except:
                                continue
                except:
                    pass  # If we can't get connections, just skip
                
                # Infer purpose based on name and connections
                slider_name_lower = slider_info["name"].lower()
                connected_types = [conn["component_type"] for conn in slider_info["connected_components"]]
                
                if any(keyword in slider_name_lower for keyword in ["width", "w", "x"]):
                    slider_info["inferred_purpose"] = "Width/X-dimension control"
                elif any(keyword in slider_name_lower for keyword in ["height", "h", "y"]):
                    slider_info["inferred_purpose"] = "Height/Y-dimension control"
                elif any(keyword in slider_name_lower for keyword in ["depth", "d", "z"]):
                    slider_info["inferred_purpose"] = "Depth/Z-dimension control"
                elif any(keyword in slider_name_lower for keyword in ["count", "num", "n"]):
                    slider_info["inferred_purpose"] = "Count/quantity control"
                elif any(keyword in slider_name_lower for keyword in ["angle", "rot", "rotation"]):
                    slider_info["inferred_purpose"] = "Angle/rotation control"
                elif any(keyword in slider_name_lower for keyword in ["scale", "size"]):
                    slider_info["inferred_purpose"] = "Scale/size control"
                elif any(keyword in slider_name_lower for keyword in ["offset", "shift"]):
                    slider_info["inferred_purpose"] = "Offset/position control"
                elif "GH_Move" in connected_types or "Transform" in connected_types:
                    slider_info["inferred_purpose"] = "Transformation parameter"
                elif "GH_Divide" in connected_types or "Division" in connected_types:
                    slider_info["inferred_purpose"] = "Division/array parameter"
                elif len(slider_info["connected_components"]) > 0:
                    slider_info["inferred_purpose"] = f"Parameter for {slider_info['connected_components'][0]['component_name']}"
                
                sliders.append(slider_info)
        
        return {
            "success": True,
            "sliders": sliders,
            "count": len(sliders),
            "summary": f"Found {len(sliders)} sliders with connection analysis"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error analyzing sliders: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="get_grasshopper_components",
    description=(
        "Get a comprehensive list of all components in the current Grasshopper definition, "
        "including their types, parameters, and connections. This provides a complete map "
        "of the grasshopper definition structure.\n\n"
        "**Returns:**\n"
        "Dictionary containing all components with their details and connections."
    )
)
async def get_grasshopper_components() -> Dict[str, Any]:
    """
    Get all components in the current Grasshopper definition via HTTP bridge.
    
    Returns:
        Dict containing all component information
    """
    
    return call_bridge_api("/get_components", {})

@bridge_handler("/get_components")
def handle_get_components(data):
    """Bridge handler for getting all components"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }
        
        components = []
        
        for obj in gh_doc.Objects:
            component_info = {
                "name": obj.NickName or "Unnamed",
                "type": type(obj).__name__,
                "category": obj.Category if hasattr(obj, 'Category') else "Unknown",
                "subcategory": obj.SubCategory if hasattr(obj, 'SubCategory') else "Unknown",
                "position": {"x": float(obj.Attributes.Pivot.X), "y": float(obj.Attributes.Pivot.Y)},
                "inputs": [],
                "outputs": [],
                "is_special": False,
                "special_type": None
            }
            
            # Check for special component types
            if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                component_info["is_special"] = True
                component_info["special_type"] = "NumberSlider"
                component_info["slider_info"] = {
                    "current_value": float(str(obj.Slider.Value)),
                    "min_value": float(str(obj.Slider.Minimum)),
                    "max_value": float(str(obj.Slider.Maximum)),
                    "precision": obj.Slider.DecimalPlaces
                }
            elif isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                component_info["is_special"] = True
                component_info["special_type"] = "Panel"
                component_info["panel_text"] = obj.UserText if hasattr(obj, 'UserText') else ""
            elif isinstance(obj, Grasshopper.Kernel.Special.GH_ValueList):
                component_info["is_special"] = True
                component_info["special_type"] = "ValueList"
                component_info["list_items"] = []
                if hasattr(obj, 'ListItems'):
                    for item in obj.ListItems:
                        component_info["list_items"].append({
                            "name": item.Name,
                            "value": str(item.Value)
                        })
            
            # Get input parameters
            if hasattr(obj, 'Params') and obj.Params.Input:
                for i in range(obj.Params.Input.Count):
                    param = obj.Params.Input[i]
                    param_info = {
                        "name": param.NickName or param.Name,
                        "description": param.Description if hasattr(param, 'Description') else "",
                        "type": type(param).__name__,
                        "optional": param.Optional,
                        "source_count": param.SourceCount
                    }
                    component_info["inputs"].append(param_info)
            
            # Get output parameters
            if hasattr(obj, 'Params') and obj.Params.Output:
                for i in range(obj.Params.Output.Count):
                    param = obj.Params.Output[i]
                    param_info = {
                        "name": param.NickName or param.Name,
                        "description": param.Description if hasattr(param, 'Description') else "",
                        "type": type(param).__name__,
                        "recipient_count": param.Recipients.Count
                    }
                    component_info["outputs"].append(param_info)
            
            components.append(component_info)
        
        # Group components by category
        categories = {}
        for comp in components:
            cat = comp["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(comp["name"])
        
        return {
            "success": True,
            "components": components,
            "total_count": len(components),
            "categories": categories,
            "special_components": [comp for comp in components if comp["is_special"]],
            "summary": f"Found {len(components)} total components across {len(categories)} categories"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error getting components: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="set_multiple_grasshopper_sliders",
    description=(
        "Set multiple Grasshopper slider values at once in a specific file. "
        "This tool will activate the specified file (making it visible to the user), "
        "then efficiently update multiple parameters simultaneously.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, required): Name of the .gh file containing the sliders (e.g., 'Primary Truss Generator.gh')\n"
        "- **slider_updates** (dict): Dictionary mapping slider names to new values\n"
        "\n**Returns:**\n"
        "Dictionary containing the results of all slider updates."
    )
)
async def set_multiple_grasshopper_sliders(file_name: str, slider_updates: Dict[str, float]) -> Dict[str, Any]:
    """
    Set multiple Grasshopper sliders at once via HTTP bridge.

    Args:
        file_name: Name of the .gh file containing the sliders
        slider_updates: Dictionary mapping slider names to new values

    Returns:
        Dict containing batch operation results
    """

    request_data = {
        "file_name": file_name,
        "slider_updates": slider_updates
    }

    return call_bridge_api("/set_multiple_sliders", request_data)

@bridge_handler("/set_multiple_sliders")
def handle_set_multiple_sliders(data):
    """Bridge handler for setting multiple sliders at once"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import System

        file_name = data.get('file_name', '')
        slider_updates = data.get('slider_updates', {})

        if not slider_updates:
            return {
                "success": False,
                "error": "No slider updates provided",
                "file_name": file_name
            }

        # Ensure the correct file is active first
        activation_result = ensure_file_is_active(file_name)
        if not activation_result.get("success", False):
            return {
                "success": False,
                "error": activation_result.get("error", "Failed to activate file"),
                "file_name": file_name
            }

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "file_name": file_name
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "file_name": file_name
            }
        
        # Cache slider components for efficient batch processing
        slider_components = {}
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                slider_name = obj.NickName or "Unnamed"
                slider_components[slider_name] = obj
        
        results = []
        success_count = 0
        
        # Disable solver during batch updates
        gh.DisableSolver()
        
        try:
            for slider_name, new_value in slider_updates.items():
                try:
                    if slider_name in slider_components:
                        obj = slider_components[slider_name]
                        old_value = float(str(obj.Slider.Value))
                        
                        # Clamp value to slider bounds
                        clamped_value = max(float(str(obj.Slider.Minimum)), 
                                          min(float(str(obj.Slider.Maximum)), float(new_value)))
                        
                        obj.Slider.Value = System.Decimal.Parse(str(clamped_value))
                        
                        results.append({
                            "slider_name": slider_name,
                            "success": True,
                            "old_value": old_value,
                            "new_value": float(clamped_value),
                            "clamped": clamped_value != float(new_value)
                        })
                        success_count += 1
                    else:
                        results.append({
                            "slider_name": slider_name,
                            "success": False,
                            "error": f"Slider '{slider_name}' not found"
                        })
                        
                except Exception as e:
                    results.append({
                        "slider_name": slider_name,
                        "success": False,
                        "error": f"Error setting slider: {str(e)}"
                    })
            
            # Re-enable solver and compute solution
            gh.EnableSolver()
            gh_doc.NewSolution(True)
            
        except Exception as e:
            # Ensure solver is re-enabled even if batch update fails
            gh.EnableSolver()
            raise e
        
        return {
            "success": True,
            "results": results,
            "total_updates": len(slider_updates),
            "successful_updates": success_count,
            "failed_updates": len(slider_updates) - success_count,
            "summary": f"Successfully updated {success_count} of {len(slider_updates)} sliders"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error in batch slider update: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="debug_grasshopper_state",
    description=(
        "Get comprehensive debugging information about the current Grasshopper state. "
        "This tool provides detailed information for troubleshooting issues including "
        "plugin status, document state, component errors, and system information.\n\n"
        "**Returns:**\n"
        "Dictionary containing detailed debugging information about Grasshopper state."
    )
)
async def debug_grasshopper_state() -> Dict[str, Any]:
    """
    Get comprehensive debugging information about Grasshopper state via HTTP bridge.
    
    Returns:
        Dict containing detailed debugging information
    """
    
    return call_bridge_api("/debug_state", {})

@bridge_handler("/debug_state")
def handle_debug_state(data):
    """Bridge handler for debugging state requests"""
    try:
        import clr
        import sys
        import os
        
        debug_info = {
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "clr_version": str(clr.version) if hasattr(clr, 'version') else "Unknown"
            },
            "assemblies_loaded": [],
            "grasshopper_status": {},
            "document_status": {},
            "component_errors": [],
            "warnings": []
        }
        
        # Check loaded assemblies
        try:
            for assembly in clr.References:
                debug_info["assemblies_loaded"].append(str(assembly))
        except Exception as e:
            debug_info["warnings"].append(f"Could not enumerate assemblies: {str(e)}")
        
        try:
            clr.AddReference('Grasshopper')
            clr.AddReference('RhinoCommon')
            import Grasshopper
            import Rhino
            
            # Check Grasshopper plugin status
            gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
            if gh:
                debug_info["grasshopper_status"] = {
                    "plugin_available": True,
                    "plugin_type": str(type(gh)),
                    "is_loaded": True
                }
                
                # Check document status
                if Grasshopper.Instances.ActiveCanvas:
                    gh_doc = Grasshopper.Instances.ActiveCanvas.Document
                    if gh_doc:
                        debug_info["document_status"] = {
                            "document_available": True,
                            "is_modified": gh_doc.IsModified,
                            "is_enabled": gh_doc.Enabled,
                            "object_count": gh_doc.Objects.Count,
                            "file_path": gh_doc.FilePath if hasattr(gh_doc, 'FilePath') and gh_doc.FilePath else "Unsaved",
                            "solver_status": "Unknown"
                        }
                        
                        # Count component types and check for errors
                        component_summary = {}
                        error_count = 0
                        warning_count = 0
                        
                        for obj in gh_doc.Objects:
                            obj_type = type(obj).__name__
                            component_summary[obj_type] = component_summary.get(obj_type, 0) + 1
                            
                            # Check for component runtime messages (errors/warnings)
                            if hasattr(obj, 'RuntimeMessages'):
                                for message in obj.RuntimeMessages:
                                    message_info = {
                                        "component": obj.NickName or obj_type,
                                        "level": str(message.Level),
                                        "message": str(message.Text)
                                    }
                                    
                                    if "Error" in str(message.Level):
                                        error_count += 1
                                        debug_info["component_errors"].append(message_info)
                                    elif "Warning" in str(message.Level):
                                        warning_count += 1
                                        debug_info["warnings"].append(message_info)
                        
                        debug_info["document_status"]["component_summary"] = component_summary
                        debug_info["document_status"]["error_count"] = error_count
                        debug_info["document_status"]["warning_count"] = warning_count
                        
                    else:
                        debug_info["document_status"] = {
                            "document_available": False,
                            "error": "No active Grasshopper document"
                        }
                else:
                    debug_info["document_status"] = {
                        "document_available": False,
                        "error": "No active Grasshopper canvas"
                    }
            else:
                debug_info["grasshopper_status"] = {
                    "plugin_available": False,
                    "error": "Grasshopper plugin not found"
                }
                
        except ImportError as e:
            debug_info["grasshopper_status"] = {
                "plugin_available": False,
                "error": f"Cannot import Grasshopper: {str(e)}"
            }
        except Exception as e:
            debug_info["grasshopper_status"] = {
                "plugin_available": False,
                "error": f"Unexpected error: {str(e)}"
            }
        
        # Add environment info
        debug_info["environment"] = {
            "rhino_version": "Unknown",
            "grasshopper_version": "Unknown"
        }
        
        try:
            import Rhino
            debug_info["environment"]["rhino_version"] = str(Rhino.RhinoApp.Version)
        except:
            pass
            
        try:
            import Grasshopper
            if hasattr(Grasshopper, 'Versioning'):
                debug_info["environment"]["grasshopper_version"] = str(Grasshopper.Versioning.Version)
        except:
            pass
        
        return {
            "success": True,
            "debug_info": debug_info,
            "summary": f"Debug info collected - {len(debug_info['component_errors'])} errors, {len(debug_info['warnings'])} warnings"
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error collecting debug info: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="list_grasshopper_valuelist_components",
    description=(
        "List all ValueList components in a specific Grasshopper file. "
        "This tool will activate the specified file (making it visible to the user), "
        "then scan for ValueList components (dropdown menus with predefined options) "
        "and return their names, current selections, and available options.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, required): Name of the .gh file to list valuelists from (e.g., 'Primary Truss Generator.gh')\n"
        "\n**Returns:**\n"
        "Dictionary containing list of ValueList components with their options and current selections."
    )
)
async def list_grasshopper_valuelist_components(file_name: str) -> Dict[str, Any]:
    """
    List all ValueList components in a specific Grasshopper file via HTTP bridge.

    Args:
        file_name: Name of the .gh file to list valuelists from

    Returns:
        Dict containing ValueList information
    """

    request_data = {
        "file_name": file_name
    }

    return call_bridge_api("/list_valuelists", request_data)

@bridge_handler("/list_valuelists")
def handle_list_valuelists(data):
    """Bridge handler for listing ValueList components"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino

        file_name = data.get('file_name', '')

        # Ensure the correct file is active first
        activation_result = ensure_file_is_active(file_name)
        if not activation_result.get("success", False):
            return {
                "success": False,
                "error": activation_result.get("error", "Failed to activate file"),
                "file_name": file_name,
                "valuelist_components": []
            }

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "file_name": file_name,
                "valuelist_components": []
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "file_name": file_name,
                "valuelist_components": []
            }
        
        valuelist_components = []
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_ValueList):
                valuelist_info = {
                    "name": obj.NickName or "Unnamed",
                    "current_selection_index": obj.SelectionIndex,
                    "current_selection_name": None,
                    "current_selection_value": None,
                    "list_items": []
                }
                
                # Get all available items
                if hasattr(obj, 'ListItems'):
                    for i, item in enumerate(obj.ListItems):
                        item_info = {
                            "index": i,
                            "name": item.Name,
                            "value": str(item.Value)
                        }
                        valuelist_info["list_items"].append(item_info)
                        
                        # Mark current selection
                        if i == obj.SelectionIndex:
                            valuelist_info["current_selection_name"] = item.Name
                            valuelist_info["current_selection_value"] = str(item.Value)
                
                valuelist_components.append(valuelist_info)
        
        return {
            "success": True,
            "valuelist_components": valuelist_components,
            "count": len(valuelist_components),
            "message": f"Found {len(valuelist_components)} ValueList components"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "valuelist_components": []
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error listing ValueList components: {str(e)}",
            "traceback": traceback.format_exc(),
            "valuelist_components": []
        }

@gh_tool(
    name="set_grasshopper_valuelist_selection",
    description=(
        "Change the selected item in a Grasshopper ValueList component in a specific file. "
        "This tool will activate the specified file (making it visible to the user), "
        "then find the ValueList component and update its selection. "
        "Use 'get_active_gh_files' to see open files and 'list_grasshopper_valuelist_components' to see available ValueLists.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, required): Name of the .gh file containing the ValueList (e.g., 'Primary Truss Generator.gh')\n"
        "- **valuelist_name** (str): The name/nickname of the ValueList component to modify\n"
        "- **selection** (str or int): Either the name of the item to select or its index number\n"
        "\n**Returns:**\n"
        "Dictionary containing the operation status and updated ValueList information."
    )
)
async def set_grasshopper_valuelist_selection(file_name: str, valuelist_name: str, selection: str) -> Dict[str, Any]:
    """
    Set the selected item in a Grasshopper ValueList component via HTTP bridge.

    Args:
        file_name: Name of the .gh file containing the ValueList
        valuelist_name: Name of the ValueList component
        selection: Name or index of the item to select

    Returns:
        Dict containing operation results
    """

    request_data = {
        "file_name": file_name,
        "valuelist_name": valuelist_name,
        "selection": selection
    }

    return call_bridge_api("/set_valuelist_selection", request_data)

@bridge_handler("/set_valuelist_selection")
def handle_set_valuelist_selection(data):
    """Bridge handler for setting ValueList selection"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino

        file_name = data.get('file_name', '')
        valuelist_name = data.get('valuelist_name', '')
        selection = data.get('selection', '')

        # Ensure the correct file is active first
        activation_result = ensure_file_is_active(file_name)
        if not activation_result.get("success", False):
            return {
                "success": False,
                "error": activation_result.get("error", "Failed to activate file"),
                "file_name": file_name,
                "valuelist_name": valuelist_name,
                "selection": selection
            }

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "file_name": file_name,
                "valuelist_name": valuelist_name,
                "selection": selection
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "file_name": file_name,
                "valuelist_name": valuelist_name,
                "selection": selection
            }
        
        # Find the ValueList component
        valuelist_found = False
        old_selection = None
        new_selection_index = None
        new_selection_name = None
        new_selection_value = None
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_ValueList):
                if (obj.NickName or "Unnamed") == valuelist_name:
                    valuelist_found = True
                    old_selection = {
                        "index": obj.SelectionIndex,
                        "name": obj.ListItems[obj.SelectionIndex].Name if obj.SelectionIndex < len(obj.ListItems) else None,
                        "value": str(obj.ListItems[obj.SelectionIndex].Value) if obj.SelectionIndex < len(obj.ListItems) else None
                    }
                    
                    # Try to find the selection by name or index
                    selection_found = False
                    
                    # Try as index first
                    try:
                        index = int(selection)
                        if 0 <= index < len(obj.ListItems):
                            obj.SelectItem(index)
                            new_selection_index = index
                            new_selection_name = obj.ListItems[index].Name
                            new_selection_value = str(obj.ListItems[index].Value)
                            selection_found = True
                    except ValueError:
                        # Not an integer, try as name or value
                        for i, item in enumerate(obj.ListItems):
                            if item.Name == selection or str(item.Value) == selection:
                                obj.SelectItem(i)
                                new_selection_index = i
                                new_selection_name = item.Name
                                new_selection_value = str(item.Value)
                                selection_found = True
                                break
                    
                    if not selection_found:
                        available_options = [f"{i}: {item.Name} ({item.Value})" for i, item in enumerate(obj.ListItems)]
                        return {
                            "success": False,
                            "error": f"Selection '{selection}' not found in ValueList '{valuelist_name}'",
                            "available_options": available_options,
                            "valuelist_name": valuelist_name,
                            "selection": selection
                        }
                    
                    # Trigger solution recompute
                    gh_doc.NewSolution(True)
                    break
        
        if not valuelist_found:
            return {
                "success": False,
                "error": f"ValueList '{valuelist_name}' not found",
                "valuelist_name": valuelist_name,
                "selection": selection
            }
        
        return {
            "success": True,
            "valuelist_name": valuelist_name,
            "old_selection": old_selection,
            "new_selection": {
                "index": new_selection_index,
                "name": new_selection_name,
                "value": new_selection_value
            },
            "message": f"ValueList '{valuelist_name}' updated to '{new_selection_name}'"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "valuelist_name": data.get('valuelist_name', ''),
            "selection": data.get('selection', '')
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error setting ValueList selection: {str(e)}",
            "traceback": traceback.format_exc(),
            "valuelist_name": data.get('valuelist_name', ''),
            "selection": data.get('selection', '')
        }

@gh_tool(
    name="list_grasshopper_panels",
    description=(
        "List all Panel components in the current Grasshopper definition. "
        "Panel components display text data and can be used for both input and output. "
        "This tool returns their names and current text content.\n\n"
        "**Returns:**\n"
        "Dictionary containing list of Panel components with their text content."
    )
)
async def list_grasshopper_panels() -> Dict[str, Any]:
    """
    List all Panel components in the current Grasshopper definition via HTTP bridge.
    
    Returns:
        Dict containing Panel information
    """
    
    return call_bridge_api("/list_panels", {})

@bridge_handler("/list_panels")
def handle_list_panels(data):
    """Bridge handler for listing Panel components"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "panels": []
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "panels": []
            }
        
        panels = []
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                panel_info = {
                    "name": obj.NickName or "Unnamed",
                    "user_text": obj.UserText if hasattr(obj, 'UserText') else "",
                    "position": {"x": float(obj.Attributes.Pivot.X), "y": float(obj.Attributes.Pivot.Y)},
                    "volatile_data": []
                }
                
                # Try to extract volatile data (computed values)
                try:
                    if hasattr(obj, 'VolatileData') and obj.VolatileData:
                        vd = obj.VolatileData
                        # Try multiple ways to access the data
                        for path in vd.Paths:
                            branch = vd.get_Branch(path)
                            if branch:
                                for i in range(branch.Count):
                                    try:
                                        item = branch[i]
                                        if item is not None:
                                            # Try to get the actual value
                                            if hasattr(item, 'Value'):
                                                panel_info["volatile_data"].append(str(item.Value))
                                            else:
                                                panel_info["volatile_data"].append(str(item))
                                    except Exception:
                                        continue
                    
                    # Also try to get values from input parameters if panel is displaying input data
                    if hasattr(obj, 'Params') and obj.Params.Input and obj.Params.Input.Count > 0:
                        for i in range(obj.Params.Input.Count):
                            input_param = obj.Params.Input[i]
                            if hasattr(input_param, 'VolatileData') and input_param.VolatileData:
                                input_vd = input_param.VolatileData
                                for path in input_vd.Paths:
                                    branch = input_vd.get_Branch(path)
                                    if branch:
                                        for j in range(branch.Count):
                                            try:
                                                item = branch[j]
                                                if item is not None:
                                                    if hasattr(item, 'Value'):
                                                        panel_info["volatile_data"].append(str(item.Value))
                                                    else:
                                                        panel_info["volatile_data"].append(str(item))
                                            except Exception:
                                                continue
                                
                except Exception as e:
                    panel_info["volatile_data_error"] = f"Error extracting data: {str(e)}"
                
                panels.append(panel_info)
        
        return {
            "success": True,
            "panels": panels,
            "count": len(panels),
            "message": f"Found {len(panels)} Panel components"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "panels": []
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error listing Panel components: {str(e)}",
            "traceback": traceback.format_exc(),
            "panels": []
        }

@gh_tool(
    name="set_grasshopper_panel_text",
    description=(
        "Change the text content of a Grasshopper Panel component in a specific file. "
        "This tool will activate the specified file (making it visible to the user), "
        "then find the Panel component and update its text. "
        "Use 'get_active_gh_files' to see open files and 'list_grasshopper_panels' to see available Panels.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, required): Name of the .gh file containing the Panel (e.g., 'Primary Truss Generator.gh')\n"
        "- **panel_name** (str): The name/nickname of the Panel component to modify\n"
        "- **new_text** (str): The new text content to set for the panel\n"
        "\n**Returns:**\n"
        "Dictionary containing the operation status and updated Panel information."
    )
)
async def set_grasshopper_panel_text(file_name: str, panel_name: str, new_text: str) -> Dict[str, Any]:
    """
    Set the text content of a Grasshopper Panel component via HTTP bridge.

    Args:
        file_name: Name of the .gh file containing the Panel
        panel_name: Name of the Panel component
        new_text: New text content to set

    Returns:
        Dict containing operation results
    """

    request_data = {
        "file_name": file_name,
        "panel_name": panel_name,
        "new_text": new_text
    }

    return call_bridge_api("/set_panel_text", request_data)

@bridge_handler("/set_panel_text")
def handle_set_panel_text(data):
    """Bridge handler for setting Panel text"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino

        file_name = data.get('file_name', '')
        panel_name = data.get('panel_name', '')
        new_text = str(data.get('new_text', ''))

        # Ensure the correct file is active first
        activation_result = ensure_file_is_active(file_name)
        if not activation_result.get("success", False):
            return {
                "success": False,
                "error": activation_result.get("error", "Failed to activate file"),
                "file_name": file_name,
                "panel_name": panel_name,
                "new_text": new_text
            }

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "file_name": file_name,
                "panel_name": panel_name,
                "new_text": new_text
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "file_name": file_name,
                "panel_name": panel_name,
                "new_text": new_text
            }
        
        # Find the Panel component
        panel_found = False
        old_text = None
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                if (obj.NickName or "Unnamed") == panel_name:
                    panel_found = True
                    old_text = obj.UserText if hasattr(obj, 'UserText') else ""
                    
                    # Set the new text
                    obj.UserText = new_text
                    obj.ExpireSolution(True)
                    
                    # Trigger solution recompute
                    gh_doc.NewSolution(True)
                    break
        
        if not panel_found:
            return {
                "success": False,
                "error": f"Panel '{panel_name}' not found",
                "panel_name": panel_name,
                "new_text": new_text
            }
        
        return {
            "success": True,
            "panel_name": panel_name,
            "old_text": old_text,
            "new_text": new_text,
            "message": f"Panel '{panel_name}' text updated"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "panel_name": data.get('panel_name', ''),
            "new_text": data.get('new_text', '')
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error setting Panel text: {str(e)}",
            "traceback": traceback.format_exc(),
            "panel_name": data.get('panel_name', ''),
            "new_text": data.get('new_text', '')
        }

@gh_tool(
    name="get_grasshopper_panel_data",
    description=(
        "Extract data values from Grasshopper Panel components. "
        "This tool can extract computed values, text content, and other data from panels. "
        "Useful for reading output values like truss weight, calculations, or any data displayed in panels.\n\n"
        "**Parameters:**\n"
        "- **panel_name** (str, optional): Name of a specific panel to read, or leave empty to read all panels\n"
        "\n**Returns:**\n"
        "Dictionary containing panel data including text content and computed values."
    )
)
async def get_grasshopper_panel_data(panel_name: str = "") -> Dict[str, Any]:
    """
    Get data from Grasshopper Panel components via HTTP bridge.
    
    Args:
        panel_name: Name of specific panel to read (optional, reads all if empty)
        
    Returns:
        Dict containing panel data
    """
    
    request_data = {"panel_name": panel_name}
    
    return call_bridge_api("/get_panel_data", request_data)

@bridge_handler("/get_panel_data")
def handle_get_panel_data(data):
    """Bridge handler for getting Panel data"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        
        panel_name = data.get('panel_name', '')
        
        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }
        
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }
        
        panel_data = []
        
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_Panel):
                current_panel_name = obj.NickName or "Unnamed"
                
                # If specific panel requested, skip others
                if panel_name and current_panel_name != panel_name:
                    continue
                
                panel_info = {
                    "name": current_panel_name,
                    "user_text": obj.UserText if hasattr(obj, 'UserText') else "",
                    "volatile_data_text": "",
                    "volatile_data_list": [],
                    "position": {"x": float(obj.Attributes.Pivot.X), "y": float(obj.Attributes.Pivot.Y)},
                    "computed_values": [],
                    "display_text": ""
                }
                
                # Extract volatile data (computed values)
                try:
                    all_values = []
                    
                    if hasattr(obj, 'VolatileData') and obj.VolatileData:
                        vd = obj.VolatileData
                        
                        for path in vd.Paths:
                            branch = vd.get_Branch(path)
                            if branch:
                                for i in range(branch.Count):
                                    try:
                                        item = branch[i]
                                        if item is not None:
                                            # Try to get the actual value
                                            if hasattr(item, 'Value'):
                                                item_str = str(item.Value).replace('"', "'")
                                                all_values.append(item_str)
                                            else:
                                                item_str = str(item).replace('"', "'")
                                                all_values.append(item_str)
                                    except Exception:
                                        continue
                    
                    # Also try to get values from input parameters if panel is displaying input data
                    if hasattr(obj, 'Params') and obj.Params.Input and obj.Params.Input.Count > 0:
                        for i in range(obj.Params.Input.Count):
                            input_param = obj.Params.Input[i]
                            if hasattr(input_param, 'VolatileData') and input_param.VolatileData:
                                input_vd = input_param.VolatileData
                                for path in input_vd.Paths:
                                    branch = input_vd.get_Branch(path)
                                    if branch:
                                        for j in range(branch.Count):
                                            try:
                                                item = branch[j]
                                                if item is not None:
                                                    if hasattr(item, 'Value'):
                                                        item_str = str(item.Value).replace('"', "'")
                                                        all_values.append(item_str)
                                                    else:
                                                        item_str = str(item).replace('"', "'")
                                                        all_values.append(item_str)
                                            except Exception:
                                                continue
                    
                    panel_info["volatile_data_list"] = all_values
                    panel_info["volatile_data_text"] = ','.join(all_values) if all_values else ""
                    panel_info["computed_values"] = all_values
                    
                    # Try to extract display text from the panel itself
                    try:
                        if hasattr(obj, 'ToString'):
                            panel_info["display_text"] = str(obj.ToString())
                    except:
                        pass
                        
                    # Try alternative methods to get the actual displayed content
                    try:
                        if hasattr(obj, 'Properties'):
                            if hasattr(obj.Properties, 'Text'):
                                panel_info["display_text"] = str(obj.Properties.Text)
                    except:
                        pass
                        
                    # Try to get text from the panel's visual representation
                    try:
                        if hasattr(obj, 'GetValue'):
                            value = obj.GetValue(0, 0)  # Try to get first value
                            if value is not None:
                                panel_info["display_text"] = str(value)
                    except:
                        pass
                        
                except Exception as e:
                    panel_info["volatile_data_error"] = f"Could not extract volatile data: {str(e)}"
                
                panel_data.append(panel_info)
        
        if panel_name and not panel_data:
            return {
                "success": False,
                "error": f"Panel '{panel_name}' not found"
            }
        
        return {
            "success": True,
            "panel_data": panel_data,
            "count": len(panel_data),
            "message": f"Retrieved data from {len(panel_data)} panel(s)"
        }
        
    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error getting Panel data: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="analyze_grasshopper_inputs_with_context",
    description=(
        "Analyze all inputs in a specific Grasshopper file including sliders, geometry parameters, "
        "and other input components. This tool will activate the specified file (making it visible to the user), "
        "then analyze it to provide comprehensive context by analyzing group names, "
        "nearby scribble text annotations, and component positions to help understand the purpose "
        "of each input even when component names aren't properly set.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, required): Name of the .gh file to analyze (e.g., 'Primary Truss Generator.gh')\n"
        "\n**Returns:**\n"
        "Dictionary containing:\n"
        "- Sliders with their group context and nearby annotations\n"
        "- Geometry input parameters (curves, surfaces, points) with context\n"
        "- All inputs organized by their inferred purpose and location"
    )
)
async def analyze_grasshopper_inputs_with_context(file_name: str) -> Dict[str, Any]:
    """
    Analyze all Grasshopper inputs with full context including groups and annotations.

    Args:
        file_name: Name of the .gh file to analyze

    Returns:
        Dict containing comprehensive input analysis with context
    """

    request_data = {
        "file_name": file_name
    }

    return call_bridge_api("/analyze_inputs_context", request_data)

@bridge_handler("/analyze_inputs_context")
def handle_analyze_inputs_context(data):
    """Bridge handler for analyzing inputs with context"""
    import traceback
    debug_log = []

    try:
        debug_log.append("Starting analyze_inputs_context handler")

        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import System

        debug_log.append("Imports successful")

        file_name = data.get('file_name', '')

        # Ensure the correct file is active first
        activation_result = ensure_file_is_active(file_name)
        if not activation_result.get("success", False):
            debug_log.append(f"Failed to activate file: {activation_result.get('error', 'Unknown error')}")
            return {
                "success": False,
                "error": activation_result.get("error", "Failed to activate file"),
                "file_name": file_name,
                "debug_log": debug_log
            }

        debug_log.append(f"File activated: {file_name}")

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            debug_log.append("Grasshopper plugin not available")
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "file_name": file_name,
                "debug_log": debug_log
            }

        debug_log.append("Grasshopper plugin found")

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            debug_log.append("No active Grasshopper document found")
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "file_name": file_name,
                "debug_log": debug_log
            }

        debug_log.append(f"Found Grasshopper document with {gh_doc.ObjectCount} objects")

        # Build a map of groups and their contained objects
        groups_map = {}
        debug_log.append("Building groups map")

        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_Group):
                # Get bounds - GH_Group uses Attributes.Bounds not obj.Bounds
                bounds_rect = obj.Attributes.Bounds if hasattr(obj.Attributes, 'Bounds') else None

                if bounds_rect:
                    group_info = {
                        "name": obj.NickName or "Unnamed Group",
                        "color": str(obj.Colour) if hasattr(obj, 'Colour') else "Unknown",
                        "bounds": {
                            "left": float(bounds_rect.Left),
                            "right": float(bounds_rect.Right),
                            "top": float(bounds_rect.Top),
                            "bottom": float(bounds_rect.Bottom)
                        },
                        "members": []
                    }
                    groups_map[str(obj.InstanceGuid)] = group_info

        debug_log.append(f"Found {len(groups_map)} groups")

        # Map components to their groups and find nearby scribbles
        component_group_map = {}
        scribbles = []
        debug_log.append("Mapping components to groups and finding scribbles")

        for obj in gh_doc.Objects:
            try:
                obj_guid = str(obj.InstanceGuid)

                # Convert bounds to JSON-serializable format
                bounds_data = None
                if hasattr(obj.Attributes, 'Bounds'):
                    bounds_rect = obj.Attributes.Bounds
                    bounds_data = {
                        "left": float(bounds_rect.Left),
                        "right": float(bounds_rect.Right),
                        "top": float(bounds_rect.Top),
                        "bottom": float(bounds_rect.Bottom),
                        "width": float(bounds_rect.Width),
                        "height": float(bounds_rect.Height)
                    }

                obj_bounds = {
                    "x": float(obj.Attributes.Pivot.X),
                    "y": float(obj.Attributes.Pivot.Y),
                    "bounds": bounds_data
                }

                # Check if object is in any group
                for group_guid, group_info in groups_map.items():
                    bounds = group_info["bounds"]
                    if (bounds["left"] <= obj_bounds["x"] <= bounds["right"] and
                        bounds["top"] <= obj_bounds["y"] <= bounds["bottom"]):
                        component_group_map[obj_guid] = group_info["name"]
                        group_info["members"].append(obj.NickName or type(obj).__name__)
                        break

                # Collect scribble text annotations
                if isinstance(obj, Grasshopper.Kernel.Special.GH_Scribble):
                    scribble_text = ""
                    if hasattr(obj, 'Text'):
                        scribble_text = obj.Text
                    elif hasattr(obj, 'RichText'):
                        scribble_text = obj.RichText

                    scribbles.append({
                        "text": scribble_text,
                        "position": obj_bounds,
                        "guid": obj_guid
                    })
            except Exception as obj_error:
                debug_log.append(f"Error processing object {obj.NickName if hasattr(obj, 'NickName') else 'unknown'}: {str(obj_error)}")
                continue

        debug_log.append(f"Found {len(scribbles)} scribbles, mapped {len(component_group_map)} components to groups")

        # Helper function to find nearby scribbles
        def find_nearby_annotations(obj_position, max_distance=150):
            nearby = []
            for scribble in scribbles:
                dx = abs(scribble["position"]["x"] - obj_position["x"])
                dy = abs(scribble["position"]["y"] - obj_position["y"])
                distance = (dx*dx + dy*dy) ** 0.5
                if distance < max_distance:
                    nearby.append({
                        "text": scribble["text"],
                        "distance": distance
                    })
            # Sort by distance
            nearby.sort(key=lambda x: x["distance"])
            return nearby

        # Analyze sliders with context
        sliders_with_context = []
        debug_log.append("Analyzing sliders with context")

        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_NumberSlider):
                try:
                    obj_guid = str(obj.InstanceGuid)
                    position = {"x": float(obj.Attributes.Pivot.X), "y": float(obj.Attributes.Pivot.Y)}

                    slider_info = {
                        "name": obj.NickName or "Unnamed",
                        "current_value": float(str(obj.Slider.Value)),
                        "min_value": float(str(obj.Slider.Minimum)),
                        "max_value": float(str(obj.Slider.Maximum)),
                        "precision": obj.Slider.DecimalPlaces,
                        "type": obj.Slider.Type.ToString(),
                        "position": position,
                        "group_name": component_group_map.get(obj_guid, None),
                        "nearby_annotations": find_nearby_annotations(position),
                        "inferred_purpose": "Unknown"
                    }

                    # Enhanced purpose inference using group name and annotations
                    all_context_text = (slider_info["name"] + " " +
                                       (slider_info["group_name"] or "") + " " +
                                       " ".join([ann["text"] for ann in slider_info["nearby_annotations"]])).lower()

                    if any(kw in all_context_text for kw in ["length", "distance", "span"]):
                        slider_info["inferred_purpose"] = "Length/Distance control"
                    elif any(kw in all_context_text for kw in ["width", "wide"]):
                        slider_info["inferred_purpose"] = "Width control"
                    elif any(kw in all_context_text for kw in ["height", "tall", "depth"]):
                        slider_info["inferred_purpose"] = "Height/Depth control"
                    elif any(kw in all_context_text for kw in ["count", "number", "quantity", "num"]):
                        slider_info["inferred_purpose"] = "Count/Quantity control"
                    elif any(kw in all_context_text for kw in ["angle", "rotation", "rotate"]):
                        slider_info["inferred_purpose"] = "Angle/Rotation control"
                    elif any(kw in all_context_text for kw in ["factor", "ratio", "proportion"]):
                        slider_info["inferred_purpose"] = "Factor/Ratio control"
                    elif any(kw in all_context_text for kw in ["truss", "structural", "beam"]):
                        slider_info["inferred_purpose"] = "Structural parameter"
                    elif slider_info["group_name"]:
                        slider_info["inferred_purpose"] = f"Parameter for {slider_info['group_name']}"

                    sliders_with_context.append(slider_info)
                except Exception as slider_error:
                    debug_log.append(f"Error processing slider {obj.NickName if hasattr(obj, 'NickName') else 'unknown'}: {str(slider_error)}")
                    continue

        debug_log.append(f"Found {len(sliders_with_context)} sliders with context")

        # Analyze geometry input parameters with context
        geometry_inputs = []
        debug_log.append("Analyzing geometry input parameters with context")

        geometry_param_types = [
            "Grasshopper.Kernel.Parameters.Param_Curve",
            "Grasshopper.Kernel.Parameters.Param_Surface",
            "Grasshopper.Kernel.Parameters.Param_Brep",
            "Grasshopper.Kernel.Parameters.Param_Geometry",
            "Grasshopper.Kernel.Parameters.Param_Line",
            "Grasshopper.Kernel.Parameters.Param_Circle",
            "Grasshopper.Kernel.Parameters.Param_Arc",
            "Grasshopper.Kernel.Parameters.Param_Point"
        ]

        for obj in gh_doc.Objects:
            try:
                obj_type = type(obj).__module__ + "." + type(obj).__name__

                # Check if it's a geometry parameter type
                is_geometry_param = any(geom_type in obj_type for geom_type in geometry_param_types)

                # Also check for parameter containers
                if not is_geometry_param and hasattr(obj, 'SourceCount'):
                    is_geometry_param = (obj.SourceCount == 0 and  # No input connections
                                        hasattr(obj, 'Recipients') and obj.Recipients.Count > 0)  # Has outputs

                if is_geometry_param:
                    obj_guid = str(obj.InstanceGuid)
                    position = {"x": float(obj.Attributes.Pivot.X), "y": float(obj.Attributes.Pivot.Y)}

                    # Check if it's truly an input (no sources, has recipients)
                    has_sources = hasattr(obj, 'SourceCount') and obj.SourceCount > 0
                    has_recipients = hasattr(obj, 'Recipients') and obj.Recipients.Count > 0

                    if not has_sources and has_recipients:
                        geom_info = {
                            "name": obj.NickName or "Unnamed",
                            "type": type(obj).__name__,
                            "full_type": obj_type,
                            "position": position,
                            "group_name": component_group_map.get(obj_guid, None),
                            "nearby_annotations": find_nearby_annotations(position),
                            "description": obj.Description if hasattr(obj, 'Description') else "",
                            "has_data": False,
                            "data_count": 0
                        }

                        # Check if it has data
                        if hasattr(obj, 'VolatileDataCount'):
                            geom_info["has_data"] = obj.VolatileDataCount > 0
                            geom_info["data_count"] = obj.VolatileDataCount

                        # Infer purpose from context
                        all_context_text = (geom_info["name"] + " " +
                                           (geom_info["group_name"] or "") + " " +
                                           " ".join([ann["text"] for ann in geom_info["nearby_annotations"]])).lower()

                        if "curve" in obj_type.lower() or "curve" in all_context_text:
                            geom_info["inferred_purpose"] = "Curve input"
                        elif "surface" in obj_type.lower() or "surface" in all_context_text:
                            geom_info["inferred_purpose"] = "Surface input"
                        elif "point" in obj_type.lower() or "point" in all_context_text:
                            geom_info["inferred_purpose"] = "Point input"
                        elif "line" in obj_type.lower() or "line" in all_context_text:
                            geom_info["inferred_purpose"] = "Line input"
                        else:
                            geom_info["inferred_purpose"] = "Geometry input"

                        geometry_inputs.append(geom_info)
            except Exception as geom_error:
                debug_log.append(f"Error processing geometry object: {str(geom_error)}")
                continue

        debug_log.append(f"Found {len(geometry_inputs)} geometry inputs with context")

        debug_log.append("Successfully completed analysis")

        return {
            "success": True,
            "sliders": sliders_with_context,
            "geometry_inputs": geometry_inputs,
            "groups": list(groups_map.values()),
            "annotations": scribbles,
            "summary": f"Found {len(sliders_with_context)} sliders and {len(geometry_inputs)} geometry inputs with contextual information",
            "debug_log": debug_log
        }

    except ImportError as e:
        debug_log.append(f"ImportError: {str(e)}")
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}",
            "debug_log": debug_log
        }
    except Exception as e:
        debug_log.append(f"Exception in main handler: {str(e)}")
        return {
            "success": False,
            "error": f"Error analyzing inputs: {str(e)}",
            "traceback": traceback.format_exc(),
            "debug_log": debug_log
        }

@gh_tool(
    name="analyze_grasshopper_outputs_with_context",
    description=(
        "Analyze all output components in the Grasshopper definition including geometry outputs "
        "(curves, surfaces, meshes, etc.). This provides comprehensive context by analyzing "
        "group names, nearby scribble text annotations, and component positions to help understand "
        "what each output represents. Outputs are typically parameter components at the end of the "
        "definition that receive data but don't send it to other components.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, optional): Name of specific .gh file to analyze (e.g., 'Primary Truss Generator.gh'). If not provided, analyzes the currently active document.\n"
        "\n**Returns:**\n"
        "Dictionary containing:\n"
        "- Geometry output parameters with their group context and annotations\n"
        "- Output data organized by type (curves, surfaces, points, etc.)\n"
        "- Inferred purpose of each output based on context"
    )
)
async def analyze_grasshopper_outputs_with_context(file_name: str = None) -> Dict[str, Any]:
    """
    Analyze all Grasshopper outputs with full context including groups and annotations.

    Args:
        file_name: Optional name of specific .gh file to analyze

    Returns:
        Dict containing comprehensive output analysis with context
    """
    request_data = {
        "file_name": file_name
    }

    return call_bridge_api("/analyze_outputs_context", request_data)

@bridge_handler("/analyze_outputs_context")
def handle_analyze_outputs_context(data):
    """Bridge handler for analyzing outputs with context"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        import Grasshopper
        import Rhino
        import os

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available"
            }

        # Get the document - either specified by name or use active
        file_name = data.get('file_name', None)
        gh_doc = None

        if file_name:
            # Find the specified document in DocumentServer
            doc_server = Grasshopper.Instances.DocumentServer
            if doc_server:
                for doc in doc_server:
                    if doc and hasattr(doc, 'FilePath') and doc.FilePath:
                        current_file_name = os.path.basename(str(doc.FilePath))
                        if current_file_name.lower() == file_name.lower():
                            gh_doc = doc
                            break

            if not gh_doc:
                return {
                    "success": False,
                    "error": f"Document '{file_name}' not found in open documents. Use get_active_gh_files to see what's open."
                }
        else:
            # Use active document if no file_name specified
            gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
            if not gh_doc:
                return {
                    "success": False,
                    "error": "No active Grasshopper document found"
                }

        # Build groups map and scribbles (reuse logic from inputs analysis)
        groups_map = {}
        for obj in gh_doc.Objects:
            if isinstance(obj, Grasshopper.Kernel.Special.GH_Group):
                # Get bounds - GH_Group uses Attributes.Bounds not obj.Bounds
                bounds_rect = obj.Attributes.Bounds if hasattr(obj.Attributes, 'Bounds') else None

                if bounds_rect:
                    group_info = {
                        "name": obj.NickName or "Unnamed Group",
                        "bounds": {
                            "left": float(bounds_rect.Left),
                            "right": float(bounds_rect.Right),
                            "top": float(bounds_rect.Top),
                            "bottom": float(bounds_rect.Bottom)
                        }
                    }
                    groups_map[str(obj.InstanceGuid)] = group_info

        component_group_map = {}
        scribbles = []

        for obj in gh_doc.Objects:
            obj_guid = str(obj.InstanceGuid)
            obj_bounds = {
                "x": float(obj.Attributes.Pivot.X),
                "y": float(obj.Attributes.Pivot.Y)
            }

            # Map to groups
            for group_guid, group_info in groups_map.items():
                bounds = group_info["bounds"]
                if (bounds["left"] <= obj_bounds["x"] <= bounds["right"] and
                    bounds["top"] <= obj_bounds["y"] <= bounds["bottom"]):
                    component_group_map[obj_guid] = group_info["name"]
                    break

            # Collect scribbles
            if isinstance(obj, Grasshopper.Kernel.Special.GH_Scribble):
                scribble_text = ""
                if hasattr(obj, 'Text'):
                    scribble_text = obj.Text
                elif hasattr(obj, 'RichText'):
                    scribble_text = obj.RichText

                scribbles.append({
                    "text": scribble_text,
                    "position": obj_bounds,
                    "guid": obj_guid
                })

        def find_nearby_annotations(obj_position, max_distance=150):
            nearby = []
            for scribble in scribbles:
                dx = abs(scribble["position"]["x"] - obj_position["x"])
                dy = abs(scribble["position"]["y"] - obj_position["y"])
                distance = (dx*dx + dy*dy) ** 0.5
                if distance < max_distance:
                    nearby.append({
                        "text": scribble["text"],
                        "distance": distance
                    })
            nearby.sort(key=lambda x: x["distance"])
            return nearby

        # Analyze geometry output parameters
        geometry_outputs = []
        geometry_param_types = [
            "Grasshopper.Kernel.Parameters.Param_Curve",
            "Grasshopper.Kernel.Parameters.Param_Surface",
            "Grasshopper.Kernel.Parameters.Param_Brep",
            "Grasshopper.Kernel.Parameters.Param_Geometry",
            "Grasshopper.Kernel.Parameters.Param_Line",
            "Grasshopper.Kernel.Parameters.Param_Circle",
            "Grasshopper.Kernel.Parameters.Param_Arc",
            "Grasshopper.Kernel.Parameters.Param_Point",
            "Grasshopper.Kernel.Parameters.Param_Mesh"
        ]

        for obj in gh_doc.Objects:
            obj_type = type(obj).__module__ + "." + type(obj).__name__

            # Check if it's a geometry parameter type
            is_geometry_param = any(geom_type in obj_type for geom_type in geometry_param_types)

            if is_geometry_param or hasattr(obj, 'SourceCount'):
                obj_guid = str(obj.InstanceGuid)
                position = {"x": float(obj.Attributes.Pivot.X), "y": float(obj.Attributes.Pivot.Y)}

                # Check if it's truly an output (has sources, no/few recipients)
                has_sources = hasattr(obj, 'SourceCount') and obj.SourceCount > 0
                has_recipients = hasattr(obj, 'Recipients') and obj.Recipients.Count > 0

                # Output criteria: has input data but doesn't feed other components (or very few)
                if has_sources and not has_recipients:
                    geom_info = {
                        "name": obj.NickName or "Unnamed",
                        "type": type(obj).__name__,
                        "full_type": obj_type,
                        "position": position,
                        "group_name": component_group_map.get(obj_guid, None),
                        "nearby_annotations": find_nearby_annotations(position),
                        "description": obj.Description if hasattr(obj, 'Description') else "",
                        "has_data": False,
                        "data_count": 0,
                        "data_type": "Unknown"
                    }

                    # Check if it has data
                    if hasattr(obj, 'VolatileDataCount'):
                        geom_info["has_data"] = obj.VolatileDataCount > 0
                        geom_info["data_count"] = obj.VolatileDataCount

                    # Determine data type
                    if "Curve" in obj_type:
                        geom_info["data_type"] = "Curves"
                    elif "Surface" in obj_type or "Brep" in obj_type:
                        geom_info["data_type"] = "Surfaces/BReps"
                    elif "Point" in obj_type:
                        geom_info["data_type"] = "Points"
                    elif "Line" in obj_type:
                        geom_info["data_type"] = "Lines"
                    elif "Mesh" in obj_type:
                        geom_info["data_type"] = "Meshes"
                    else:
                        geom_info["data_type"] = "Geometry"

                    # Infer purpose from context
                    all_context_text = (geom_info["name"] + " " +
                                       (geom_info["group_name"] or "") + " " +
                                       " ".join([ann["text"] for ann in geom_info["nearby_annotations"]])).lower()

                    if any(kw in all_context_text for kw in ["truss", "beam", "member", "element"]):
                        geom_info["inferred_purpose"] = "Structural elements output"
                    elif any(kw in all_context_text for kw in ["upper", "top", "chord"]):
                        geom_info["inferred_purpose"] = "Upper/top elements output"
                    elif any(kw in all_context_text for kw in ["lower", "bottom"]):
                        geom_info["inferred_purpose"] = "Lower/bottom elements output"
                    elif any(kw in all_context_text for kw in ["vertical", "vert"]):
                        geom_info["inferred_purpose"] = "Vertical elements output"
                    elif any(kw in all_context_text for kw in ["diagonal", "diag", "brace"]):
                        geom_info["inferred_purpose"] = "Diagonal/bracing elements output"
                    elif geom_info["group_name"]:
                        geom_info["inferred_purpose"] = f"{geom_info['group_name']} output"
                    else:
                        geom_info["inferred_purpose"] = f"{geom_info['data_type']} output"

                    geometry_outputs.append(geom_info)

        # Organize outputs by type
        outputs_by_type = {}
        for output in geometry_outputs:
            data_type = output["data_type"]
            if data_type not in outputs_by_type:
                outputs_by_type[data_type] = []
            outputs_by_type[data_type].append(output["name"])

        return {
            "success": True,
            "geometry_outputs": geometry_outputs,
            "outputs_by_type": outputs_by_type,
            "total_outputs": len(geometry_outputs),
            "summary": f"Found {len(geometry_outputs)} geometry outputs with contextual information"
        }

    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error analyzing outputs: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="set_grasshopper_geometry_input",
    description=(
        "Set geometry from Rhino to a Grasshopper parameter component in a specific file. "
        "This tool will activate the specified file (making it visible to the user), "
        "then take Rhino object IDs and assign them to the specified Grasshopper geometry parameter. "
        "Use this to feed curves, surfaces, or other geometry from Rhino into Grasshopper.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, required): Name of the .gh file to work with (e.g., 'Primary Truss Generator.gh')\n"
        "- **parameter_name** (str): Name of the Grasshopper parameter component to set\n"
        "- **rhino_object_ids** (list): List of Rhino object GUIDs/IDs to reference\n"
        "\n**Returns:**\n"
        "Dictionary containing operation status and parameter information."
    )
)
async def set_grasshopper_geometry_input(file_name: str, parameter_name: str, rhino_object_ids: list) -> Dict[str, Any]:
    """
    Set geometry from Rhino to a Grasshopper parameter via HTTP bridge.

    Args:
        file_name: Name of the .gh file to work with
        parameter_name: Name of the parameter component
        rhino_object_ids: List of Rhino object IDs

    Returns:
        Dict containing operation results
    """

    request_data = {
        "file_name": file_name,
        "parameter_name": parameter_name,
        "rhino_object_ids": rhino_object_ids
    }

    return call_bridge_api("/set_geometry_input", request_data)

@bridge_handler("/set_geometry_input")
def handle_set_geometry_input(data):
    """Bridge handler for setting geometry input"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        clr.AddReference('RhinoCommon')
        import Grasshopper
        import Rhino
        import System
        import scriptcontext as sc
        import os

        file_name = data.get('file_name', '')
        parameter_name = data.get('parameter_name', '')
        rhino_object_ids = data.get('rhino_object_ids', [])

        if not parameter_name:
            return {
                "success": False,
                "error": "No parameter_name provided",
                "file_name": file_name
            }

        if not rhino_object_ids:
            return {
                "success": False,
                "error": "No rhino_object_ids provided",
                "file_name": file_name
            }

        # Ensure the correct file is active first
        activation_result = ensure_file_is_active(file_name)
        if not activation_result.get("success", False):
            return {
                "success": False,
                "error": activation_result.get("error", "Failed to activate file"),
                "file_name": file_name,
                "parameter_name": parameter_name
            }

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "file_name": file_name
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "file_name": file_name
            }

        # Find the parameter component - try multiple approaches
        param_found = False
        target_param = None

        # First, try exact name match
        for obj in gh_doc.Objects:
            obj_name = obj.NickName if obj.NickName else (obj.Name if hasattr(obj, 'Name') else "Unnamed")
            if obj_name == parameter_name:
                # Check if it's a parameter - be more flexible
                obj_type_name = type(obj).__name__
                is_param = ("Param" in obj_type_name or
                           (hasattr(obj, 'Category') and obj.Category == "Params") or
                           hasattr(obj, 'PersistentData'))

                if is_param:
                    target_param = obj
                    param_found = True
                    break

        # If not found, try case-insensitive partial match
        if not param_found:
            for obj in gh_doc.Objects:
                obj_name = obj.NickName if obj.NickName else (obj.Name if hasattr(obj, 'Name') else "Unnamed")
                if parameter_name.lower() in obj_name.lower() or obj_name.lower() in parameter_name.lower():
                    obj_type_name = type(obj).__name__
                    is_param = ("Param" in obj_type_name or
                               (hasattr(obj, 'Category') and obj.Category == "Params") or
                               hasattr(obj, 'PersistentData'))

                    if is_param:
                        target_param = obj
                        param_found = True
                        break

        if not param_found:
            # List available geometry parameters to help user
            available_params = []
            for obj in gh_doc.Objects:
                obj_type_name = type(obj).__name__
                if "Param" in obj_type_name and ("Curve" in obj_type_name or "Geometry" in obj_type_name or "Surface" in obj_type_name):
                    obj_name = obj.NickName if obj.NickName else (obj.Name if hasattr(obj, 'Name') else "Unnamed")
                    has_sources = hasattr(obj, 'SourceCount') and obj.SourceCount > 0
                    if not has_sources:  # Only show input parameters
                        available_params.append(obj_name)

            return {
                "success": False,
                "error": f"Parameter '{parameter_name}' not found",
                "available_geometry_parameters": available_params[:10],  # Show first 10
                "suggestion": "Try one of the available parameter names listed above"
            }

        # Clear existing data first to replace (not append)
        cleared_info = []
        try:
            if hasattr(target_param, 'ClearData'):
                target_param.ClearData()
                cleared_info.append("ClearData()")

            # Also clear persistent data to ensure complete replacement
            if hasattr(target_param, 'PersistentData') and target_param.PersistentData is not None:
                old_count = target_param.PersistentData.DataCount if hasattr(target_param.PersistentData, 'DataCount') else 0
                target_param.PersistentData.Clear()
                cleared_info.append(f"PersistentData.Clear() - removed {old_count} items")

            # Clear volatile data if present
            if hasattr(target_param, 'VolatileData') and target_param.VolatileData is not None:
                target_param.VolatileData.Clear()
                cleared_info.append("VolatileData.Clear()")

        except Exception as e:
            # Log but continue - some parameters may not support clearing
            cleared_info.append(f"Clear error (continuing): {str(e)}")

        # Convert Rhino object IDs to Guids and get geometry
        geometries_added = []
        errors = []

        for obj_id in rhino_object_ids:
            try:
                guid = System.Guid(obj_id)
                rhino_obj = sc.doc.Objects.FindId(guid)

                if rhino_obj:
                    geom = rhino_obj.Geometry

                    if geom:
                        # Create appropriate GH type wrapper
                        gh_geom = None

                        if isinstance(geom, Rhino.Geometry.Curve):
                            gh_geom = Grasshopper.Kernel.Types.GH_Curve(geom)
                        elif isinstance(geom, Rhino.Geometry.Surface):
                            gh_geom = Grasshopper.Kernel.Types.GH_Surface(geom)
                        elif isinstance(geom, Rhino.Geometry.Brep):
                            gh_geom = Grasshopper.Kernel.Types.GH_Brep(geom)
                        elif isinstance(geom, Rhino.Geometry.Point3d):
                            gh_geom = Grasshopper.Kernel.Types.GH_Point(geom)
                        elif isinstance(geom, Rhino.Geometry.Mesh):
                            gh_geom = Grasshopper.Kernel.Types.GH_Mesh(geom)
                        else:
                            # Try generic geometry wrapper
                            try:
                                gh_geom = Grasshopper.Kernel.Types.GH_GeometricGoo.CreateFromGeometry(geom)
                            except:
                                pass

                        if gh_geom:
                            # Add to persistent data
                            target_param.AddPersistentData(gh_geom)
                            geometries_added.append(obj_id)
                        else:
                            errors.append(f"Could not convert geometry type {type(geom).__name__}")
                    else:
                        errors.append(f"Object {obj_id} has no geometry")
                else:
                    errors.append(f"Object {obj_id} not found in Rhino document")

            except Exception as e:
                errors.append(f"Error processing {obj_id}: {str(e)}")
                continue

        if not geometries_added:
            return {
                "success": False,
                "error": "Failed to add any geometry to parameter",
                "details": errors
            }

        # Expire solution to recompute
        target_param.ExpireSolution(True)
        gh_doc.NewSolution(True)

        return {
            "success": True,
            "parameter_name": parameter_name,
            "geometries_added": len(geometries_added),
            "object_ids": geometries_added,
            "cleared_operations": cleared_info,
            "message": f"Successfully set {len(geometries_added)} geometry object(s) to parameter '{parameter_name}' (replaced existing data)"
        }

    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error setting geometry input: {str(e)}",
            "traceback": traceback.format_exc()
        }

@gh_tool(
    name="extract_grasshopper_geometry_output",
    description=(
        "Extract geometry data from a Grasshopper output parameter component in a specific file. "
        "This tool will activate the specified file (making it visible to the user), "
        "then retrieve the computed geometry (curves, surfaces, points, etc.) from Grasshopper "
        "and optionally bake it into the Rhino document.\n\n"
        "**Parameters:**\n"
        "- **file_name** (str, required): Name of the .gh file to extract from (e.g., 'Primary Truss Generator.gh')\n"
        "- **parameter_name** (str): Name of the Grasshopper output parameter to extract from\n"
        "- **bake_to_rhino** (bool): Whether to bake the geometry into Rhino document (default: false)\n"
        "- **layer_name** (str, optional): Layer name to bake geometry to (creates if doesn't exist)\n"
        "\n**Returns:**\n"
        "Dictionary containing extracted geometry data and optionally baked object IDs."
    )
)
async def extract_grasshopper_geometry_output(
    file_name: str,
    parameter_name: str,
    bake_to_rhino: bool = False,
    layer_name: str = ""
) -> Dict[str, Any]:
    """
    Extract geometry from a Grasshopper output parameter via HTTP bridge.

    Args:
        file_name: Name of the .gh file to extract from
        parameter_name: Name of the output parameter component
        bake_to_rhino: Whether to bake geometry into Rhino
        layer_name: Optional layer name for baked geometry

    Returns:
        Dict containing extracted geometry data
    """

    request_data = {
        "file_name": file_name,
        "parameter_name": parameter_name,
        "bake_to_rhino": bake_to_rhino,
        "layer_name": layer_name
    }

    return call_bridge_api("/extract_geometry_output", request_data)

@bridge_handler("/extract_geometry_output")
def handle_extract_geometry_output(data):
    """Bridge handler for extracting geometry output"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        clr.AddReference('RhinoCommon')
        import Grasshopper
        import Rhino
        import rhinoscriptsyntax as rs
        import scriptcontext as sc

        file_name = data.get('file_name', '')
        parameter_name = data.get('parameter_name', '')
        bake_to_rhino = data.get('bake_to_rhino', False)
        layer_name = data.get('layer_name', '')

        if not parameter_name:
            return {
                "success": False,
                "error": "No parameter_name provided",
                "file_name": file_name
            }

        # Ensure the correct file is active first
        activation_result = ensure_file_is_active(file_name)
        if not activation_result.get("success", False):
            return {
                "success": False,
                "error": activation_result.get("error", "Failed to activate file"),
                "file_name": file_name,
                "parameter_name": parameter_name
            }

        # Get the Grasshopper plugin and document
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            return {
                "success": False,
                "error": "Grasshopper plugin not available",
                "file_name": file_name
            }

        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found",
                "file_name": file_name
            }

        # Find the parameter component
        param_found = False
        target_param = None

        for obj in gh_doc.Objects:
            if (obj.NickName or "Unnamed") == parameter_name:
                # Check if it's a parameter with output data
                if hasattr(obj, 'VolatileData') and obj.VolatileData:
                    target_param = obj
                    param_found = True
                    break

        if not param_found:
            return {
                "success": False,
                "error": f"Parameter '{parameter_name}' not found or has no output data"
            }

        # Extract geometry data
        extracted_geometry = []
        baked_ids = []
        geometry_types_extracted = []

        if target_param.VolatileData:
            vd = target_param.VolatileData

            # Set up layer if baking
            if bake_to_rhino and layer_name:
                if not rs.IsLayer(layer_name):
                    rs.AddLayer(layer_name)
                rs.CurrentLayer(layer_name)

            for path in vd.Paths:
                branch = vd.get_Branch(path)
                if branch:
                    for i in range(branch.Count):
                        try:
                            item = branch[i]
                            if item is not None:
                                geom_info = {
                                    "index": i,
                                    "path": str(path),
                                    "type": type(item).__name__,
                                    "data": {}
                                }

                                # Extract actual geometry
                                actual_geom = None

                                if hasattr(item, 'Value'):
                                    actual_geom = item.Value
                                else:
                                    actual_geom = item

                                if actual_geom:
                                    geometry_types_extracted.append(type(actual_geom).__name__)

                                # Use smart conversion for baking
                                bakeable_geom = None
                                if bake_to_rhino and actual_geom:
                                    converted_geom, orig_type, conv_type, success, error_msg = convert_geometry_to_base(actual_geom)
                                    if success and converted_geom:
                                        bakeable_geom = converted_geom

                                # Get geometry details based on type
                                # Check for Line FIRST (before Curve) as it's a struct, not a Curve subclass
                                if isinstance(actual_geom, Rhino.Geometry.Line):
                                    geom_info["geometry_type"] = "Line"
                                    geom_info["data"]["length"] = float(actual_geom.Length)
                                    geom_info["data"]["start"] = {
                                        "x": float(actual_geom.From.X),
                                        "y": float(actual_geom.From.Y),
                                        "z": float(actual_geom.From.Z)
                                    }
                                    geom_info["data"]["end"] = {
                                        "x": float(actual_geom.To.X),
                                        "y": float(actual_geom.To.Y),
                                        "z": float(actual_geom.To.Z)
                                    }

                                    # Bake if requested - use converted geometry
                                    if bake_to_rhino and bakeable_geom:
                                        obj_id = sc.doc.Objects.Add(bakeable_geom)
                                        if obj_id != System.Guid.Empty:
                                            baked_ids.append(str(obj_id))
                                            sc.doc.Views.Redraw()

                                elif isinstance(actual_geom, Rhino.Geometry.Arc):
                                    geom_info["geometry_type"] = "Arc"
                                    geom_info["data"]["length"] = float(actual_geom.Length)
                                    geom_info["data"]["radius"] = float(actual_geom.Radius)
                                    geom_info["data"]["center"] = {
                                        "x": float(actual_geom.Center.X),
                                        "y": float(actual_geom.Center.Y),
                                        "z": float(actual_geom.Center.Z)
                                    }

                                    # Bake if requested
                                    if bake_to_rhino and bakeable_geom:
                                        obj_id = sc.doc.Objects.Add(bakeable_geom)
                                        if obj_id != System.Guid.Empty:
                                            baked_ids.append(str(obj_id))
                                            sc.doc.Views.Redraw()

                                elif isinstance(actual_geom, Rhino.Geometry.Circle):
                                    geom_info["geometry_type"] = "Circle"
                                    geom_info["data"]["radius"] = float(actual_geom.Radius)
                                    geom_info["data"]["circumference"] = float(actual_geom.Circumference)
                                    geom_info["data"]["center"] = {
                                        "x": float(actual_geom.Center.X),
                                        "y": float(actual_geom.Center.Y),
                                        "z": float(actual_geom.Center.Z)
                                    }

                                    # Bake if requested
                                    if bake_to_rhino and bakeable_geom:
                                        obj_id = sc.doc.Objects.Add(bakeable_geom)
                                        if obj_id != System.Guid.Empty:
                                            baked_ids.append(str(obj_id))
                                            sc.doc.Views.Redraw()

                                elif isinstance(actual_geom, Rhino.Geometry.Curve):
                                    geom_info["geometry_type"] = "Curve"
                                    geom_info["data"]["length"] = float(actual_geom.GetLength())
                                    geom_info["data"]["is_closed"] = actual_geom.IsClosed

                                    # Sample points
                                    sample_points = []
                                    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
                                        param = actual_geom.Domain.ParameterAt(t)
                                        pt = actual_geom.PointAt(param)
                                        sample_points.append({
                                            "x": float(pt.X),
                                            "y": float(pt.Y),
                                            "z": float(pt.Z)
                                        })
                                    geom_info["data"]["sample_points"] = sample_points

                                    # Bake if requested
                                    if bake_to_rhino:
                                        obj_id = sc.doc.Objects.AddCurve(actual_geom)
                                        if obj_id != System.Guid.Empty:
                                            baked_ids.append(str(obj_id))
                                            sc.doc.Views.Redraw()

                                elif isinstance(actual_geom, Rhino.Geometry.Surface):
                                    geom_info["geometry_type"] = "Surface"
                                    try:
                                        area = actual_geom.GetSurfaceSize()
                                        geom_info["data"]["area"] = float(area[0]) if area[0] else None
                                    except:
                                        geom_info["data"]["area"] = None

                                    # Bake if requested
                                    if bake_to_rhino:
                                        obj_id = sc.doc.Objects.AddSurface(actual_geom)
                                        if obj_id != System.Guid.Empty:
                                            baked_ids.append(str(obj_id))
                                            sc.doc.Views.Redraw()

                                elif isinstance(actual_geom, Rhino.Geometry.Point3d):
                                    geom_info["geometry_type"] = "Point"
                                    geom_info["data"]["coordinates"] = {
                                        "x": float(actual_geom.X),
                                        "y": float(actual_geom.Y),
                                        "z": float(actual_geom.Z)
                                    }

                                    # Bake if requested
                                    if bake_to_rhino:
                                        obj_id = sc.doc.Objects.AddPoint(actual_geom)
                                        if obj_id != System.Guid.Empty:
                                            baked_ids.append(str(obj_id))
                                            sc.doc.Views.Redraw()

                                elif isinstance(actual_geom, Rhino.Geometry.Brep):
                                    geom_info["geometry_type"] = "Brep"
                                    geom_info["data"]["is_solid"] = actual_geom.IsSolid
                                    geom_info["data"]["volume"] = float(actual_geom.GetVolume()) if actual_geom.IsSolid else None

                                    # Bake if requested
                                    if bake_to_rhino:
                                        obj_id = sc.doc.Objects.AddBrep(actual_geom)
                                        if obj_id != System.Guid.Empty:
                                            baked_ids.append(str(obj_id))
                                            sc.doc.Views.Redraw()

                                elif isinstance(actual_geom, Rhino.Geometry.Mesh):
                                    geom_info["geometry_type"] = "Mesh"
                                    geom_info["data"]["vertex_count"] = actual_geom.Vertices.Count
                                    geom_info["data"]["face_count"] = actual_geom.Faces.Count

                                    # Bake if requested
                                    if bake_to_rhino:
                                        obj_id = sc.doc.Objects.AddMesh(actual_geom)
                                        if obj_id != System.Guid.Empty:
                                            baked_ids.append(str(obj_id))
                                            sc.doc.Views.Redraw()

                                # Handle data types (numbers, text, etc.) - cannot be baked
                                elif isinstance(actual_geom, (int, float)):
                                    geom_info["geometry_type"] = "Number"
                                    geom_info["data"]["value"] = float(actual_geom)
                                    # Numbers cannot be baked to Rhino

                                elif isinstance(actual_geom, str):
                                    geom_info["geometry_type"] = "Text"
                                    geom_info["data"]["text"] = str(actual_geom)
                                    # Text cannot be baked to Rhino (would need text entity)

                                elif isinstance(actual_geom, bool):
                                    geom_info["geometry_type"] = "Boolean"
                                    geom_info["data"]["value"] = bool(actual_geom)
                                    # Booleans cannot be baked to Rhino

                                extracted_geometry.append(geom_info)

                        except Exception as e:
                            continue

        result = {
            "success": True,
            "parameter_name": parameter_name,
            "geometry_count": len(extracted_geometry),
            "extracted_geometry": extracted_geometry,
            "geometry_types": list(set(geometry_types_extracted)),
            "message": f"Extracted {len(extracted_geometry)} geometry object(s) from '{parameter_name}'"
        }

        if bake_to_rhino:
            result["baked_to_rhino"] = True
            result["baked_object_ids"] = baked_ids
            result["baked_count"] = len(baked_ids)
            result["layer"] = layer_name or "Current"
            result["message"] += f" and baked {len(baked_ids)} to Rhino"
            if len(baked_ids) == 0 and len(extracted_geometry) > 0:
                result["warning"] = f"Extracted {len(extracted_geometry)} geometries but baked 0. Types found: {', '.join(set(geometry_types_extracted))}"

        return result

    except ImportError as e:
        return {
            "success": False,
            "error": f"Grasshopper not available: {str(e)}"
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error extracting geometry output: {str(e)}",
            "traceback": traceback.format_exc()
        }

# ============================================================================
# CROSS-FILE WORKFLOW TOOLS (GENERIC)
# ============================================================================

def convert_geometry_to_base(geom, debug_log=None):
    """
    Convert various Rhino geometry types to GeometryBase for adding to document.
    Returns (converted_geometry, original_type_name, converted_type_name, success, error_message)
    """
    import Rhino

    if geom is None:
        return (None, "None", "None", False, "Geometry is None")

    original_type = type(geom).__name__

    # Handle Line struct -> LineCurve
    if isinstance(geom, Rhino.Geometry.Line):
        if not geom.IsValid:
            return (None, original_type, "LineCurve", False, "Invalid Line")
        converted = Rhino.Geometry.LineCurve(geom)
        if debug_log is not None:
            debug_log.append(f"Converted Line to LineCurve")
        return (converted, original_type, "LineCurve", True, None)

    # Handle Arc struct -> ArcCurve
    if isinstance(geom, Rhino.Geometry.Arc):
        if not geom.IsValid:
            return (None, original_type, "ArcCurve", False, "Invalid Arc")
        converted = Rhino.Geometry.ArcCurve(geom)
        if debug_log is not None:
            debug_log.append(f"Converted Arc to ArcCurve")
        return (converted, original_type, "ArcCurve", True, None)

    # Handle Circle struct -> ArcCurve
    if isinstance(geom, Rhino.Geometry.Circle):
        if not geom.IsValid:
            return (None, original_type, "ArcCurve", False, "Invalid Circle")
        converted = Rhino.Geometry.ArcCurve(geom)
        if debug_log is not None:
            debug_log.append(f"Converted Circle to ArcCurve")
        return (converted, original_type, "ArcCurve", True, None)

    # Handle Plane -> PlaneSurface
    if isinstance(geom, Rhino.Geometry.Plane):
        if not geom.IsValid:
            return (None, original_type, "PlaneSurface", False, "Invalid Plane")
        # Create a plane surface with default extents
        converted = Rhino.Geometry.PlaneSurface(geom, Rhino.Geometry.Interval(-100, 100), Rhino.Geometry.Interval(-100, 100))
        if debug_log is not None:
            debug_log.append(f"Converted Plane to PlaneSurface")
        return (converted, original_type, "PlaneSurface", True, None)

    # Handle Box -> Brep
    if isinstance(geom, Rhino.Geometry.Box):
        if not geom.IsValid:
            return (None, original_type, "Brep", False, "Invalid Box")
        converted = geom.ToBrep()
        if debug_log is not None:
            debug_log.append(f"Converted Box to Brep")
        return (converted, original_type, "Brep", True, None)

    # Already GeometryBase types - validate and pass through
    if isinstance(geom, Rhino.Geometry.GeometryBase):
        if isinstance(geom, Rhino.Geometry.Curve):
            if not geom.IsValid:
                return (None, original_type, original_type, False, "Invalid Curve")
        elif isinstance(geom, Rhino.Geometry.Surface):
            if not geom.IsValid:
                return (None, original_type, original_type, False, "Invalid Surface")
        elif isinstance(geom, Rhino.Geometry.Brep):
            if not geom.IsValid:
                return (None, original_type, original_type, False, "Invalid Brep")
        elif isinstance(geom, Rhino.Geometry.Mesh):
            if not geom.IsValid:
                return (None, original_type, original_type, False, "Invalid Mesh")

        return (geom, original_type, original_type, True, None)

    # Handle non-geometry data types (numbers, strings, etc.)
    # These cannot be added to Rhino document but can be transferred as data
    if isinstance(geom, (int, float, str, bool)):
        return (None, original_type, "Data", False, f"Data type {original_type} cannot be baked to Rhino (use for data-only transfer)")

    # Unknown type
    return (None, original_type, "Unknown", False, f"Unsupported geometry type: {original_type}")


def validate_geometry_compatibility(source_types, target_param_obj, debug_log=None):
    """
    Validate if source geometry types are compatible with target parameter.
    Returns (is_compatible, warning_message)
    """
    import Grasshopper

    if not target_param_obj:
        return (True, None)  # Can't validate without target

    # Get target parameter type hints
    target_type_name = type(target_param_obj).__name__

    # Build compatibility message
    warnings = []

    # Check if target expects specific types
    if hasattr(target_param_obj, 'TypeHint'):
        type_hint = target_param_obj.TypeHint
        if type_hint:
            hint_name = type(type_hint).__name__
            if debug_log is not None:
                debug_log.append(f"Target parameter type hint: {hint_name}")

    # Detect common incompatibilities
    has_curves = any(t in source_types for t in ['Line', 'LineCurve', 'Curve', 'Arc', 'ArcCurve', 'Circle', 'NurbsCurve', 'PolyCurve', 'Polyline'])
    has_surfaces = any(t in source_types for t in ['Surface', 'Brep', 'BrepFace', 'NurbsSurface', 'PlaneSurface'])
    has_meshes = any(t in source_types for t in ['Mesh'])
    has_data = any(t in source_types for t in ['Int32', 'Double', 'String', 'Boolean', 'int', 'float', 'str', 'bool'])

    # Check target parameter type
    if 'Curve' in target_type_name:
        if has_surfaces:
            warnings.append("WARNING: Source contains Surfaces/Breps but target expects Curves. Surface edges may be extracted.")
        if has_meshes:
            warnings.append("WARNING: Source contains Meshes but target expects Curves. This may fail or extract mesh edges.")
        if has_data:
            warnings.append("WARNING: Source contains data (numbers/text) but target expects Curves. These will be skipped.")

    elif 'Surface' in target_type_name or 'Brep' in target_type_name:
        if has_curves:
            warnings.append("INFO: Source contains Curves but target expects Surfaces. Curves will be passed as-is (may need lofting/extrusion).")
        if has_data:
            warnings.append("WARNING: Source contains data (numbers/text) but target expects Surfaces. These will be skipped.")

    elif 'Mesh' in target_type_name:
        if has_curves:
            warnings.append("WARNING: Source contains Curves but target expects Meshes. This will likely fail.")
        if has_surfaces:
            warnings.append("INFO: Source contains Surfaces/Breps but target expects Meshes. May need meshing component.")
        if has_data:
            warnings.append("WARNING: Source contains data (numbers/text) but target expects Meshes. These will be skipped.")

    elif 'Number' in target_type_name or 'Integer' in target_type_name:
        if has_curves or has_surfaces or has_meshes:
            warnings.append("WARNING: Source contains geometry but target expects Numbers. This will fail.")

    return (len([w for w in warnings if w.startswith("WARNING")]) == 0, warnings)


@gh_tool(
    name="transfer_eml_geometry_between_files",
    description=(
        "Transfer geometry data directly between two Grasshopper files without baking to Rhino. "
        "This tool extracts geometry from an eml_ output parameter in one file and injects it "
        "into an eml_ input parameter in another file. Works with ANY eml_ prefixed geometry parameters.\n\n"
        "**Use Cases:**\n"
        "- Transfer curves from a generator file to a processor file\n"
        "- Pass surfaces between optimization stages\n"
        "- Chain multiple .gh files in a pipeline\n\n"
        "**Parameters:**\n"
        "- **source_file** (str): Source .gh filename (e.g., 'curve_generator.gh')\n"
        "- **source_parameter** (str): Output parameter name (e.g., 'eml_output_curves')\n"
        "- **target_file** (str): Target .gh filename (e.g., 'surface_builder.gh')\n"
        "- **target_parameter** (str): Input parameter name (e.g., 'eml_input_curves')\n"
        "- **auto_open_files** (bool): Automatically open files if not already open (default: true)\n"
        "\n**Returns:**\n"
        "Dictionary containing transfer status and geometry information."
    )
)
async def transfer_eml_geometry_between_files(
    source_file: str,
    source_parameter: str,
    target_file: str,
    target_parameter: str,
    auto_open_files: bool = True
) -> Dict[str, Any]:
    """
    Transfer geometry between two Grasshopper files via eml_ parameters.

    Args:
        source_file: Source .gh filename
        source_parameter: Output parameter name in source file
        target_file: Target .gh filename
        target_parameter: Input parameter name in target file
        auto_open_files: Auto-open files if needed

    Returns:
        Dict containing transfer results
    """
    request_data = {
        "source_file": source_file,
        "source_parameter": source_parameter,
        "target_file": target_file,
        "target_parameter": target_parameter,
        "auto_open_files": auto_open_files
    }

    return call_bridge_api("/transfer_eml_geometry", request_data)

@bridge_handler("/transfer_eml_geometry")
def handle_transfer_eml_geometry(data):
    """Bridge handler for transferring geometry between files"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        clr.AddReference('RhinoCommon')
        import Grasshopper
        import Rhino
        import System
        import scriptcontext as sc
        import os

        source_file = data.get('source_file', '')
        source_parameter = data.get('source_parameter', '')
        target_file = data.get('target_file', '')
        target_parameter = data.get('target_parameter', '')
        auto_open_files = data.get('auto_open_files', True)

        # Ensure Grasshopper is loaded
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            if auto_open_files:
                Rhino.RhinoApp.RunScript("_Grasshopper", False)
                import time
                time.sleep(2)
                gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
            if not gh:
                return {
                    "success": False,
                    "error": "Grasshopper plugin not available"
                }

        # Helper function to find and open file
        def open_gh_file_if_needed(file_name):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            library_path = os.path.join(script_dir, "Grasshopper File Library")

            # Find the file
            target_file = None
            for root, dirs, files in os.walk(library_path):
                for file in files:
                    if file.lower() == file_name.lower():
                        target_file = os.path.join(root, file)
                        break
                if target_file:
                    break

            if not target_file:
                return None

            # Check if already open
            doc_server = Grasshopper.Instances.DocumentServer
            if doc_server:
                for doc in doc_server:
                    if doc and hasattr(doc, 'FilePath') and doc.FilePath:
                        if os.path.normpath(doc.FilePath).lower() == os.path.normpath(target_file).lower():
                            return doc  # Already open

            # Open the file if auto_open is enabled
            if auto_open_files:
                command = f'_GrasshopperOpen "{target_file}"'
                Rhino.RhinoApp.RunScript(command, False)
                import time
                time.sleep(1)  # Give it time to load

                # Try to get the newly opened document
                doc_server = Grasshopper.Instances.DocumentServer
                if doc_server:
                    for doc in doc_server:
                        if doc and hasattr(doc, 'FilePath') and doc.FilePath:
                            if os.path.normpath(doc.FilePath).lower() == os.path.normpath(target_file).lower():
                                return doc

            return None

        # Debug info
        debug_info = []
        debug_info.append(f"Attempting to transfer from {source_file}:{source_parameter} to {target_file}:{target_parameter}")

        # Step 1: Open source file and extract geometry
        source_doc = open_gh_file_if_needed(source_file)
        if not source_doc:
            return {
                "success": False,
                "error": f"Could not open or find source file: {source_file}",
                "debug_info": debug_info
            }

        debug_info.append(f"Source file opened: {source_file}")
        source_path = str(source_doc.FilePath) if source_doc.FilePath else None

        # PROPERLY activate source doc using OpenDocument (this switches the visible tab)
        if source_path:
            try:
                import time
                debug_info.append(f"Calling gh.OpenDocument for source: {source_path}")
                gh.OpenDocument(source_path)
                time.sleep(0.5)  # Give UI time to switch

                # Verify activation worked
                if Grasshopper.Instances.ActiveCanvas and Grasshopper.Instances.ActiveCanvas.Document:
                    active_doc = Grasshopper.Instances.ActiveCanvas.Document
                    active_name = os.path.basename(str(active_doc.FilePath)) if active_doc.FilePath else "Unknown"
                    debug_info.append(f"Active document after OpenDocument: {active_name}")

                    if active_doc == source_doc:
                        debug_info.append(f"✓ Successfully activated source file: {source_file}")
                    else:
                        debug_info.append(f"WARNING: Expected {source_file} to be active, but {active_name} is active")
                else:
                    debug_info.append(f"WARNING: No active canvas after OpenDocument")
            except Exception as e:
                debug_info.append(f"ERROR activating source file: {str(e)}")
                import traceback
                debug_info.append(f"Traceback: {traceback.format_exc()[:300]}")

        # Find source parameter and extract geometry
        source_obj = None
        for obj in source_doc.Objects:
            if hasattr(obj, 'NickName') and obj.NickName:
                if obj.NickName.lower() == source_parameter.lower():
                    source_obj = obj
                    debug_info.append(f"Found source parameter: {source_parameter}")
                    break

        if not source_obj:
            return {
                "success": False,
                "error": f"Source parameter '{source_parameter}' not found in {source_file}",
                "debug_info": debug_info
            }

        # Extract geometry data
        if not hasattr(source_obj, 'VolatileData'):
            return {
                "success": False,
                "error": f"Source parameter '{source_parameter}' has no data",
                "debug_info": debug_info
            }

        # Store geometry temporarily in Rhino document (as referenced objects)
        rhino_object_ids = []
        geometry_types_found = []
        try:
            volatile_data = source_obj.VolatileData
            debug_info.append(f"VolatileData PathCount: {volatile_data.PathCount}")

            for i in range(volatile_data.PathCount):
                path = volatile_data.get_Path(i)
                branch = volatile_data.get_Branch(path)
                debug_info.append(f"Branch {i} has {len(branch)} items")

                for item in branch:
                    if hasattr(item, 'Value'):
                        geom = item.Value
                        if geom:
                            original_type = type(geom).__name__
                            geometry_types_found.append(original_type)

                            # Use smart conversion helper
                            converted_geom, orig_type, conv_type, success, error_msg = convert_geometry_to_base(geom, debug_info)

                            if not success:
                                debug_info.append(f"Skipping {orig_type}: {error_msg}")
                                continue

                            if converted_geom is None:
                                debug_info.append(f"WARNING: Conversion returned None for {orig_type}")
                                continue

                            # Add to Rhino document temporarily
                            obj_id = sc.doc.Objects.Add(converted_geom)
                            if obj_id != System.Guid.Empty:
                                rhino_object_ids.append(str(obj_id))
                                if orig_type != conv_type:
                                    debug_info.append(f"Added geometry to Rhino: {orig_type} (converted to {conv_type}) -> {obj_id}")
                                else:
                                    debug_info.append(f"Added geometry to Rhino: {orig_type} -> {obj_id}")
                            else:
                                debug_info.append(f"WARNING: Failed to add {orig_type} (as {conv_type}) to Rhino document")
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": f"Error extracting geometry: {str(e)}",
                "traceback": traceback.format_exc(),
                "debug_info": debug_info
            }

        if not rhino_object_ids:
            return {
                "success": False,
                "error": f"No geometry found in source parameter '{source_parameter}'",
                "debug_info": debug_info,
                "geometry_types_found": list(set(geometry_types_found))
            }

        debug_info.append(f"Extracted {len(rhino_object_ids)} geometry objects from source")
        debug_info.append(f"Geometry types found: {', '.join(set(geometry_types_found))}")

        # Step 2: Open target file
        target_doc = open_gh_file_if_needed(target_file)
        if not target_doc:
            # Clean up temporary Rhino objects
            for obj_id in rhino_object_ids:
                sc.doc.Objects.Delete(System.Guid(obj_id), True)
            return {
                "success": False,
                "error": f"Could not open or find target file: {target_file}",
                "debug_info": debug_info
            }

        debug_info.append(f"Target file opened: {target_file}")
        target_path = str(target_doc.FilePath) if target_doc.FilePath else None

        # PROPERLY activate target doc using OpenDocument (this switches the visible tab)
        if target_path:
            try:
                import time
                debug_info.append(f"Calling gh.OpenDocument for target: {target_path}")
                gh.OpenDocument(target_path)
                time.sleep(0.5)  # Give UI time to switch

                # Verify activation worked
                if Grasshopper.Instances.ActiveCanvas and Grasshopper.Instances.ActiveCanvas.Document:
                    active_doc = Grasshopper.Instances.ActiveCanvas.Document
                    active_name = os.path.basename(str(active_doc.FilePath)) if active_doc.FilePath else "Unknown"
                    debug_info.append(f"Active document after OpenDocument: {active_name}")

                    if active_doc == target_doc:
                        debug_info.append(f"✓ Successfully activated target file: {target_file}")
                    else:
                        debug_info.append(f"WARNING: Expected {target_file} to be active, but {active_name} is active")
                else:
                    debug_info.append(f"WARNING: No active canvas after OpenDocument")
            except Exception as e:
                debug_info.append(f"ERROR activating target file: {str(e)}")
                import traceback
                debug_info.append(f"Traceback: {traceback.format_exc()[:300]}")

        # Find target parameter
        target_obj = None
        for obj in target_doc.Objects:
            if hasattr(obj, 'NickName') and obj.NickName:
                if obj.NickName.lower() == target_parameter.lower():
                    target_obj = obj
                    debug_info.append(f"Found target parameter: {target_parameter}")
                    break

        if not target_obj:
            # Clean up temporary Rhino objects
            for obj_id in rhino_object_ids:
                sc.doc.Objects.Delete(System.Guid(obj_id), True)
            return {
                "success": False,
                "error": f"Target parameter '{target_parameter}' not found in {target_file}",
                "debug_info": debug_info
            }

        # Validate geometry compatibility with target
        is_compatible, compatibility_warnings = validate_geometry_compatibility(
            list(set(geometry_types_found)),
            target_obj,
            debug_info
        )

        if compatibility_warnings:
            for warning in compatibility_warnings:
                debug_info.append(warning)

        # Step 3: Inject geometry into target parameter
        try:
            debug_info.append(f"Clearing existing data from target parameter to replace (not append)")

            # Thorough clearing to ensure replacement not appending
            if hasattr(target_obj, 'ClearData'):
                target_obj.ClearData()

            # Also clear persistent data explicitly
            if hasattr(target_obj, 'PersistentData') and target_obj.PersistentData is not None:
                target_obj.PersistentData.Clear()

            # Clear volatile data if present
            if hasattr(target_obj, 'VolatileData') and target_obj.VolatileData is not None:
                target_obj.VolatileData.Clear()

            debug_info.append(f"Data cleared successfully, adding new geometry")

            # Add new references
            transferred_count = 0
            for obj_id_str in rhino_object_ids:
                obj_id = System.Guid(obj_id_str)
                rhino_obj = sc.doc.Objects.Find(obj_id)
                if rhino_obj:
                    geom = rhino_obj.Geometry
                    if geom:
                        # Add geometry as persistent data
                        target_obj.AddPersistentData(geom.Duplicate())
                        transferred_count += 1
                        debug_info.append(f"Transferred geometry {transferred_count}/{len(rhino_object_ids)}: {type(geom).__name__}")

            debug_info.append(f"Expiring solution to trigger recompute")
            # Expire solution to trigger recompute
            target_obj.ExpireSolution(True)

            debug_info.append(f"Cleaning up temporary Rhino objects")
            # Clean up temporary Rhino objects
            for obj_id in rhino_object_ids:
                sc.doc.Objects.Delete(System.Guid(obj_id), True)

            debug_info.append(f"Transfer complete! {transferred_count} objects transferred")

            result = {
                "success": True,
                "message": f"Successfully transferred {transferred_count} geometry object(s) from {source_file} to {target_file}",
                "source_file": source_file,
                "source_parameter": source_parameter,
                "target_file": target_file,
                "target_parameter": target_parameter,
                "geometry_count": transferred_count,
                "geometry_types": list(set(geometry_types_found)),
                "debug_info": debug_info
            }

            # Add compatibility warnings if any
            if compatibility_warnings:
                result["compatibility_warnings"] = compatibility_warnings
                result["is_compatible"] = is_compatible

            return result

        except Exception as e:
            import traceback
            debug_info.append(f"ERROR during injection: {str(e)}")
            debug_info.append(f"Traceback: {traceback.format_exc()[:500]}")

            # Clean up temporary Rhino objects
            for obj_id in rhino_object_ids:
                try:
                    sc.doc.Objects.Delete(System.Guid(obj_id), True)
                except:
                    pass
            return {
                "success": False,
                "error": f"Error injecting geometry: {str(e)}",
                "traceback": traceback.format_exc(),
                "debug_info": debug_info
            }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error in geometry transfer: {str(e)}",
            "traceback": traceback.format_exc(),
            "debug_info": debug_info if 'debug_info' in locals() else []
        }

@gh_tool(
    name="execute_eml_workflow",
    description=(
        "Execute an automated multi-file Grasshopper workflow. This tool chains multiple .gh files "
        "together, automatically transferring data between eml_ parameters. Works with ANY .gh files "
        "that follow the eml_ naming convention.\n\n"
        "**Use Cases:**\n"
        "- Automated design pipelines (generator → processor → exporter)\n"
        "- Multi-stage optimization workflows\n"
        "- Complex parametric workflows without manual intervention\n\n"
        "**Parameters:**\n"
        "- **workflow_steps** (list): List of workflow steps, each containing:\n"
        "  - **file** (str): .gh filename\n"
        "  - **inputs** (dict, optional): Input parameter values {param_name: value}\n"
        "    - Values can be numbers, strings, or Rhino object IDs\n"
        "    - Use '{{step_N.param_name}}' to reference outputs from previous steps\n"
        "  - **extract_outputs** (list, optional): List of output parameter names to extract\n"
        "- **auto_discover** (bool): Auto-discover and suggest connections (default: false)\n"
        "\n**Example:**\n"
        "```json\n"
        "[\n"
        "  {\n"
        "    \"file\": \"curve_generator.gh\",\n"
        "    \"inputs\": {\"eml_num_points\": 20},\n"
        "    \"extract_outputs\": [\"eml_output_curve\"]\n"
        "  },\n"
        "  {\n"
        "    \"file\": \"surface_builder.gh\",\n"
        "    \"inputs\": {\"eml_input_curve\": \"{{step_0.eml_output_curve}}\"},\n"
        "    \"extract_outputs\": [\"eml_output_surface\"]\n"
        "  }\n"
        "]\n"
        "```\n"
        "\n**Returns:**\n"
        "Dictionary containing workflow execution results and extracted outputs from each step."
    )
)
async def execute_eml_workflow(
    workflow_steps,
    auto_discover: bool = False
) -> Dict[str, Any]:
    """
    Execute an automated multi-file EML workflow.

    Args:
        workflow_steps: List of workflow step configurations
        auto_discover: Auto-discover and suggest parameter connections

    Returns:
        Dict containing workflow results
    """
    request_data = {
        "workflow_steps": workflow_steps,
        "auto_discover": auto_discover
    }

    return call_bridge_api("/execute_eml_workflow", request_data)

@bridge_handler("/execute_eml_workflow")
def handle_execute_eml_workflow(data):
    """Bridge handler for executing EML workflows"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        clr.AddReference('RhinoCommon')
        import Grasshopper
        import Rhino
        import System
        import scriptcontext as sc
        import os
        import re

        workflow_steps = data.get('workflow_steps', [])
        auto_discover = data.get('auto_discover', False)

        if not workflow_steps:
            return {
                "success": False,
                "error": "No workflow steps provided"
            }

        # Ensure Grasshopper is loaded
        gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
        if not gh:
            Rhino.RhinoApp.RunScript("_Grasshopper", False)
            import time
            time.sleep(2)
            gh = Rhino.RhinoApp.GetPlugInObject("Grasshopper")
            if not gh:
                return {
                    "success": False,
                    "error": "Grasshopper plugin not available"
                }

        # Storage for outputs from each step
        step_outputs = {}
        results = []

        # Helper function to resolve references like {{step_0.eml_output_curve}}
        def resolve_reference(value, step_outputs):
            if isinstance(value, str):
                match = re.match(r'\{\{step_(\d+)\.(.+)\}\}', value)
                if match:
                    step_idx = int(match.group(1))
                    param_name = match.group(2)
                    if step_idx in step_outputs and param_name in step_outputs[step_idx]:
                        return step_outputs[step_idx][param_name]
            return value

        # Helper function to open/get file
        def get_gh_document(file_name):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            library_path = os.path.join(script_dir, "Grasshopper File Library")

            # Find the file
            target_file = None
            for root, dirs, files in os.walk(library_path):
                for file in files:
                    if file.lower() == file_name.lower():
                        target_file = os.path.join(root, file)
                        break
                if target_file:
                    break

            if not target_file:
                return None, None

            # Check if already open
            doc_server = Grasshopper.Instances.DocumentServer
            if doc_server:
                for doc in doc_server:
                    if doc and hasattr(doc, 'FilePath') and doc.FilePath:
                        if os.path.normpath(doc.FilePath).lower() == os.path.normpath(target_file).lower():
                            return doc, target_file

            # Open the file
            command = f'_GrasshopperOpen "{target_file}"'
            Rhino.RhinoApp.RunScript(command, False)
            import time
            time.sleep(1)

            # Get the newly opened document
            doc_server = Grasshopper.Instances.DocumentServer
            if doc_server:
                for doc in doc_server:
                    if doc and hasattr(doc, 'FilePath') and doc.FilePath:
                        if os.path.normpath(doc.FilePath).lower() == os.path.normpath(target_file).lower():
                            return doc, target_file

            return None, None

        # Execute each step
        for step_idx, step in enumerate(workflow_steps):
            step_file = step.get('file', '')
            step_inputs = step.get('inputs', {})
            extract_outputs = step.get('extract_outputs', [])

            if not step_file:
                results.append({
                    "step": step_idx,
                    "success": False,
                    "error": "No file specified for step"
                })
                continue

            # Open the file
            doc, file_path = get_gh_document(step_file)
            if not doc:
                results.append({
                    "step": step_idx,
                    "file": step_file,
                    "success": False,
                    "error": f"Could not open file: {step_file}"
                })
                continue

            # Activate the document
            doc.Enabled = True

            # Set input parameters
            inputs_set = {}
            for param_name, param_value in step_inputs.items():
                # Resolve references to previous outputs
                resolved_value = resolve_reference(param_value, step_outputs)

                # Find the parameter
                param_obj = None
                for obj in doc.Objects:
                    if hasattr(obj, 'NickName') and obj.NickName:
                        if obj.NickName.lower() == param_name.lower():
                            param_obj = obj
                            break

                if not param_obj:
                    inputs_set[param_name] = {"success": False, "error": "Parameter not found"}
                    continue

                # Handle different types of inputs
                try:
                    # Check if it's a geometry reference (list of object IDs from previous step)
                    if isinstance(resolved_value, list) and all(isinstance(x, str) for x in resolved_value):
                        # Geometry transfer from previous step - clear existing to replace
                        if hasattr(param_obj, 'ClearData'):
                            param_obj.ClearData()
                        if hasattr(param_obj, 'PersistentData') and param_obj.PersistentData is not None:
                            param_obj.PersistentData.Clear()
                        if hasattr(param_obj, 'VolatileData') and param_obj.VolatileData is not None:
                            param_obj.VolatileData.Clear()

                        for obj_id_str in resolved_value:
                            try:
                                obj_id = System.Guid(obj_id_str)
                                rhino_obj = sc.doc.Objects.Find(obj_id)
                                if rhino_obj and rhino_obj.Geometry:
                                    param_obj.AddPersistentData(rhino_obj.Geometry.Duplicate())
                            except:
                                pass
                        param_obj.ExpireSolution(True)
                        inputs_set[param_name] = {"success": True, "type": "geometry_list"}

                    # Handle slider/number parameters
                    elif hasattr(param_obj, 'Slider'):
                        param_obj.Slider.Value = float(resolved_value)
                        param_obj.ExpireSolution(True)
                        inputs_set[param_name] = {"success": True, "value": resolved_value, "type": "slider"}

                    # Handle panel/text parameters
                    elif hasattr(param_obj, 'UserText'):
                        param_obj.UserText = str(resolved_value)
                        param_obj.ExpireSolution(True)
                        inputs_set[param_name] = {"success": True, "value": resolved_value, "type": "panel"}

                    # Handle boolean toggles
                    elif hasattr(param_obj, 'Value') and hasattr(param_obj, 'SetPersistentData'):
                        param_obj.SetPersistentData(0, 0, resolved_value)
                        param_obj.ExpireSolution(True)
                        inputs_set[param_name] = {"success": True, "value": resolved_value, "type": "boolean"}

                    else:
                        inputs_set[param_name] = {"success": False, "error": "Unknown parameter type"}

                except Exception as e:
                    inputs_set[param_name] = {"success": False, "error": str(e)}

            # Extract output parameters
            outputs_extracted = {}
            for output_param_name in extract_outputs:
                # Find the parameter
                output_obj = None
                for obj in doc.Objects:
                    if hasattr(obj, 'NickName') and obj.NickName:
                        if obj.NickName.lower() == output_param_name.lower():
                            output_obj = obj
                            break

                if not output_obj:
                    outputs_extracted[output_param_name] = {"success": False, "error": "Parameter not found"}
                    continue

                # Extract geometry data
                if hasattr(output_obj, 'VolatileData'):
                    try:
                        volatile_data = output_obj.VolatileData
                        temp_obj_ids = []

                        for i in range(volatile_data.PathCount):
                            path = volatile_data.get_Path(i)
                            branch = volatile_data.get_Branch(path)
                            for item in branch:
                                if hasattr(item, 'Value'):
                                    geom = item.Value
                                    if geom:
                                        # Use smart conversion helper
                                        converted_geom, orig_type, conv_type, success, error_msg = convert_geometry_to_base(geom)

                                        if not success or not converted_geom:
                                            continue

                                        # Add to Rhino temporarily
                                        obj_id = sc.doc.Objects.Add(converted_geom)
                                        if obj_id != System.Guid.Empty:
                                            temp_obj_ids.append(str(obj_id))

                        outputs_extracted[output_param_name] = {
                            "success": True,
                            "geometry_ids": temp_obj_ids,
                            "count": len(temp_obj_ids)
                        }

                        # Store for next step
                        if step_idx not in step_outputs:
                            step_outputs[step_idx] = {}
                        step_outputs[step_idx][output_param_name] = temp_obj_ids

                    except Exception as e:
                        outputs_extracted[output_param_name] = {"success": False, "error": str(e)}
                else:
                    outputs_extracted[output_param_name] = {"success": False, "error": "No data available"}

            # Record step results
            results.append({
                "step": step_idx,
                "file": step_file,
                "success": True,
                "inputs_set": inputs_set,
                "outputs_extracted": outputs_extracted
            })

        return {
            "success": True,
            "message": f"Workflow completed with {len(results)} steps",
            "steps": results,
            "total_steps": len(workflow_steps)
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error executing workflow: {str(e)}",
            "traceback": traceback.format_exc()
        }

# ============================================================================
# EXPLICIT BAKING TOOL
# ============================================================================

@gh_tool(
    name="bake_grasshopper_geometry_to_rhino",
    description=(
        "Explicitly bake Grasshopper geometry output to Rhino document with user confirmation. "
        "This tool should ONLY be used when the user explicitly asks to bake geometry. "
        "Unlike extract_grasshopper_geometry_output which is for data inspection, this tool "
        "permanently adds geometry to the Rhino document.\n\n"
        "**IMPORTANT - User Confirmation Required:**\n"
        "Before calling this tool, you MUST confirm with the user:\n"
        "- Which geometries to bake (parameter names)\n"
        "- Which layer to bake to (default: 'Default')\n"
        "- Whether to organize in sub-layers\n\n"
        "**Use Cases:**\n"
        "- User explicitly asks to bake geometry (curves, surfaces, meshes, etc.)\n"
        "- User wants to export parametric geometry from Grasshopper to Rhino\n"
        "- User wants to create permanent Rhino geometry from Grasshopper output\n\n"
        "**Parameters:**\n"
        "- **file_name** (str): Source .gh filename\n"
        "- **parameter_names** (list): List of output parameter names to bake\n"
        "- **layer_name** (str): Target layer name (default: 'Default')\n"
        "- **create_sublayers** (bool): Create sub-layers by parameter name (default: True)\n"
        "- **clear_existing** (bool): Clear existing geometry from target layer(s) before baking (default: False)\n"
        "- **user_confirmed** (bool): Must be True, set after getting user confirmation\n\n"
        "**Returns:**\n"
        "Dictionary with baked geometry details including object IDs, counts, and layer structure."
    )
)
async def bake_grasshopper_geometry_to_rhino(
    file_name: str,
    parameter_names: list,
    layer_name: str = "Default",
    create_sublayers: bool = True,
    clear_existing: bool = False,
    user_confirmed: bool = False
) -> Dict[str, Any]:
    """
    Handler for explicit geometry baking with user confirmation.
    """
    return call_bridge_api("/bake_gh_geometry", {
        "file_name": file_name,
        "parameter_names": parameter_names,
        "layer_name": layer_name,
        "create_sublayers": create_sublayers,
        "clear_existing": clear_existing,
        "user_confirmed": user_confirmed
    })


@bridge_handler("/bake_gh_geometry")
def handle_bake_gh_geometry(data):
    """Bridge handler for explicit geometry baking"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        clr.AddReference('RhinoCommon')
        import Grasshopper
        import Rhino
        import rhinoscriptsyntax as rs
        import scriptcontext as sc
        import System

        file_name = data.get('file_name', '')
        parameter_names = data.get('parameter_names', [])
        layer_name = data.get('layer_name', 'Default')
        create_sublayers = data.get('create_sublayers', True)
        clear_existing = data.get('clear_existing', False)
        user_confirmed = data.get('user_confirmed', False)

        # Safety check - require user confirmation
        if not user_confirmed:
            return {
                "success": False,
                "error": "User confirmation required before baking geometry",
                "message": "Please confirm with the user which geometries to bake and which layer to use before calling this tool with user_confirmed=True."
            }

        if not parameter_names:
            return {
                "success": False,
                "error": "No parameter_names provided"
            }

        # Ensure the correct file is active
        activation_result = ensure_file_is_active(file_name)
        if not activation_result.get("success", False):
            return {
                "success": False,
                "error": activation_result.get("error", "Failed to activate file")
            }

        # Get active Grasshopper document
        gh_doc = Grasshopper.Instances.ActiveCanvas.Document if Grasshopper.Instances.ActiveCanvas else None
        if not gh_doc:
            return {
                "success": False,
                "error": "No active Grasshopper document found"
            }

        # Create or verify layer exists using RhinoCommon
        layer_exists = False
        for i in range(sc.doc.Layers.Count):
            if sc.doc.Layers[i].Name == layer_name:
                layer_exists = True
                break

        if not layer_exists:
            # Create new layer using RhinoCommon
            new_layer = Rhino.DocObjects.Layer()
            new_layer.Name = layer_name
            layer_index_new = sc.doc.Layers.Add(new_layer)
            if layer_index_new < 0:
                return {
                    "success": False,
                    "error": f"Failed to create layer '{layer_name}'"
                }
            # Layer was successfully added
            layer_exists = True

        # Initialize variables
        baking_results = {}
        total_baked = 0
        debug_log = []
        debug_log.append(f"Main layer '{layer_name}' verified/created successfully")

        # Clear existing geometry if requested (for non-sublayer mode)
        if clear_existing and not create_sublayers:
            layer_objects = rs.ObjectsByLayer(layer_name)
            if layer_objects:
                deleted_count = rs.DeleteObjects(layer_objects)
                debug_log.append(f"Cleared {deleted_count} existing objects from layer '{layer_name}'")
            else:
                debug_log.append(f"No existing objects to clear from layer '{layer_name}'")

        for param_name in parameter_names:
            debug_log.append(f"Processing parameter: {param_name}")

            # Find parameter
            param_obj = None
            for obj in gh_doc.Objects:
                if (obj.NickName or "Unnamed") == param_name:
                    if hasattr(obj, 'VolatileData') and obj.VolatileData:
                        param_obj = obj
                        break

            if not param_obj:
                baking_results[param_name] = {
                    "success": False,
                    "error": "Parameter not found or has no data"
                }
                debug_log.append(f"Parameter '{param_name}' not found")
                continue

            # Create sublayer if requested
            target_layer = layer_name
            if create_sublayers:
                # Find parent layer index
                parent_layer_index = -1
                for i in range(sc.doc.Layers.Count):
                    if sc.doc.Layers[i].Name == layer_name:
                        parent_layer_index = i
                        break

                # Check if sublayer exists
                sublayer_name = f"{layer_name}::{param_name}"
                sublayer_exists = False
                for i in range(sc.doc.Layers.Count):
                    if sc.doc.Layers[i].FullPath == sublayer_name:
                        sublayer_exists = True
                        break

                # Create sublayer if it doesn't exist
                if not sublayer_exists and parent_layer_index >= 0:
                    new_sublayer = Rhino.DocObjects.Layer()
                    new_sublayer.Name = param_name
                    new_sublayer.ParentLayerId = sc.doc.Layers[parent_layer_index].Id
                    sc.doc.Layers.Add(new_sublayer)

                target_layer = sublayer_name

            # Clear existing geometry from target layer if requested
            if clear_existing:
                layer_objects = rs.ObjectsByLayer(target_layer)
                if layer_objects:
                    deleted_count = rs.DeleteObjects(layer_objects)
                    debug_log.append(f"Cleared {deleted_count} existing objects from layer '{target_layer}'")

            # Set current layer and get layer index using RhinoCommon
            previous_layer = rs.CurrentLayer()

            # Find the layer object directly using RhinoCommon
            layer_index = -1
            for i in range(sc.doc.Layers.Count):
                layer = sc.doc.Layers[i]
                if layer.FullPath == target_layer:
                    layer_index = i
                    break

            # If not found by FullPath, try by Name
            if layer_index == -1:
                for i in range(sc.doc.Layers.Count):
                    layer = sc.doc.Layers[i]
                    if layer.Name == target_layer:
                        layer_index = i
                        break

            debug_log.append(f"Previous layer: {previous_layer}")
            debug_log.append(f"Target layer: {target_layer}")
            debug_log.append(f"Found layer index: {layer_index}")

            if layer_index == -1:
                debug_log.append(f"ERROR: Could not find layer '{target_layer}' in document")
                baking_results[param_name] = {
                    "success": False,
                    "error": f"Layer '{target_layer}' not found in document"
                }
                continue

            # Set the current layer
            rs.CurrentLayer(target_layer)
            current_layer_name = rs.CurrentLayer()
            debug_log.append(f"Current layer after set: {current_layer_name}")

            # Bake geometry
            baked_ids = []
            geometry_types = []

            try:
                volatile_data = param_obj.VolatileData
                for i in range(volatile_data.PathCount):
                    path = volatile_data.get_Path(i)
                    branch = volatile_data.get_Branch(path)

                    for item in branch:
                        try:
                            actual_geom = item.Value if hasattr(item, 'Value') else item
                            if actual_geom:
                                geometry_types.append(type(actual_geom).__name__)

                                # Use smart conversion
                                converted_geom, orig_type, conv_type, success, error_msg = convert_geometry_to_base(actual_geom)

                                if success and converted_geom:
                                    # Create object attributes with specific layer
                                    attrs = Rhino.DocObjects.ObjectAttributes()
                                    attrs.LayerIndex = layer_index

                                    # Add geometry with attributes to specify layer
                                    obj_id = sc.doc.Objects.Add(converted_geom, attrs)
                                    if obj_id != System.Guid.Empty:
                                        baked_ids.append(str(obj_id))
                                        debug_log.append(f"Baked {orig_type} -> {conv_type}: {obj_id}")
                                else:
                                    debug_log.append(f"Skipped {orig_type}: {error_msg}")

                        except Exception as e:
                            debug_log.append(f"Error baking item: {str(e)}")
                            continue

                sc.doc.Views.Redraw()

                baking_results[param_name] = {
                    "success": True,
                    "baked_count": len(baked_ids),
                    "baked_ids": baked_ids,
                    "layer": target_layer,
                    "geometry_types": list(set(geometry_types))
                }
                total_baked += len(baked_ids)

            except Exception as e:
                import traceback
                baking_results[param_name] = {
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }

        return {
            "success": True,
            "message": f"Baked {total_baked} geometry objects to Rhino",
            "total_baked": total_baked,
            "layer_name": layer_name,
            "parameters_processed": baking_results,
            "debug_log": debug_log
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error baking geometry: {str(e)}",
            "traceback": traceback.format_exc()
        }


# ============================================================================
# CUSTOM SCRIPT EXECUTION TOOL
# ============================================================================

@gh_tool(
    name="execute_custom_python_script",
    description=(
        "Execute custom Python script in Rhino/Grasshopper environment with comprehensive debugging. "
        "Use this tool when you need to run custom Python code that leverages RhinoCommon and "
        "Grasshopper APIs directly.\n\n"
        "**Use Cases:**\n"
        "- Complex geometry operations not covered by existing tools\n"
        "- Custom batch processing of Grasshopper data\n"
        "- Advanced Rhino document manipulation\n"
        "- Custom analysis or calculations\n\n"
        "**Parameters:**\n"
        "- **script_code** (str): Python code to execute (supports RhinoCommon, Grasshopper APIs)\n"
        "- **script_description** (str): Brief description of what the script does\n"
        "- **return_variable** (str, optional): Name of variable to return from script scope\n\n"
        "**Available in Script Scope:**\n"
        "- `Rhino` - RhinoCommon library\n"
        "- `Grasshopper` - Grasshopper API\n"
        "- `rs` - rhinoscriptsyntax\n"
        "- `sc` - scriptcontext (access to Rhino document)\n"
        "- `ghenv` - Grasshopper environment\n"
        "- `math`, `System` - Standard libraries\n\n"
        "**Returns:**\n"
        "Dictionary with execution results, output, errors, and debug information."
    )
)
async def execute_custom_python_script(
    script_code: str,
    script_description: str,
    return_variable: str = None
) -> Dict[str, Any]:
    """
    Handler for custom script execution with debugging.
    """
    return call_bridge_api("/execute_custom_script", {
        "script_code": script_code,
        "script_description": script_description,
        "return_variable": return_variable
    })


@bridge_handler("/execute_custom_script")
def handle_execute_custom_script(data):
    """Bridge handler for custom script execution"""
    try:
        import clr
        clr.AddReference('Grasshopper')
        clr.AddReference('RhinoCommon')
        import Grasshopper
        import Rhino
        import rhinoscriptsyntax as rs
        import scriptcontext as sc
        import System
        import math
        import io
        import sys

        script_code = data.get('script_code', '')
        script_description = data.get('script_description', 'Custom script')
        return_variable = data.get('return_variable', None)

        if not script_code:
            return {
                "success": False,
                "error": "No script_code provided"
            }

        debug_log = []
        debug_log.append(f"Executing: {script_description}")
        debug_log.append(f"Script length: {len(script_code)} characters")
        debug_log.append(f"Script lines: {len(script_code.splitlines())}")

        # Capture stdout/stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured_output = io.StringIO()
        captured_errors = io.StringIO()

        try:
            sys.stdout = captured_output
            sys.stderr = captured_errors

            # Prepare execution environment
            exec_globals = {
                'Rhino': Rhino,
                'Grasshopper': Grasshopper,
                'rs': rs,
                'sc': sc,
                'System': System,
                'math': math,
                '__builtins__': __builtins__
            }

            exec_locals = {}

            # Execute script
            debug_log.append("Starting script execution...")
            exec(script_code, exec_globals, exec_locals)
            debug_log.append("Script execution completed successfully")

            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Get output
            output_text = captured_output.getvalue()
            error_text = captured_errors.getvalue()

            # Get return value if specified
            return_value = None
            return_value_type = None
            if return_variable and return_variable in exec_locals:
                return_value = exec_locals[return_variable]
                return_value_type = type(return_value).__name__
                debug_log.append(f"Return variable '{return_variable}' = {return_value_type}")

                # Convert to serializable format
                if isinstance(return_value, (list, tuple)):
                    return_value = [str(item) for item in return_value]
                elif not isinstance(return_value, (str, int, float, bool, dict)):
                    return_value = str(return_value)

            # Get all variables created in script
            created_variables = {
                k: {"type": type(v).__name__, "value": str(v)[:100]}
                for k, v in exec_locals.items()
                if not k.startswith('_')
            }

            result = {
                "success": True,
                "message": "Script executed successfully",
                "script_description": script_description,
                "output": output_text if output_text else None,
                "errors": error_text if error_text else None,
                "return_value": return_value,
                "return_value_type": return_value_type,
                "created_variables": created_variables,
                "debug_log": debug_log
            }

            # Redraw views if geometry was modified
            sc.doc.Views.Redraw()

            return result

        except Exception as e:
            import traceback

            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            output_text = captured_output.getvalue()
            error_text = captured_errors.getvalue()

            return {
                "success": False,
                "error": f"Script execution failed: {str(e)}",
                "traceback": traceback.format_exc(),
                "output": output_text if output_text else None,
                "errors": error_text if error_text else None,
                "debug_log": debug_log,
                "script_description": script_description
            }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error in script handler: {str(e)}",
            "traceback": traceback.format_exc()
        }


# ============================================================================
# WORKFLOW SUGGESTION TOOL
# ============================================================================

@gh_tool(
    name="suggest_gh_workflow",
    description=(
        "Get workflow suggestions based on file metadata and user goals. "
        "Analyzes available Grasshopper files and their relationships to suggest "
        "optimal workflows for achieving specific design or analysis goals.\n\n"
        "**Use Cases:**\n"
        "- User wants to know which files to use for a complete workflow\n"
        "- Understanding file dependencies and proper execution order\n"
        "- Learning what inputs are needed for a workflow\n"
        "- Finding workflows by category or tags\n\n"
        "**Parameters:**\n"
        "- **goal** (str, optional): User's goal (e.g., 'structural design', 'complete roof')\n"
        "- **category** (str, optional): Filter by category (e.g., 'structural', 'geometry')\n"
        "- **workflow_id** (str, optional): Get specific workflow by ID\n\n"
        "**Returns:**\n"
        "Suggested workflows with step-by-step instructions, required files, inputs, and outputs."
    )
)
async def suggest_gh_workflow(
    goal: str = "",
    category: str = "",
    workflow_id: str = ""
) -> Dict[str, Any]:
    """
    Get workflow suggestions based on metadata.
    """
    return call_bridge_api("/suggest_workflow", {
        "goal": goal,
        "category": category,
        "workflow_id": workflow_id
    })


@bridge_handler("/suggest_workflow")
def handle_suggest_workflow(data):
    """Bridge handler for workflow suggestions"""
    try:
        import os
        import json

        goal = data.get('goal', '').lower()
        category = data.get('category', '').lower()
        workflow_id = data.get('workflow_id', '')

        # Get the library path and load metadata
        script_dir = os.path.dirname(os.path.abspath(__file__))
        library_path = os.path.join(script_dir, "Grasshopper File Library")
        metadata_path = os.path.join(library_path, "metadata.json")

        if not os.path.exists(metadata_path):
            return {
                "success": False,
                "error": "metadata.json not found in Grasshopper File Library",
                "suggestion": "Create a metadata.json file to enable workflow suggestions"
            }

        # Load metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        workflows = metadata.get('workflows', [])
        files = metadata.get('files', [])

        if not workflows:
            return {
                "success": True,
                "message": "No workflows defined in metadata",
                "available_files": [f['filename'] for f in files],
                "suggestion": "Add workflow definitions to metadata.json"
            }

        # Filter workflows
        suggested_workflows = []

        for workflow in workflows:
            # Filter by workflow_id if specified
            if workflow_id and workflow.get('id') != workflow_id:
                continue

            # Filter by category
            if category:
                # Check if any files in workflow match category
                workflow_categories = set()
                for step in workflow.get('steps', []):
                    step_file = step.get('file')
                    file_meta = next((f for f in files if f['filename'] == step_file), None)
                    if file_meta:
                        workflow_categories.add(file_meta.get('category', ''))

                if category not in workflow_categories:
                    continue

            # Filter by goal (search in name, description, tags)
            if goal:
                searchable_text = (
                    workflow.get('name', '') + ' ' +
                    workflow.get('description', '')
                ).lower()

                # Also check file tags
                for step in workflow.get('steps', []):
                    step_file = step.get('file')
                    file_meta = next((f for f in files if f['filename'] == step_file), None)
                    if file_meta:
                        searchable_text += ' ' + ' '.join(file_meta.get('tags', []))

                if goal not in searchable_text:
                    continue

            suggested_workflows.append(workflow)

        # If no workflows matched filters, return all workflows
        if not suggested_workflows and not workflow_id:
            suggested_workflows = workflows

        return {
            "success": True,
            "workflows": suggested_workflows,
            "workflow_count": len(suggested_workflows),
            "library_info": metadata.get('library_info', {}),
            "message": f"Found {len(suggested_workflows)} workflow(s)"
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Error suggesting workflows: {str(e)}",
            "traceback": traceback.format_exc()
        }


# All tools are now automatically registered using the @gh_tool decorator
# Summary of available tools:
#
# FILE MANAGEMENT (5 tools):
# 1. list_gh_files - List available .gh files in library
# 2. open_gh_file - Open .gh files (auto-launches Grasshopper if needed)
# 3. open_all_gh_files - Open all .gh files at once (NEW!)
# 4. get_active_gh_files - Get currently open files
# 5. close_gh_file - Close specific files
#
# EML PARAMETER TOOLS (4 tools):
# 6. list_eml_parameters - Discover all eml_ prefixed parameters
# 7. get_eml_parameter_value - Extract value from eml_ parameter
# 8. set_eml_parameter_value - Set value for eml_ parameter
# 9. suggest_eml_connections - Suggest connections between eml_ parameters
#
# CROSS-FILE WORKFLOW TOOLS (2 tools - NEW!):
# 10. transfer_eml_geometry_between_files - Direct geometry transfer without baking
# 11. execute_eml_workflow - Automated multi-file workflow orchestration
#
# TRADITIONAL GRASSHOPPER TOOLS (16 tools):
# 12. list_grasshopper_sliders - Basic slider listing
# 13. set_grasshopper_slider - Set individual slider value
# 14. get_grasshopper_overview - File overview and component counts
# 15. analyze_grasshopper_sliders - Detailed slider analysis with connections
# 16. get_grasshopper_components - Complete component mapping
# 17. set_multiple_grasshopper_sliders - Batch slider updates
# 18. debug_grasshopper_state - Comprehensive debugging information
# 19. list_grasshopper_valuelist_components - List ValueList components and options
# 20. set_grasshopper_valuelist_selection - Change ValueList selections
# 21. list_grasshopper_panels - List Panel components and text content
# 22. set_grasshopper_panel_text - Update Panel text content
# 23. get_grasshopper_panel_data - Extract data and values from Panels
# 24. analyze_grasshopper_inputs_with_context - Enhanced input analysis with groups and annotations
# 25. analyze_grasshopper_outputs_with_context - Enhanced output analysis with groups and annotations
# 26. set_grasshopper_geometry_input - Set Rhino geometry to Grasshopper parameter
# 27. extract_grasshopper_geometry_output - Extract and optionally bake Grasshopper geometry output
#
# USER-CONTROLLED TOOLS (2 tools):
# 28. bake_grasshopper_geometry_to_rhino - Explicit baking with user confirmation and layer control
# 29. execute_custom_python_script - Custom script execution with comprehensive debugging
#
# WORKFLOW TOOLS (1 tool - NEW!):
# 30. suggest_gh_workflow - Intelligent workflow suggestions based on metadata
#
# TOTAL: 30 tools (5 file management + 4 eml + 2 workflow + 16 traditional + 2 user-controlled + 1 workflow suggestion)