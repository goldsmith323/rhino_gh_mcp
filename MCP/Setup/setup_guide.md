# Rhino Grasshopper MCP Server - Setup Guide

This guide will help you set up the Python environment and configure Claude Desktop to use the Rhino Grasshopper MCP Server.

## Prerequisites

- **Rhino 8** installed on your system
- **Claude Desktop** installed ([download here](https://claude.ai/download))

## Step 1: Install UV Package Manager

UV is a fast, modern Python package manager that will handle Python installation and dependencies automatically.

### Windows

Open PowerShell and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### macOS/Linux

Open Terminal and run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Verify Installation

Close and reopen your terminal, then run:

```bash
uv --version
```

You should see a version number (e.g., `uv 0.4.x`).

---

## Step 2: Setup Python Environment

### Windows

1. Open Command Prompt or PowerShell
2. Navigate to the Setup folder:
   ```cmd
   cd path\to\rhino_gh_mcp\MCP\Setup
   ```
3. Run the setup script:
   ```cmd
   setup_env.bat
   ```

### macOS/Linux

1. Open Terminal
2. Navigate to the Setup folder:
   ```bash
   cd path/to/rhino_gh_mcp/MCP/Setup
   ```
3. Make the script executable and run it:
   ```bash
   chmod +x setup_env.sh
   ./setup_env.sh
   ```

The script will:
- Check if UV is installed
- Install Python 3.10+ automatically (if needed)
- Install all required dependencies (mcp, pydantic, requests, etc.)
- Create a virtual environment in `.venv/` folder

**This process typically takes 1-2 minutes on first run.**

---

## Step 3: Configure Claude Desktop

### Locate Claude Desktop Config File

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```
(Usually: `C:\Users\YourUsername\AppData\Roaming\Claude\claude_desktop_config.json`)

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### Add MCP Server Configuration

1. Open `claude_desktop_config.json` in a text editor
2. Add the following configuration (replace `YOUR_REPO_PATH` with your actual path):

#### Windows Configuration:

```json
{
  "mcpServers": {
    "Rhino Grasshopper MCP": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\YOUR_REPO_PATH\\rhino_gh_mcp\\MCP\\Setup",
        "run",
        "--native-tls",
        "python",
        "..\\main.py"
      ],
      "description": "Rhino 3D and Grasshopper parametric design tools"
    }
  }
}
```

#### macOS/Linux Configuration:

```json
{
  "mcpServers": {
    "Rhino Grasshopper MCP": {
      "command": "uv",
      "args": [
        "--directory",
        "/YOUR_REPO_PATH/rhino_gh_mcp/MCP/Setup",
        "run",
        "--native-tls",
        "python",
        "../main.py"
      ],
      "description": "Rhino 3D and Grasshopper parametric design tools"
    }
  }
}
```

### Important Notes:

- Use **double backslashes** (`\\`) for Windows paths
- Use **forward slashes** (`/`) for macOS/Linux paths
- Replace `YOUR_REPO_PATH` with the full absolute path to your repository
- The `..\\main.py` (Windows) or `../main.py` (macOS/Linux) refers to the main.py file one level up from Setup folder

### Example (Windows):

```json
{
  "mcpServers": {
    "Rhino Grasshopper MCP": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Path\\To\\rhino_gh_mcp\\MCP\\Setup",
        "run",
        "--native-tls",
        "python",
        "..\\main.py"
      ],
      "description": "Rhino 3D and Grasshopper parametric design tools"
    }
  }
}
```

---

## Step 4: Start Rhino Bridge Server

The MCP server needs to communicate with Rhino through a bridge server.

1. **Open Rhino 8**
2. **Open Python Script Editor**: `Tools > PythonScript > Edit`
3. **Load the bridge startup script**:
   - Click `Open` in the script editor
   - Navigate to: `rhino_gh_mcp/Rhino/start_rhino_bridge.py`
   - Click `Open`
4. **Run the script**: Click the green "Run" button (▶)
5. **Start the bridge**: In the Python console, type:
   ```python
   start_bridge()
   ```

You should see:
```
Bridge server started on http://localhost:8080
```

**Keep Rhino and the bridge server running** while using the MCP server.

---

## Step 5: Restart Claude Desktop

1. **Completely quit Claude Desktop** (close all windows)
2. **Restart Claude Desktop**
3. **Verify MCP Connection**: Look for the 🔌 icon or MCP indicator in Claude Desktop

---

## Verification

Test that everything is working by asking Claude:

```
Can you get Rhino info?
```

Claude should respond with information about your Rhino session (version, units, tolerance, etc.).

If you see errors, check:
- ✅ UV environment is set up (ran `setup_env.bat` or `setup_env.sh`)
- ✅ Path in `claude_desktop_config.json` is correct and absolute
- ✅ Rhino Bridge Server is running (`http://localhost:8080`)
- ✅ Claude Desktop was restarted after config changes

