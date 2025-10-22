"""
Rhino 3D Tools

This module contains all Rhino-specific MCP tools that communicate with the
Rhino bridge server to execute operations within Rhino 3D.

Tools are automatically registered using the @rhino_tool decorator.
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Import bridge_client from MCP directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'MCP'))
from bridge_client import call_bridge_api

# Import the decorator system
try:
    from .tool_registry import rhino_tool, bridge_handler
except ImportError:
    # Fallback for direct import
    from tool_registry import rhino_tool, bridge_handler

# Get DEBUG_MODE from environment
DEBUG_MODE = False
try:
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

def filter_debug_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Filter response based on DEBUG_MODE to save tokens"""
    if DEBUG_MODE:
        return response

    filtered = {}
    essential_keys = [
        'success', 'error', 'message', 'warning',
        'line_id', 'point_count', 'truss_type', 'member_count',
        'version', 'document_name', 'unit_system'
    ]

    for key in essential_keys:
        if key in response:
            filtered[key] = response[key]

    # Include debug info only on errors
    if not response.get('success', True):
        if 'traceback' in response:
            filtered['traceback'] = response['traceback']

    # Copy unhandled keys
    for key, value in response.items():
        if key not in essential_keys and key not in ['traceback']:
            filtered[key] = value

    return filtered

@rhino_tool(
    name="draw_line_rhino",
    description=(
        "Draw a line in Rhino 3D space between two points. "
        "This tool creates a line object in the current Rhino document. "
        "Coordinates are specified in Rhino's current units (usually millimeters or inches). "
        "\n\n**Parameters:**\n"
        "- **start_x** (float): X-coordinate of the line start point\n"
        "- **start_y** (float): Y-coordinate of the line start point\n" 
        "- **start_z** (float): Z-coordinate of the line start point\n"
        "- **end_x** (float): X-coordinate of the line end point\n"
        "- **end_y** (float): Y-coordinate of the line end point\n"
        "- **end_z** (float): Z-coordinate of the line end point\n"
        "\n**Returns:**\n"
        "Dictionary containing the line ID and status information."
    )
)
async def draw_line_rhino(
    start_x: float, 
    start_y: float, 
    start_z: float, 
    end_x: float, 
    end_y: float, 
    end_z: float
) -> Dict[str, Any]:
    """
    Draw a line in Rhino between two 3D points via HTTP bridge.
    
    Args:
        start_x: X-coordinate of start point
        start_y: Y-coordinate of start point  
        start_z: Z-coordinate of start point
        end_x: X-coordinate of end point
        end_y: Y-coordinate of end point
        end_z: Z-coordinate of end point
        
    Returns:
        Dict containing line creation results
    """
    
    request_data = {
        "start_x": start_x,
        "start_y": start_y,
        "start_z": start_z,
        "end_x": end_x,
        "end_y": end_y,
        "end_z": end_z
    }
    
    return call_bridge_api("/draw_line", request_data)

@bridge_handler("/draw_line")
def handle_draw_line(data):
    """Bridge handler for line drawing requests"""
    try:
        # Import Rhino modules here since this runs inside Rhino
        import rhinoscriptsyntax as rs
        
        # Extract coordinates
        start_x = float(data.get('start_x', 0))
        start_y = float(data.get('start_y', 0))
        start_z = float(data.get('start_z', 0))
        end_x = float(data.get('end_x', 0))
        end_y = float(data.get('end_y', 0))
        end_z = float(data.get('end_z', 0))
        
        # Create the line in Rhino
        start_point = [start_x, start_y, start_z]
        end_point = [end_x, end_y, end_z]
        
        line_id = rs.AddLine(start_point, end_point)
        
        if line_id:
            line_length = rs.CurveLength(line_id)
            result = {
                "success": True,
                "line_id": str(line_id),
                "start_point": start_point,
                "end_point": end_point,
                "length": line_length,
                "message": f"Line created successfully with length {line_length:.2f}"
            }
            return filter_debug_response(result)
        else:
            result = {
                "success": False,
                "error": "Failed to create line in Rhino",
                "line_id": None
            }
            return filter_debug_response(result)
    except ImportError:
        result = {
            "success": False,
            "error": "Rhino is not available",
            "line_id": None
        }
        return filter_debug_response(result)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error drawing line: {str(e)}",
            "line_id": None
        }
        return filter_debug_response(result)

