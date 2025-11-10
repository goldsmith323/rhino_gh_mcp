#!/bin/bash

echo "================================================"
echo "Rhino Grasshopper MCP - Environment Setup"
echo "================================================"
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "[ERROR] UV is not installed!"
    echo ""
    echo "Please install UV first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "[1/3] UV is installed ✓"
echo ""

# Navigate to Setup directory
cd "$(dirname "$0")"

echo "[2/3] Installing Python and dependencies with UV..."
echo "This may take a minute on first run..."
echo ""

uv pip install --native-tls -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Installation failed!"
    echo "Please check the error messages above."
    exit 1
fi

echo ""
echo "[3/3] Environment setup complete! ✓"
echo ""
echo "================================================"
echo "Next Steps:"
echo "================================================"
echo "1. Configure Claude Desktop (see setup_guide.md)"
echo "2. Start Rhino Bridge Server (see Rhino/README.md)"
echo "3. Restart Claude Desktop"
echo "================================================"
echo ""