---

## Troubleshooting

### "UV is not installed" Error

Make sure you installed UV (Step 1) and restarted your terminal/command prompt.

### "Module not found" Error

Run the setup script again:
```bash
cd MCP/Setup
setup_env.bat   # Windows
./setup_env.sh  # macOS/Linux
```

### "Cannot connect to bridge server" Error

1. Verify Rhino is open
2. Verify bridge server is running:
   - In Rhino Python console: `bridge_status()`
   - Should show: `Bridge server is running on http://localhost:8080`
3. If stopped, restart it:
   ```python
   start_bridge()
   ```

### MCP Server Not Showing in Claude Desktop

1. Check `claude_desktop_config.json` syntax (valid JSON)
2. Verify the path is absolute (full path, not relative)
3. Restart Claude Desktop completely
4. Check Claude Desktop logs for errors

---

## What UV Does

UV provides several advantages for this setup:

- ✅ **Automatic Python Installation**: Installs Python 3.10+ if not present
- ✅ **Fast Dependency Management**: ~10x faster than pip
- ✅ **Reproducible Environments**: `uv.lock` ensures everyone has the same versions
- ✅ **Isolated Environment**: Dependencies don't conflict with system Python
- ✅ **Cross-Platform**: Works identically on Windows, macOS, and Linux

When you run the setup script, UV will:
1. Create a virtual environment in `.venv/`
2. Install Python 3.10+ if needed
3. Install all required packages (mcp, pydantic, requests, etc.)
4. Use native TLS to handle SSL certificates

The `uv run` command in Claude Desktop config automatically:
1. Activates the virtual environment
2. Runs the specified Python script
3. No manual activation needed!

---

## Advanced Configuration

### Environment Variables

You can customize the bridge server connection by setting environment variables:

- `RHINO_BRIDGE_HOST`: Default is `localhost`
- `RHINO_BRIDGE_PORT`: Default is `8080`
- `DEBUG_MODE`: Set to `true` for verbose logging (default: `false`)

### SSL Certificate Issues

If you encounter SSL certificate errors when Claude Desktop starts the MCP server, the `--native-tls` flag (included in the configuration above) tells UV to use your system's native TLS/SSL implementation instead of its bundled certificates. This is especially important in corporate environments with custom SSL certificates or proxy configurations.

**Note:** The `--native-tls` flag is already included in all configuration examples above and is recommended for all users to avoid certificate validation issues.

### Manual Python Execution (Without UV)

If you prefer not to use UV, you can manually set up a virtual environment:

```bash
cd MCP/Setup
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

If you encounter SSL issues with pip:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

Then update Claude config to use the venv Python directly:

**Windows:**
```json
{
  "mcpServers": {
    "Rhino Grasshopper MCP": {
      "command": "C:\\YOUR_REPO_PATH\\rhino_gh_mcp\\MCP\\Setup\\.venv\\Scripts\\python.exe",
      "args": [
        "..\\main.py"
      ]
    }
  }
}
```

**macOS/Linux:**
```json
{
  "mcpServers": {
    "Rhino Grasshopper MCP": {
      "command": "/YOUR_REPO_PATH/rhino_gh_mcp/MCP/Setup/.venv/bin/python",
      "args": [
        "../main.py"
      ]
    }
  }
}
```

---

## Getting Help

For additional documentation, see:
- **Main README**: `rhino_gh_mcp/README.md`
- **MCP Server README**: `rhino_gh_mcp/MCP/README.md`
- **Rhino Bridge README**: `rhino_gh_mcp/Rhino/README.md`
- **Debugging Guide**: `rhino_gh_mcp/DEBUGGING_GUIDE.md`

For issues and questions, check the repository's issue tracker or documentation.