@rhino_tool(
    name="get_rhino_info",
    description=(
        "Get information about the current Rhino session and document. "
        "This tool provides details about the Rhino version, document units, "
        "and current session status."
    )
)
async def get_rhino_info() -> Dict[str, Any]:
    """
    Get information about the current Rhino session via HTTP bridge.
    
    Returns:
        Dict containing Rhino session information
    """
    
    return call_bridge_api("/get_rhino_info", {})

@bridge_handler("/get_rhino_info")
def handle_get_rhino_info(data):
    """Bridge handler for get Rhino info requests"""
    try:
        # Import Rhino modules here since this runs inside Rhino
        import rhinoscriptsyntax as rs
        
        info = {
            "rhino_available": True,
            "grasshopper_available": False,  # Will be updated if GH is available
        }
        
        # Try to get Grasshopper availability
        try:
            import ghpython
            import grasshopper as gh
            info["grasshopper_available"] = True
        except ImportError:
            pass
        
        # Try to get Rhino-specific information
        try:
            info["document_units"] = rs.UnitSystemName(rs.UnitSystem())
            info["object_count"] = rs.ObjectCount()
            info["is_command_running"] = rs.IsCommand()
        except Exception as e:
            info["rhino_error"] = str(e)
        
        result = {
            "success": True,
            "info": info,
            "message": "Rhino information retrieved successfully"
        }
        return filter_debug_response(result)
    except ImportError:
        result = {
            "success": False,
            "error": "Rhino is not available",
            "info": {}
        }
        return filter_debug_response(result)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error getting Rhino info: {str(e)}",
            "info": {}
        }
        return filter_debug_response(result)

