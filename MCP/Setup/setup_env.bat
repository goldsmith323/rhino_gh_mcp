@echo off
echo ================================================
echo Rhino Grasshopper MCP - Environment Setup
echo ================================================
echo.

REM Check if uv is installed
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] UV is not installed!
    echo.
    echo Please install UV first:
    echo   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    echo Then run this script again.
    pause
    exit /b 1
)

echo [1/3] UV is installed ✓
echo.

REM Navigate to Setup directory
cd /d "%~dp0"

echo [2/3] Installing Python and dependencies with UV...
echo This may take a minute on first run...
echo.

uv pip install --native-tls -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Installation failed!
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo [3/3] Environment setup complete! ✓
echo.
echo ================================================
echo Next Steps:
echo ================================================
echo 1. Configure Claude Desktop (see setup_guide.md)
echo 2. Start Rhino Bridge Server (see Rhino/README.md)
echo 3. Restart Claude Desktop
echo ================================================
echo.
pause
