#!/bin/bash

# ====================================================
# SMD Local Installer - Social Media Downloader
# Author: Jaynuke79
# Repo: https://github.com/Jaynuke79/Social-Media-Downloader
# License: MIT
# ====================================================

# Package name for pip
PACKAGE_NAME="social-media-downloader"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------
# Function: Display the installer header
# ---------------------------------------------
function show_header() {
    clear
    echo -e "\e[96m===========================================\e[0m"
    echo -e "\e[1;95m       SMD Local Installer - v2.0         \e[0m"
    echo -e "\e[96m===========================================\e[0m"
    echo -e "\e[93mAuthor:\e[0m Jaynuke79"
    echo -e "\e[93mSource:\e[0m Local Repository"
    echo -e "\e[93mPath  :\e[0m $SCRIPT_DIR"
    echo ""
}

# ---------------------------------------------
# Function: Check Python and pip availability
# ---------------------------------------------
function check_python() {
    if command -v python3 &>/dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &>/dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "\e[91mError: Python is not installed.\e[0m"
        echo -e "Please install Python 3.10+ first."
        return 1
    fi

    # Check pip
    if ! $PYTHON_CMD -m pip --version &>/dev/null; then
        echo -e "\e[91mError: pip is not installed.\e[0m"
        echo -e "Please install pip first:"
        echo -e "  sudo apt install python3-pip"
        return 1
    fi

    echo -e "✅ Python and pip are available ($PYTHON_CMD)"
    return 0
}

# ---------------------------------------------
# Function: Ensure FFmpeg is installed
# ---------------------------------------------
function ensure_ffmpeg() {
    if ! command -v ffmpeg &>/dev/null; then
        echo -e "\n📦 FFmpeg is not installed. Installing..."
        if command -v apt &>/dev/null; then
            sudo apt update && sudo apt install -y ffmpeg
        elif command -v yum &>/dev/null; then
            sudo yum install -y ffmpeg
        elif command -v brew &>/dev/null; then
            brew install ffmpeg
        else
            echo -e "\e[93m⚠️  Please install FFmpeg manually for your system.\e[0m"
            return 1
        fi
    else
        echo -e "✅ FFmpeg is already installed."
    fi
}

# ---------------------------------------------
# Function: Get current local version
# ---------------------------------------------
function get_local_version() {
    if [ -f "$SCRIPT_DIR/smd/__init__.py" ]; then
        grep '__version__' "$SCRIPT_DIR/smd/__init__.py" | cut -d '"' -f 2
    else
        echo "unknown"
    fi
}

# ---------------------------------------------
# Function: Get installed version
# ---------------------------------------------
function get_installed_version() {
    if $PYTHON_CMD -c "import smd; print(smd.__version__)" 2>/dev/null; then
        return 0
    else
        echo "not_installed"
        return 1
    fi
}

# ---------------------------------------------
# Function: Perform local installation using pip
# ---------------------------------------------
function perform_install() {
    LOCAL_VERSION=$(get_local_version)
    
    echo -e "\n📦 Installing SMD from local repository..."
    echo -e "Version: $LOCAL_VERSION"
    echo -e "Source: $SCRIPT_DIR"
    
    read -p $'\nProceed with installation? (y/n): ' CONFIRM

    if [[ "$CONFIRM" == [yY] ]]; then
        echo -e "\n🔧 Installing package and dependencies..."
        
        # Try regular installation first
        if $PYTHON_CMD -m pip install "$SCRIPT_DIR"; then
            echo -e "\n✅ Installation successful!"
            echo -e "\n🎉 You can now use:"
            echo -e "  • \e[96msmd\e[0m"
            echo -e "  • \e[96msocial-media-downloader\e[0m"
            echo -e "  • \e[96mpython -m smd\e[0m"
            echo -e "\n🔐 New in this version: Authentication features!"
            echo -e "  • Download your saved Instagram posts"
            echo -e "  • Download your YouTube liked videos & Watch Later"
            echo -e "  • Access private content from your own accounts"
        else
            echo -e "\n❌ Installation failed!"
            echo -e "Try installing with --user flag:"
            echo -e "  $PYTHON_CMD -m pip install --user \"$SCRIPT_DIR\""
        fi
    else
        echo -e "\nInstallation cancelled by user."
    fi
}

# ---------------------------------------------
# Function: Perform editable installation
# ---------------------------------------------
function perform_editable_install() {
    LOCAL_VERSION=$(get_local_version)
    
    echo -e "\n🛠️  Installing SMD in editable mode..."
    echo -e "Version: $LOCAL_VERSION"
    echo -e "Source: $SCRIPT_DIR"
    echo -e "\n\e[93mNote: Editable mode allows you to modify the source code\e[0m"
    echo -e "\e[93mand see changes without reinstalling.\e[0m"
    
    read -p $'\nProceed with editable installation? (y/n): ' CONFIRM

    if [[ "$CONFIRM" == [yY] ]]; then
        echo -e "\n🔧 Installing package in editable mode..."
        
        # Try editable installation
        if $PYTHON_CMD -m pip install -e "$SCRIPT_DIR"; then
            echo -e "\n✅ Editable installation successful!"
            echo -e "\n🎉 You can now use:"
            echo -e "  • \e[96msmd\e[0m"
            echo -e "  • \e[96msocial-media-downloader\e[0m"
            echo -e "  • \e[96mpython -m smd\e[0m"
            echo -e "\n\e[93m📝 Changes to source code will be reflected immediately!\e[0m"
        else
            echo -e "\n❌ Editable installation failed!"
            echo -e "Falling back to regular installation..."
            perform_install
        fi
    else
        echo -e "\nEditable installation cancelled by user."
    fi
}