@rhino_tool(
    name="typical_roof_truss_generator",
    description=(
        "Generate a typical roof truss structure in Rhino based on an upper chord line. "
        "This tool creates a complete truss with top chord, bottom chord, and web members.\n\n"
        "**IMPORTANT:** This tool requires explicit user input. Do NOT call with default values. "
        "Always ask the user to specify all required parameters before calling this tool.\n\n"
        "**Required User Input (ASK USER FOR THESE):**\n"
        "1. Upper chord line coordinates (start and end points)\n"
        "2. Truss depth (vertical distance from top to bottom chord)\n"
        "3. Number of divisions/bays\n"
        "4. Truss type (optional - defaults to Pratt)\n\n"
        "**Available Truss Types:**\n"
        "- **Pratt**: Vertical members with diagonals in compression\n"
        "- **Warren**: No verticals, alternating diagonal members\n"
        "- **Vierendeel**: Rectangular panels with moment connections\n"
        "- **Brown**: Similar to Pratt but with different diagonal orientation\n"
        "- **Howe**: Vertical members with diagonals in tension\n"
        "- **Onedir**: Single direction diagonals only\n\n"
        "**Parameters:**\n"
        "- **upper_line_start_x** (float): X-coordinate of upper line start point (ASK USER)\n"
        "- **upper_line_start_y** (float): Y-coordinate of upper line start point (ASK USER)\n"
        "- **upper_line_start_z** (float): Z-coordinate of upper line start point (ASK USER)\n"
        "- **upper_line_end_x** (float): X-coordinate of upper line end point (ASK USER)\n"
        "- **upper_line_end_y** (float): Y-coordinate of upper line end point (ASK USER)\n"
        "- **upper_line_end_z** (float): Z-coordinate of upper line end point (ASK USER)\n"
        "- **truss_depth** (float): Vertical depth of truss (ASK USER)\n"
        "- **num_divisions** (int): Number of truss divisions/bays (ASK USER, minimum 2)\n"
        "- **truss_type** (str): Type of truss (Pratt, Warren, Vierendeel, Brown, Howe, Onedir)\n"
        "- **clear_previous** (bool): Clear previously generated truss objects (default: true)\n"
        "- **truss_plane_direction** (str): Direction of truss plane (default: 'perpendicular')\n"
        "\n**Returns:**\n"
        "Dictionary containing truss generation results, member IDs, and geometry information."
    )
)
async def typical_roof_truss_generator(
    upper_line_start_x: float,
    upper_line_start_y: float,
    upper_line_start_z: float,
    upper_line_end_x: float,
    upper_line_end_y: float,
    upper_line_end_z: float,
    truss_depth: float,
    num_divisions: int,
    truss_type: str = "Pratt",
    clear_previous: bool = True,
    truss_plane_direction: str = "perpendicular"
) -> Dict[str, Any]:
    """
    Generate a typical roof truss structure based on an upper chord line.
    
    IMPORTANT: This tool requires the user to explicitly specify the upper chord line coordinates.
    Do NOT call this tool with default values - always ask the user to define:
    1. The upper chord line (start and end points)  
    2. Truss depth
    3. Number of divisions
    4. Truss type (optional)
    
    Available truss types:
    - Pratt: Vertical members with diagonals in compression
    - Warren: No verticals, alternating diagonal members
    - Vierendeel: Rectangular panels with moment connections
    - Brown: Similar to Pratt but with different diagonal orientation
    - Howe: Vertical members with diagonals in tension
    - Onedir: Single direction diagonals only
    
    Args:
        upper_line_start_x: X-coordinate of upper line start point (REQUIRED from user)
        upper_line_start_y: Y-coordinate of upper line start point (REQUIRED from user)
        upper_line_start_z: Z-coordinate of upper line start point (REQUIRED from user)
        upper_line_end_x: X-coordinate of upper line end point (REQUIRED from user)
        upper_line_end_y: Y-coordinate of upper line end point (REQUIRED from user)
        upper_line_end_z: Z-coordinate of upper line end point (REQUIRED from user)
        truss_depth: Vertical depth of the truss (REQUIRED from user)
        num_divisions: Number of truss divisions/bays (REQUIRED from user, minimum 2)
        truss_type: Type of truss (Pratt, Warren, Vierendeel, Brown, Howe, Onedir)
        clear_previous: Whether to clear previously generated truss objects
        truss_plane_direction: Direction of truss plane ("perpendicular" for auto-perpendicular)
        
    Returns:
        Dict containing truss generation results
    """
    
    request_data = {
        "upper_line_start_x": upper_line_start_x,
        "upper_line_start_y": upper_line_start_y,
        "upper_line_start_z": upper_line_start_z,
        "upper_line_end_x": upper_line_end_x,
        "upper_line_end_y": upper_line_end_y,
        "upper_line_end_z": upper_line_end_z,
        "truss_depth": truss_depth,
        "num_divisions": num_divisions,
        "truss_type": truss_type,
        "clear_previous": clear_previous,
        "truss_plane_direction": truss_plane_direction
    }
    
    return call_bridge_api("/generate_truss", request_data)

