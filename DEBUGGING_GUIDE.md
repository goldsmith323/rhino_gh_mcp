# Debugging Guide

This guide explains the debugging features of the MCP server to help diagnose and fix issues quickly.

## Overview

The debugging system operates across three layers:
1. **Bridge Client** (`MCP/bridge_client.py`) - HTTP communication error reporting
2. **Bridge Server** (`Rhino/rhino_bridge_server.py`) - Server-side error handling
3. **Handler Decorator** (`Tools/tool_registry.py`) - Handler execution monitoring

## Error Information

### 1. Bridge Client Errors (MCP Side)

When a tool call fails, you'll now receive detailed error information including:

#### Connection Errors
```json
{
  "success": false,
  "error": "Cannot connect to Rhino Bridge Server at http://localhost:8080...",
  "error_type": "ConnectionError",
  "endpoint": "/analyze_inputs_context",
  "bridge_url": "http://localhost:8080"
}
```

**Common causes:**
- Rhino bridge server is not running
- Wrong host/port configuration
- Firewall blocking the connection

**How to fix:**
- Run the bridge server in Rhino using `start_rhino_bridge.py`
- Check `RHINO_BRIDGE_HOST` and `RHINO_BRIDGE_PORT` environment variables
- Verify firewall settings

#### Timeout Errors
```json
{
  "success": false,
  "error": "Request to Rhino Bridge Server timed out after 10 seconds",
  "error_type": "Timeout",
  "endpoint": "/analyze_inputs_context",
  "request_data": {}
}
```

**Common causes:**
- Handler is taking too long (e.g., complex Grasshopper analysis)
- Rhino is frozen or unresponsive
- Network issues

**How to fix:**
- Check Rhino Python console for errors
- Simplify the Grasshopper definition
- Increase timeout in `bridge_client.py` (currently 10 seconds)

#### JSON Decode Errors
```json
{
  "success": false,
  "error": "Bridge API request failed: Expecting value: line 1 column 1 (char 0)",
  "error_type": "JSONDecodeError",
  "error_details": {
    "message": "Expecting value: line 1 column 1 (char 0)",
    "line": 1,
    "column": 1
  },
  "endpoint": "/analyze_inputs_context",
  "request_data": {},
  "response_status": 500,
  "response_body": "<!-- Full response body here -->",
  "response_content_type": "text/html",
  "debug_hint": "The bridge server returned a non-JSON response..."
}
```

**Common causes:**
- Python exception in the handler (returns HTML error page instead of JSON)
- Handler returned non-dict type
- Handler didn't return anything (None)

**How to fix:**
- Check the `response_body` field for the actual error
- Look at the Rhino Python console for the full traceback
- Check the handler implementation for missing return statements

#### HTTP Errors (4xx, 5xx)
```json
{
  "success": false,
  "error": "HTTP 500 error from bridge server",
  "error_type": "HTTPError",
  "status_code": 500,
  "endpoint": "/analyze_inputs_context",
  "response_body": "<!-- Error details -->",
  "request_data": {}
}
```

### 2. Bridge Server Errors (Rhino Side)

The bridge server now prints detailed error information to the Rhino Python console:

```
[BRIDGE ERROR] Exception in handler handle_analyze_inputs_context for endpoint /analyze_inputs_context
[BRIDGE ERROR] Exception type: AttributeError
[BRIDGE ERROR] Exception message: 'NoneType' object has no attribute 'Text'
[BRIDGE ERROR] Request data: {}
[BRIDGE ERROR] Full traceback:
Traceback (most recent call last):
  File "C:\...\gh_tools.py", line 1684, in handle_analyze_inputs_context
    scribble_text = obj.Text
AttributeError: 'NoneType' object has no attribute 'Text'
```

And returns comprehensive error JSON:

```json
{
  "success": false,
  "error": "Handler error: 'NoneType' object has no attribute 'Text'",
  "error_type": "AttributeError",
  "endpoint": "/analyze_inputs_context",
  "traceback": "<!-- Full traceback -->",
  "request_data": {},
  "debug_hint": "An exception occurred in the Rhino bridge handler..."
}
```

### 3. Handler Decorator Errors