# ---------------------------------------------
# Function: Install development dependencies
# ---------------------------------------------
function install_dev_dependencies() {
    echo -e "\n🛠️  Installing with development dependencies..."
    
    # Try regular installation with dev dependencies first
    if $PYTHON_CMD -m pip install "$SCRIPT_DIR[dev]"; then
        echo -e "✅ Development installation successful!"
    else
        echo -e "❌ Failed to install with development dependencies."
        echo -e "Trying editable mode..."
        if $PYTHON_CMD -m pip install -e "$SCRIPT_DIR[dev]"; then
            echo -e "✅ Editable development installation successful!"
        else
            echo -e "❌ Both installation methods failed."
            echo -e "Try: $PYTHON_CMD -m pip install --user \"$SCRIPT_DIR[dev]\""
        fi
    fi
}

# ---------------------------------------------
# Function: Option 1 - Smart Install  
# ---------------------------------------------
function smart_install() {
    # Check Python and pip first
    if ! check_python; then
        return 1
    fi

    # Ensure ffmpeg is installed
    ensure_ffmpeg

    # Check if package is already installed
    INSTALLED_VERSION=$(get_installed_version 2>/dev/null)

    if [ "$INSTALLED_VERSION" != "not_installed" ]; then
        echo -e "\n✅ SMD is already installed (version $INSTALLED_VERSION)."
        echo -e "Redirecting to update/reinstall..."
        sleep 2
        update_smd
    else
        echo -e "\n📦 SMD is not installed. Proceeding with fresh installation..."
        perform_install
    fi
}

# ---------------------------------------------
# Function: Option 2 - Update/Reinstall SMD
# ---------------------------------------------
function update_smd() {
    # Check Python and pip first
    if ! check_python; then
        return 1
    fi

    INSTALLED_VERSION=$(get_installed_version 2>/dev/null)
    LOCAL_VERSION=$(get_local_version)

    echo -e "\n📊 Version Information:"
    echo -e "  Installed version : $INSTALLED_VERSION"
    echo -e "  Local version     : $LOCAL_VERSION"

    if [ "$INSTALLED_VERSION" == "not_installed" ]; then
        echo -e "\n❌ SMD is not installed. Use option 1 to install it first."
        return
    fi

    echo -e "\n🔄 Proceeding with update/reinstall from local repository..."
    perform_install
}

# ---------------------------------------------
# Function: Option 3 - Editable Install
# ---------------------------------------------
function editable_install() {
    # Check Python and pip first  
    if ! check_python; then
        return 1
    fi

    ensure_ffmpeg
    
    perform_editable_install
}

# ---------------------------------------------
# Function: Option 4 - Development Install
# ---------------------------------------------
function dev_install() {
    # Check Python and pip first  
    if ! check_python; then
        return 1
    fi

    ensure_ffmpeg
    
    echo -e "\n🛠️  Installing SMD with development dependencies..."
    install_dev_dependencies
}

# ---------------------------------------------
# Function: Option 5 - Uninstall SMD
# ---------------------------------------------
function uninstall_smd() {
    echo -e "\n🗑️  Uninstalling SMD..."
    
    if $PYTHON_CMD -m pip show "$PACKAGE_NAME" &>/dev/null; then
        $PYTHON_CMD -m pip uninstall -y "$PACKAGE_NAME"
        echo -e "✅ Uninstallation complete."
    else
        echo -e "⚠️  SMD package not found via pip."
    fi
}

# ---------------------------------------------
# Main Menu Loop
# ---------------------------------------------
while true; do
    show_header
    echo -e "\e[96m📦 Installation Options:\e[0m"
    echo "1. 🚀 Install SMD (Regular Install)"
    echo "2. 🔄 Update/Reinstall SMD"
    echo "3. 📝 Editable Install (for development)"
    echo "4. 🛠️  Development Install (with dev dependencies)"
    echo "5. 🗑️  Uninstall SMD"
    echo "6. ❌ Exit"
    echo ""
    read -p "Enter your choice [1-6]: " CHOICE

    case $CHOICE in
        1) smart_install ;;
        2) update_smd ;;
        3) editable_install ;;
        4) dev_install ;;
        5) uninstall_smd ;;
        6) echo -e "\n👋 Exiting SMD Local Installer. Goodbye!"; exit 0 ;;
        *) echo -e "\n❌ Invalid option. Please enter 1 to 6."; sleep 1 ;;
    esac

    read -p $'\n⏸️  Press Enter to return to the menu...'
done
# ---------------------------------------------
# End of script
# ---------------------------------------------
# Note: This script installs SMD from the local repository using pip.
# Supports Linux, macOS, and Windows (with bash/WSL).
# Requires Python 3.10+ and pip to be installed.