@bridge_handler("/generate_truss")
def handle_generate_truss(data):
    """Bridge handler for truss generation requests"""
    try:
        # Import Rhino modules here since this runs inside Rhino
        import rhinoscriptsyntax as rs
        import math
        
        # Extract truss parameters
        upper_line_start_x = float(data.get('upper_line_start_x', 0))
        upper_line_start_y = float(data.get('upper_line_start_y', 0))
        upper_line_start_z = float(data.get('upper_line_start_z', 0))
        upper_line_end_x = float(data.get('upper_line_end_x', 10))
        upper_line_end_y = float(data.get('upper_line_end_y', 0))
        upper_line_end_z = float(data.get('upper_line_end_z', 0))
        truss_depth = float(data.get('truss_depth', 2))
        num_divisions = int(data.get('num_divisions', 4))
        truss_type = data.get('truss_type', 'Pratt')
        clear_previous = data.get('clear_previous', True)
        truss_plane_direction = data.get('truss_plane_direction', 'perpendicular')
        
        # Clear previous truss if requested
        if clear_previous:
            clear_previous_trusses()
        
        # Generate truss geometry
        truss_members = create_truss_geometry(
            [upper_line_start_x, upper_line_start_y, upper_line_start_z],
            [upper_line_end_x, upper_line_end_y, upper_line_end_z],
            truss_depth,
            num_divisions,
            truss_type,
            truss_plane_direction
        )
        
        if truss_members:
            result = {
                "success": True,
                "truss_members": truss_members,
                "num_members": len(truss_members),
                "truss_depth": truss_depth,
                "num_divisions": num_divisions,
                "truss_type": truss_type,
                "message": f"{truss_type} truss created successfully with {len(truss_members)} members"
            }
            return filter_debug_response(result)
        else:
            result = {
                "success": False,
                "error": "Failed to create truss in Rhino",
                "truss_members": []
            }
            return filter_debug_response(result)
    except ImportError:
        result = {
            "success": False,
            "error": "Rhino is not available",
            "truss_members": []
        }
        return filter_debug_response(result)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error generating truss: {str(e)}",
            "truss_members": []
        }
        return filter_debug_response(result)

def clear_previous_trusses():
    """Clear previously generated truss objects"""
    try:
        import rhinoscriptsyntax as rs
        # Get all objects with "truss" user text
        all_objects = rs.AllObjects()
        if all_objects:
            truss_objects = []
            for obj_id in all_objects:
                user_text = rs.GetUserText(obj_id, "object_type")
                if user_text == "truss_member":
                    truss_objects.append(obj_id)
            
            if truss_objects:
                rs.DeleteObjects(truss_objects)
                print(f"Cleared {len(truss_objects)} previous truss members")
    except Exception as e:
        print(f"Error clearing previous trusses: {str(e)}")

