# Debugging Guide

Quick reference for troubleshooting the Rhino/Grasshopper MCP server.

## Quick Start

**Getting an error?** Follow these steps:
1. Check the error response in Claude (look for `error_type` and `debug_hint`)
2. Open Rhino Python console for full traceback
3. Enable DEBUG_MODE if you need more details (see below)

## DEBUG_MODE

Controls how much information tools return in their responses.

### Toggle DEBUG_MODE

**Location:** `C:\Users\SeyedZ\Documents\GitHub\rhino_gh_mcp\.env`

```bash
# Activate (verbose responses with full debugging info)
DEBUG_MODE=true

# Deactivate (concise responses, saves tokens)
DEBUG_MODE=false
```

**After changing:** Restart both MCP server and Rhino bridge server.

### What Changes?

| Mode | Returns | Use When |
|------|---------|----------|
| `false` (default) | Essential data only | Normal operation, production |
| `true` | Full details + debug logs + tracebacks | Troubleshooting, development |

---

## Error Types

### ConnectionError
**Problem:** Cannot connect to Rhino Bridge Server

**Causes:**
- Bridge server not running in Rhino
- Wrong host/port configuration
- Firewall blocking connection

**Fix:**
1. Start bridge in Rhino: Run `start_rhino_bridge.py` in Rhino Script Editor
2. Check `.env` file for correct `RHINO_BRIDGE_HOST` and `RHINO_BRIDGE_PORT`
3. Verify http://localhost:8080/status in browser

---

### Timeout
**Problem:** Request timed out after 10 seconds

**Causes:**
- Complex Grasshopper computation taking too long
- Rhino is frozen or unresponsive

**Fix:**
1. Check Rhino Python console for errors
2. Simplify Grasshopper definition
3. Increase timeout in `MCP/bridge_client.py` line 47 (change `timeout=10`)

---

### JSONDecodeError
**Problem:** Bridge returned non-JSON response (usually means Python error)

**Causes:**
- Handler crashed with Python exception
- Handler returned wrong type (not dict)
- Handler returned None

**Fix:**
1. Check `response_body` field in error for actual error message
2. Open Rhino Python console for full traceback
3. Ensure handler returns `{"success": True/False, ...}`

---

### Handler Exceptions (AttributeError, KeyError, etc.)
**Problem:** Python exception in bridge handler

**What you get:**
- Error in Claude with `error_type`, `traceback`, and `file_line`
- Console output in Rhino with `[BRIDGE ERROR]` prefix

**Fix:**
1. Check `file_line` field to see where error occurred
2. Look at `traceback` for full stack trace
3. Check Rhino Python console for detailed output
4. Add None checks before accessing attributes
5. Validate data before processing

## Debugging Workflow

**Step 1:** Read the error in Claude
- Check `error_type` (ConnectionError, Timeout, JSONDecodeError, etc.)
- Read `debug_hint` for quick guidance
- Note `file_line` if present

**Step 2:** Check Rhino Python Console
- In Rhino: Type `_EditPythonScript`
- Look for `[BRIDGE ERROR]` messages
- Review full traceback

**Step 3:** Common Fixes
- **ConnectionError:** Start bridge server in Rhino
- **Timeout:** Check Rhino console, simplify GH definition
- **JSONDecodeError:** Check `response_body` field for actual error
- **Handler exceptions:** Check `file_line` and fix code at that location

---

## Console Output Examples

### Successful Handler
```
[BRIDGE] Executing handler for endpoint: /draw_line
[BRIDGE] Handler function: handle_draw_line
[BRIDGE] Request data: {"start_x": 0, "start_y": 0, ...}
[BRIDGE] Handler handle_draw_line completed successfully
```

### Failed Handler
```
[BRIDGE ERROR] Exception in handler handle_draw_line for endpoint /draw_line
[BRIDGE ERROR] Exception type: AttributeError
[BRIDGE ERROR] Exception message: 'NoneType' object has no attribute 'X'
[BRIDGE ERROR] Request data: {"start_x": 0, ...}
[BRIDGE ERROR] Full traceback:
...
```

---

## Best Practices

1. ✅ Always return dict with `success` field from handlers
2. ✅ Check for `None` before accessing attributes
3. ✅ Use `try-except` in critical sections
4. ✅ Add `print()` statements for debugging (shows in Rhino console)
5. ✅ Test with edge cases (empty docs, missing data)

---

## Key Files

| File | What It Does |
|------|--------------|
| `MCP/bridge_client.py` | HTTP error handling & reporting |
| `Rhino/rhino_bridge_server.py` | Server-side error catching |
| `Tools/tool_registry.py` | Handler decorator with error wrapper |
| `Tools/rhino_tools.py` | Uses `filter_debug_response()` |
| `Tools/gh_tools.py` | Uses `filter_debug_response()` |

---

## Need Help?

**Include this when reporting issues:**
1. Full error JSON from tool call
2. Rhino Python console output
3. Request data that triggered error
4. Steps to reproduce
