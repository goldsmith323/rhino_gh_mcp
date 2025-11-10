# Level 1: Test Integration

## Purpose
This level contains simple Python tools to test that your MCP server is working correctly **WITHOUT requiring Rhino or Grasshopper**. Use this level first to verify your basic setup.

## What You'll Test
-  MCP server is running and responding
-  Tool registration and discovery works
-  Bridge server can execute basic Python code
-  Parameters are passed correctly
-  JSON responses are formatted correctly

## Tools Included

### 1. `hello_world()`
- **Purpose:** Verify MCP connection is working
- **Parameters:** None
- **Returns:** Success message with timestamp

### 2. `simple_math(a, b, operation)`
- **Purpose:** Test parameter passing and computation
- **Parameters:**
  - `a` (float): First number
  - `b` (float): Second number
  - `operation` (str): "add", "subtract", "multiply", or "divide"
- **Returns:** Calculation result

### 3. `echo_message(message)`
- **Purpose:** Test string parameter handling
- **Parameters:**
  - `message` (str): Any text message
- **Returns:** Echoed message with metadata (length, word count)

## How to Use

### Step 1: Copy Files to Tools Folder
```bash
# Copy custom_tools.py to the main Tools directory
cp "Tools Archive/1Test Integration/custom_tools.py" ../
```

### Step 2: Start Rhino Bridge Server
1. Open Rhino 3D
2. Run the Python script: `Rhino/start_rhino_bridge.py`
3. Wait for message: "Rhino Bridge Server started on http://localhost:8080"

### Step 3: Start MCP Server
```bash
# In your terminal, from project root
python MCP/mcp_server.py
# or use your configured MCP client
```

### Step 4: Test the Tools
Try calling these tools from your MCP client:

**Test 1 - Hello World:**
```
"Use the hello_world tool"
```
Expected: Success message with timestamp

**Test 2 - Simple Math:**
```
"Use simple_math to add 5 and 3"
```
Expected: Result of 8

**Test 3 - Echo Message:**
```
"Use echo_message to echo 'Hello MCP!'"
```
Expected: Message echoed back with metadata

## Success Criteria
 All three tools execute without errors
 You receive proper JSON responses
 No Rhino or Grasshopper errors appear

## Troubleshooting

**Problem:** "Tool not found" or "Endpoint not found"
- **Solution:** Make sure you copied `custom_tools.py` to the `Tools/` folder (not a subfolder)
- **Solution:** Restart the Rhino bridge server to rediscover tools

**Problem:** "Bridge client not available"
- **Solution:** Check that `bridge_client.py` exists in the `MCP/` folder
- **Solution:** Verify your file paths and project structure

**Problem:** "Connection refused"
- **Solution:** Make sure the Rhino bridge server is running (check for "Server started" message)
- **Solution:** Verify the server is on http://localhost:8080

## Next Steps
Once all three tools work successfully:
1.  Your MCP infrastructure is working
2.  Move to **Level 2: Early Integration** to test Rhino + Grasshopper connectivity