def create_truss_geometry(start_point, end_point, depth, divisions, truss_type, plane_direction):
    """Create the actual truss geometry in Rhino"""
    try:
        import rhinoscriptsyntax as rs
        import math
        
        truss_members = []
        
        # Vector from start to end of upper chord
        upper_vector = [end_point[0] - start_point[0], 
                      end_point[1] - start_point[1], 
                      end_point[2] - start_point[2]]
        
        # Length of upper chord
        upper_length = math.sqrt(upper_vector[0]**2 + upper_vector[1]**2 + upper_vector[2]**2)
        
        # Normalize upper vector
        if upper_length > 0:
            upper_unit = [v / upper_length for v in upper_vector]
        else:
            upper_unit = [1, 0, 0]
        
        # Calculate perpendicular direction for truss depth
        depth_vector = [0, 0, -depth]  # Truss extends downward
        
        # Generate division points along upper chord
        division_points_top = []
        division_points_bottom = []
        
        for i in range(divisions + 1):
            t = i / divisions
            
            # Top chord points
            top_point = [
                start_point[0] + t * upper_vector[0],
                start_point[1] + t * upper_vector[1],
                start_point[2] + t * upper_vector[2]
            ]
            division_points_top.append(top_point)
            
            # Bottom chord points (offset by depth)
            bottom_point = [
                top_point[0] + depth_vector[0],
                top_point[1] + depth_vector[1],
                top_point[2] + depth_vector[2]
            ]
            division_points_bottom.append(bottom_point)
        
        # Create top chord segments
        for i in range(divisions):
            line_id = rs.AddLine(division_points_top[i], division_points_top[i + 1])
            if line_id:
                rs.SetUserText(line_id, "object_type", "truss_member")
                rs.SetUserText(line_id, "member_type", "top_chord")
                truss_members.append({
                    "id": str(line_id),
                    "type": "top_chord",
                    "start": division_points_top[i],
                    "end": division_points_top[i + 1]
                })
        
        # Create bottom chord segments
        for i in range(divisions):
            line_id = rs.AddLine(division_points_bottom[i], division_points_bottom[i + 1])
            if line_id:
                rs.SetUserText(line_id, "object_type", "truss_member")
                rs.SetUserText(line_id, "member_type", "bottom_chord")
                truss_members.append({
                    "id": str(line_id),
                    "type": "bottom_chord",
                    "start": division_points_bottom[i],
                    "end": division_points_bottom[i + 1]
                })
        
        # Create web members based on truss type
        if truss_type.lower() == "pratt":
            # Pratt: Verticals + diagonals in compression
            for i in range(divisions + 1):
                line_id = rs.AddLine(division_points_top[i], division_points_bottom[i])
                if line_id:
                    rs.SetUserText(line_id, "object_type", "truss_member")
                    rs.SetUserText(line_id, "member_type", "vertical")
                    truss_members.append({
                        "id": str(line_id),
                        "type": "vertical",
                        "start": division_points_top[i],
                        "end": division_points_bottom[i]
                    })
            
            for i in range(divisions):
                if i % 2 == 0:  # Alternate diagonals
                    line_id = rs.AddLine(division_points_bottom[i], division_points_top[i + 1])
                else:
                    line_id = rs.AddLine(division_points_top[i], division_points_bottom[i + 1])
                
                if line_id:
                    rs.SetUserText(line_id, "object_type", "truss_member")
                    rs.SetUserText(line_id, "member_type", "diagonal")
                    truss_members.append({
                        "id": str(line_id),
                        "type": "diagonal",
                        "start": division_points_bottom[i] if i % 2 == 0 else division_points_top[i],
                        "end": division_points_top[i + 1] if i % 2 == 0 else division_points_bottom[i + 1]
                    })
        
        elif truss_type.lower() == "warren":
            # Warren: No verticals, alternating diagonals
            for i in range(divisions):
                if i % 2 == 0:
                    line_id = rs.AddLine(division_points_bottom[i], division_points_top[i + 1])
                    start_pt, end_pt = division_points_bottom[i], division_points_top[i + 1]
                else:
                    line_id = rs.AddLine(division_points_top[i], division_points_bottom[i + 1])
                    start_pt, end_pt = division_points_top[i], division_points_bottom[i + 1]
                
                if line_id:
                    rs.SetUserText(line_id, "object_type", "truss_member")
                    rs.SetUserText(line_id, "member_type", "diagonal")
                    truss_members.append({
                        "id": str(line_id),
                        "type": "diagonal",
                        "start": start_pt,
                        "end": end_pt
                    })
        
        elif truss_type.lower() == "vierendeel":
            # Vierendeel: Only verticals, no diagonals (moment frame)
            for i in range(divisions + 1):
                line_id = rs.AddLine(division_points_top[i], division_points_bottom[i])
                if line_id:
                    rs.SetUserText(line_id, "object_type", "truss_member")
                    rs.SetUserText(line_id, "member_type", "vertical")
                    truss_members.append({
                        "id": str(line_id),
                        "type": "vertical",
                        "start": division_points_top[i],
                        "end": division_points_bottom[i]
                    })
        
        elif truss_type.lower() == "howe":
            # Howe: Verticals + diagonals in tension (opposite of Pratt)
            for i in range(divisions + 1):
                line_id = rs.AddLine(division_points_top[i], division_points_bottom[i])
                if line_id:
                    rs.SetUserText(line_id, "object_type", "truss_member")
                    rs.SetUserText(line_id, "member_type", "vertical")
                    truss_members.append({
                        "id": str(line_id),
                        "type": "vertical",
                        "start": division_points_top[i],
                        "end": division_points_bottom[i]
                    })
            
            for i in range(divisions):
                if i % 2 == 0:
                    line_id = rs.AddLine(division_points_top[i], division_points_bottom[i + 1])
                else:
                    line_id = rs.AddLine(division_points_bottom[i], division_points_top[i + 1])
                
                if line_id:
                    rs.SetUserText(line_id, "object_type", "truss_member")
                    rs.SetUserText(line_id, "member_type", "diagonal")
                    truss_members.append({
                        "id": str(line_id),
                        "type": "diagonal",
                        "start": division_points_top[i] if i % 2 == 0 else division_points_bottom[i],
                        "end": division_points_bottom[i + 1] if i % 2 == 0 else division_points_top[i + 1]
                    })
        
        elif truss_type.lower() == "brown":
            # Brown: Similar to Pratt with different diagonal pattern
            for i in range(divisions + 1):
                line_id = rs.AddLine(division_points_top[i], division_points_bottom[i])
                if line_id:
                    rs.SetUserText(line_id, "object_type", "truss_member")
                    rs.SetUserText(line_id, "member_type", "vertical")
                    truss_members.append({
                        "id": str(line_id),
                        "type": "vertical",
                        "start": division_points_top[i],
                        "end": division_points_bottom[i]
                    })
            
            for i in range(divisions):
                # Brown pattern: both diagonals in each bay
                line_id1 = rs.AddLine(division_points_bottom[i], division_points_top[i + 1])
                line_id2 = rs.AddLine(division_points_top[i], division_points_bottom[i + 1])
                
                for line_id, start_pt, end_pt in [
                    (line_id1, division_points_bottom[i], division_points_top[i + 1]),
                    (line_id2, division_points_top[i], division_points_bottom[i + 1])
                ]:
                    if line_id:
                        rs.SetUserText(line_id, "object_type", "truss_member")
                        rs.SetUserText(line_id, "member_type", "diagonal")
                        truss_members.append({
                            "id": str(line_id),
                            "type": "diagonal",
                            "start": start_pt,
                            "end": end_pt
                        })
        
        elif truss_type.lower() == "onedir":
            # Onedir: Single direction diagonals only
            for i in range(divisions):
                line_id = rs.AddLine(division_points_bottom[i], division_points_top[i + 1])
                if line_id:
                    rs.SetUserText(line_id, "object_type", "truss_member")
                    rs.SetUserText(line_id, "member_type", "diagonal")
                    truss_members.append({
                        "id": str(line_id),
                        "type": "diagonal",
                        "start": division_points_bottom[i],
                        "end": division_points_top[i + 1]
                    })
        
        else:
            # Default to Pratt if unknown type
            for i in range(divisions + 1):
                line_id = rs.AddLine(division_points_top[i], division_points_bottom[i])
                if line_id:
                    rs.SetUserText(line_id, "object_type", "truss_member")
                    rs.SetUserText(line_id, "member_type", "vertical")
                    truss_members.append({
                        "id": str(line_id),
                        "type": "vertical",
                        "start": division_points_top[i],
                        "end": division_points_bottom[i]
                    })
            
            for i in range(divisions):
                if i % 2 == 0:
                    line_id = rs.AddLine(division_points_bottom[i], division_points_top[i + 1])
                else:
                    line_id = rs.AddLine(division_points_top[i], division_points_bottom[i + 1])
                
                if line_id:
                    rs.SetUserText(line_id, "object_type", "truss_member")
                    rs.SetUserText(line_id, "member_type", "diagonal")
                    truss_members.append({
                        "id": str(line_id),
                        "type": "diagonal",
                        "start": division_points_bottom[i] if i % 2 == 0 else division_points_top[i],
                        "end": division_points_top[i + 1] if i % 2 == 0 else division_points_bottom[i + 1]
                    })
        
        return truss_members
        
    except Exception as e:
        print(f"Error in create_truss_geometry: {str(e)}")
        return []