The `@bridge_handler` decorator now wraps every handler with comprehensive error handling:

**Console output:**
```
[BRIDGE] Executing handler for endpoint: /analyze_inputs_context
[BRIDGE] Handler function: handle_analyze_inputs_context
[BRIDGE] Request data: {}
[BRIDGE] Handler handle_analyze_inputs_context completed successfully
```

**On error:**
```
[BRIDGE ERROR] Exception in handler handle_analyze_inputs_context for endpoint /analyze_inputs_context
[BRIDGE ERROR] Exception type: KeyError
[BRIDGE ERROR] Exception message: 'missing_key'
[BRIDGE ERROR] Request data: {}
[BRIDGE ERROR] Full traceback:
<!-- Full Python traceback -->
```

**Error response includes:**
- `error_type`: Exception class name (e.g., "AttributeError", "KeyError")
- `error_message`: Exception message
- `endpoint`: The failing endpoint
- `handler_function`: Name of the handler function
- `file_line`: Extracted file and line number where error occurred
- `traceback`: Full Python traceback
- `traceback_lines`: Last 10 lines of traceback for quick reference
- `request_data`: The data that was sent to the handler
- `python_version`: Python version running in Rhino
- `debug_hint`: Helpful hint about what to check

## Debugging Workflow

### When a tool call fails:

1. **Check the error response** in your Claude conversation
   - Look at the `error_type` field to understand what kind of error occurred
   - Read the `debug_hint` for immediate guidance

2. **Check the Rhino Python console** (if using Rhino)
   - Open Rhino
   - Type `_EditPythonScript` to open the Python editor
   - Look at the console output for `[BRIDGE ERROR]` messages
   - Review the full traceback

3. **Examine the specific error details**:
   - For JSONDecodeError: Check `response_body` to see what was returned
   - For handler exceptions: Check `traceback` and `file_line` fields
   - For connection errors: Verify the bridge server is running

4. **Common fixes**:
   - Restart the Rhino bridge server
   - Check that Grasshopper file is open (for GH tools)
   - Verify the Grasshopper definition is not in an error state
   - Look for None/null values in your handler code

## Example: JSON Decode Errors

**Error pattern:**
```json
{
  "success": false,
  "error": "Bridge API request failed: Expecting value: line 1 column 1 (char 0)"
}
```

**What this indicates:**
- The bridge server returned an empty or non-JSON response
- Usually indicates a Python exception in the handler
- The handler crashed before returning proper JSON

**Detailed error response:**
```json
{
  "success": false,
  "error": "AttributeError: object has no attribute 'property'",
  "error_type": "AttributeError",
  "endpoint": "/endpoint_name",
  "file_line": "File 'tool_file.py', line 123",
  "traceback": "<!-- Full traceback -->",
  "debug_hint": "See traceback field for details"
}
```

**Resolution:**
- Check the line number in the traceback
- Add proper null/attribute checks before accessing object properties
- Review the Rhino Python console for full error details

## Logging

All errors are logged with:
- **Timestamp** (via Python logging)
- **Error type** and message
- **Full context** (endpoint, request data, response)
- **Actionable hints** in the response

## File Locations

- **MCP/bridge_client.py**: Line 23-138 - Enhanced HTTP error handling
- **Rhino/rhino_bridge_server.py**: Line 102-197 - Enhanced server error handling
- **Tools/tool_registry.py**: Line 103-192 - Enhanced handler decorator with error wrapper

## Best Practices

1. **Always return a dict** from bridge handlers with at least a `success` field
2. **Use try-except** blocks in your handlers for critical sections
3. **Add debug_log** arrays to complex handlers for troubleshooting
4. **Check for None** before accessing object attributes in Rhino/Grasshopper
5. **Log intermediate steps** using `print()` statements - they appear in Rhino console
6. **Test handlers** with edge cases (empty documents, missing data, etc.)

## Reporting Issues

When reporting bugs, include:
1. The full error JSON response from the tool call
2. The Rhino Python console output (if applicable)
3. The request data that triggered the error
4. Your Rhino version and Python version (from `python_version` field)
5. Steps to reproduce the issue
