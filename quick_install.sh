#!/bin/bash
# Quick install script for Social Media Downloader

echo "🚀 Quick Install - Social Media Downloader"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Error: Python is not installed."
    echo "Please install Python 3.10+ first."
    exit 1
fi

# Check pip
if ! $PYTHON_CMD -m pip --version &>/dev/null; then
    echo "❌ Error: pip is not installed."
    echo "Please install pip first: sudo apt install python3-pip"
    exit 1
fi

echo "✅ Python and pip are available ($PYTHON_CMD)"

# Install the package
echo ""
echo "📦 Installing Social Media Downloader..."
echo "Source: $SCRIPT_DIR"

if $PYTHON_CMD -m pip install "$SCRIPT_DIR"; then
    echo ""
    echo "✅ Installation successful!"
    echo ""
    echo "🎉 You can now use:"
    echo "  • smd"
    echo "  • social-media-downloader"
    echo "  • python3 -m smd"
    echo ""
    echo "📚 Run 'smd' to get started!"
else
    echo ""
    echo "❌ Installation failed!"
    echo ""
    echo "🔧 Try these alternatives:"
    echo "  1. Install with --user flag:"
    echo "     $PYTHON_CMD -m pip install --user \"$SCRIPT_DIR\""
    echo ""
    echo "  2. Use the full installer:"
    echo "     ./install.sh"
    exit 1
fi