@rhino_tool(
    name="get_selected_rhino_objects",
    description=(
        "Get information about currently selected objects in Rhino. This tool retrieves "
        "details about user-selected geometry including object types (curves, surfaces, points, etc.) "
        "and their IDs. Useful for understanding what the user has selected before feeding to Grasshopper.\n\n"
        "**Returns:**\n"
        "Dictionary containing list of selected objects with their types and IDs."
    )
)
async def get_selected_rhino_objects() -> Dict[str, Any]:
    """
    Get information about selected objects in Rhino via HTTP bridge.

    Returns:
        Dict containing selected object information
    """

    return call_bridge_api("/get_selected_objects", {})

@bridge_handler("/get_selected_objects")
def handle_get_selected_objects(data):
    """Bridge handler for getting selected objects"""
    try:
        import rhinoscriptsyntax as rs

        selected_ids = rs.SelectedObjects()
        if not selected_ids:
            result = {
                "success": True,
                "selected_objects": [],
                "count": 0,
                "message": "No objects currently selected in Rhino"
            }
            return filter_debug_response(result)

        objects_info = []
        for obj_id in selected_ids:
            obj_type = rs.ObjectType(obj_id)
            obj_info = {
                "id": str(obj_id),
                "type": obj_type,
                "type_name": "",
                "layer": rs.ObjectLayer(obj_id),
                "name": rs.ObjectName(obj_id) or "Unnamed"
            }

            # Get friendly type name
            if obj_type == 4:  # Curve
                obj_info["type_name"] = "Curve"
                obj_info["is_closed"] = rs.IsCurveClosed(obj_id)
                obj_info["degree"] = rs.CurveDegree(obj_id)
            elif obj_type == 8 or obj_type == 16:  # Surface or Polysurface
                obj_info["type_name"] = "Surface/Brep"
                obj_info["is_closed"] = rs.IsPolysurfaceClosed(obj_id)
            elif obj_type == 1:  # Point
                obj_info["type_name"] = "Point"
                point = rs.PointCoordinates(obj_id)
                obj_info["coordinates"] = [point.X, point.Y, point.Z]
            elif obj_type == 32:  # Mesh
                obj_info["type_name"] = "Mesh"
            else:
                obj_info["type_name"] = f"Type_{obj_type}"

            objects_info.append(obj_info)

        result = {
            "success": True,
            "selected_objects": objects_info,
            "count": len(objects_info),
            "message": f"Found {len(objects_info)} selected object(s)"
        }
        return filter_debug_response(result)

    except ImportError:
        result = {
            "success": False,
            "error": "Rhino is not available"
        }
        return filter_debug_response(result)
    except Exception as e:
        result = {
            "success": False,
            "error": f"Error getting selected objects: {str(e)}"
        }
        return filter_debug_response(result)

@rhino_tool(
    name="get_rhino_object_geometry",
    description=(
        "Extract detailed geometry data from a Rhino object by its ID. This retrieves "
        "the actual geometric data (points, control points, etc.) that can be used to "
        "transfer geometry to Grasshopper.\n\n"
        "**Parameters:**\n"
        "- **object_id** (str): The GUID/ID of the Rhino object\n"
        "\n**Returns:**\n"
        "Dictionary containing detailed geometry data including points and curve/surface information."
    )
)
async def get_rhino_object_geometry(object_id: str) -> Dict[str, Any]:
    """
    Get detailed geometry data from a Rhino object via HTTP bridge.

    Args:
        object_id: GUID/ID of the Rhino object

    Returns:
        Dict containing geometry data
    """

    request_data = {"object_id": object_id}

    return call_bridge_api("/get_object_geometry", request_data)

@bridge_handler("/get_object_geometry")
def handle_get_object_geometry(data):
    """Bridge handler for getting object geometry"""
    try:
        import rhinoscriptsyntax as rs
        import Rhino
        import scriptcontext as sc

        object_id = data.get('object_id', '')
        if not object_id:
            result = {
                "success": False,
                "error": "No object_id provided"
            }
            return filter_debug_response(result)

        # Convert string to GUID
        try:
            import System
            guid = System.Guid(object_id)
        except:
            result = {
                "success": False,
                "error": f"Invalid object_id format: {object_id}"
            }
            return filter_debug_response(result)

        # Check if object exists
        if not rs.IsObject(guid):
            result = {
                "success": False,
                "error": f"Object with ID {object_id} not found"
            }
            return filter_debug_response(result)

        obj_type = rs.ObjectType(guid)
        geometry_data = {
            "id": object_id,
            "type": obj_type,
            "type_name": "",
            "data": {}
        }

        # Get the actual Rhino geometry object
        rhino_obj = sc.doc.Objects.FindId(guid)
        if rhino_obj:
            geom = rhino_obj.Geometry

            if obj_type == 4:  # Curve
                geometry_data["type_name"] = "Curve"
                curve = geom

                # Get control points
                if hasattr(curve, 'Points') and curve.Points:
                    control_points = []
                    for i in range(curve.Points.Count):
                        pt = curve.Points[i]
                        control_points.append({
                            "x": float(pt.Location.X),
                            "y": float(pt.Location.Y),
                            "z": float(pt.Location.Z)
                        })
                    geometry_data["data"]["control_points"] = control_points

                # Get curve properties
                geometry_data["data"]["degree"] = curve.Degree if hasattr(curve, 'Degree') else None
                geometry_data["data"]["is_closed"] = rs.IsCurveClosed(guid)
                geometry_data["data"]["domain_start"] = float(curve.Domain.T0)
                geometry_data["data"]["domain_end"] = float(curve.Domain.T1)

                # Sample points along curve
                sample_points = []
                for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
                    param = curve.Domain.ParameterAt(t)
                    pt = curve.PointAt(param)
                    sample_points.append({
                        "x": float(pt.X),
                        "y": float(pt.Y),
                        "z": float(pt.Z),
                        "t": t
                    })
                geometry_data["data"]["sample_points"] = sample_points

            elif obj_type == 1:  # Point
                geometry_data["type_name"] = "Point"
                point = rs.PointCoordinates(guid)
                geometry_data["data"]["coordinates"] = {
                    "x": float(point.X),
                    "y": float(point.Y),
                    "z": float(point.Z)
                }

            elif obj_type in [8, 16]:  # Surface or Polysurface
                geometry_data["type_name"] = "Surface/Brep"
                geometry_data["data"]["is_closed"] = rs.IsPolysurfaceClosed(guid)

                # Get bounding box
                bbox = rs.BoundingBox(guid)
                if bbox:
                    geometry_data["data"]["bounding_box"] = [
                        {"x": float(pt.X), "y": float(pt.Y), "z": float(pt.Z)}
                        for pt in bbox
                    ]

        result = {
            "success": True,
            "geometry": geometry_data,
            "message": f"Retrieved geometry data for {geometry_data['type_name']}"
        }
        return filter_debug_response(result)

    except ImportError as e:
        result = {
            "success": False,
            "error": f"Rhino is not available: {str(e)}"
        }
        return filter_debug_response(result)
    except Exception as e:
        import traceback
        result = {
            "success": False,
            "error": f"Error getting object geometry: {str(e)}",
            "traceback": traceback.format_exc()
        }
        return filter_debug_response(result)

# All tools are now automatically registered using the @rhino_tool decorator
# Simply add @rhino_tool decorator to any new function and it will be available in MCP
#
# New tools added:
# - get_selected_rhino_objects - Get currently selected objects
# - get_rhino_object_geometry - Extract detailed geometry data