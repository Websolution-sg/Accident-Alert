#!/bin/bash

# Server Requirements Checker for Enhanced Accident Monitor
echo "🔍 Server Requirements Checker"
echo "==============================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get system info
get_system_info() {
    echo ""
    echo "📋 System Information:"
    echo "   OS: $(lsb_release -d 2>/dev/null | cut -f2 || cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
    echo "   Kernel: $(uname -r)"
    echo "   Architecture: $(uname -m)"
    
    if command_exists free; then
        TOTAL_RAM=$(free -h | awk '/^Mem:/ {print $2}')
        FREE_RAM=$(free -h | awk '/^Mem:/ {print $7}')
        echo "   RAM: $TOTAL_RAM (Available: $FREE_RAM)"
    fi
    
    if command_exists df; then
        DISK_INFO=$(df -h / | awk 'NR==2 {print $2 " (" $4 " available)"}')
        echo "   Disk: $DISK_INFO"
    fi
    
    echo "   Uptime: $(uptime -p 2>/dev/null || uptime)"
}

# Function to check network connectivity
check_network() {
    echo ""
    echo "🌐 Network Connectivity:"
    
    if ping -c 1 google.com >/dev/null 2>&1; then
        echo "   ✅ Internet connection: OK"
    else
        echo "   ❌ Internet connection: FAILED"
        return 1
    fi
    
    if ping -c 1 api.telegram.org >/dev/null 2>&1; then
        echo "   ✅ Telegram API access: OK"
    else
        echo "   ⚠️  Telegram API access: May have issues"
    fi
    
    if command_exists curl; then
        WAZE_TEST=$(curl -s --connect-timeout 5 "https://www.waze.com/live-map/api/georss?bottom=1.1&left=103.6&right=104.1&top=1.5&env=row&types=alerts" | jq '.alerts | length' 2>/dev/null || echo "0")
        if [ "$WAZE_TEST" -gt 0 ]; then
            echo "   ✅ Waze API access: OK ($WAZE_TEST alerts)"
        else
            echo "   ⚠️  Waze API access: Limited or blocked"
        fi
    fi
}

# Function to check required software
check_software() {
    echo ""
    echo "🛠️  Required Software:"
    
    # Python 3
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        echo "   ✅ Python 3: $PYTHON_VERSION"
    else
        echo "   ❌ Python 3: Not installed"
        MISSING_DEPS=true
    fi
    
    # pip
    if command_exists pip3; then
        PIP_VERSION=$(pip3 --version | cut -d' ' -f2)
        echo "   ✅ pip3: $PIP_VERSION"
    else
        echo "   ❌ pip3: Not installed"
        MISSING_DEPS=true
    fi
    
    # systemd
    if command_exists systemctl; then
        echo "   ✅ systemd: Available"
    else
        echo "   ❌ systemd: Not available (services won't work)"
        MISSING_DEPS=true
    fi
    
    # git
    if command_exists git; then
        echo "   ✅ git: Available"
    else
        echo "   ⚠️  git: Not installed (recommended for updates)"
    fi
    
    # curl/wget
    if command_exists curl; then
        echo "   ✅ curl: Available"
    elif command_exists wget; then
        echo "   ✅ wget: Available"
    else
        echo "   ⚠️  curl/wget: Not available (recommended)"
    fi
}

# Function to check Python packages
check_python_packages() {
    echo ""
    echo "🐍 Python Dependencies:"
    
    if command_exists pip3; then
        # Check requests
        if python3 -c "import requests" 2>/dev/null; then
            REQUESTS_VERSION=$(python3 -c "import requests; print(requests.__version__)" 2>/dev/null)
            echo "   ✅ requests: $REQUESTS_VERSION"
        else
            echo "   ❌ requests: Not installed"
            MISSING_PYTHON_DEPS=true
        fi
        
        # Check other standard libraries
        if python3 -c "import json, time, datetime, os, re" 2>/dev/null; then
            echo "   ✅ Standard libraries: Available"
        else
            echo "   ❌ Standard libraries: Missing"
            MISSING_PYTHON_DEPS=true
        fi
    else
        echo "   ❌ Cannot check - pip3 not available"
    fi
}

# Function to check ports and permissions
check_system_access() {
    echo ""
    echo "🔒 System Access:"
    
    # Check sudo access
    if sudo -n true 2>/dev/null; then
        echo "   ✅ sudo access: Available (passwordless)"
    elif sudo -l >/dev/null 2>&1; then
        echo "   ✅ sudo access: Available (requires password)"
    else
        echo "   ❌ sudo access: Not available"
        MISSING_PERMISSIONS=true
    fi
    
    # Check if user can create systemd services
    if [ -d "/etc/systemd/system" ]; then
        if sudo test -w "/etc/systemd/system" 2>/dev/null; then
            echo "   ✅ systemd service creation: Possible"
        else
            echo "   ❌ systemd service creation: No write access"
            MISSING_PERMISSIONS=true
        fi
    else
        echo "   ❌ systemd directory: Not found"
        MISSING_PERMISSIONS=true
    fi
    
    # Check home directory write access
    if [ -w "$HOME" ]; then
        echo "   ✅ Home directory write: OK"
    else
        echo "   ❌ Home directory write: No access"
        MISSING_PERMISSIONS=true
    fi
}

# Function to provide installation commands
show_installation_commands() {
    echo ""
    echo "🔧 Installation Commands:"
    echo ""
    
    # Detect OS
    if command_exists apt-get; then
        echo "For Ubuntu/Debian:"
        echo "   sudo apt-get update"
        echo "   sudo apt-get install -y python3 python3-pip git curl"
        echo "   python3 -m pip install --user requests"
    elif command_exists yum; then
        echo "For CentOS/RHEL:"
        echo "   sudo yum update -y"
        echo "   sudo yum install -y python3 python3-pip git curl"
        echo "   python3 -m pip install --user requests"
    elif command_exists dnf; then
        echo "For Fedora:"
        echo "   sudo dnf update -y"
        echo "   sudo dnf install -y python3 python3-pip git curl"
        echo "   python3 -m pip install --user requests"
    else
        echo "Please install the following packages using your system's package manager:"
        echo "   - python3 (version 3.7+)"
        echo "   - python3-pip"
        echo "   - git"
        echo "   - curl"
        echo "   Then run: python3 -m pip install --user requests"
    fi
}

# Main execution
main() {
    get_system_info
    check_network
    check_software
    check_python_packages
    check_system_access
    
    echo ""
    echo "📊 Summary:"
    echo "=========="
    
    ISSUES=0
    
    if [ "$MISSING_DEPS" = true ]; then
        echo "❌ Missing system dependencies"
        ISSUES=$((ISSUES + 1))
    fi
    
    if [ "$MISSING_PYTHON_DEPS" = true ]; then
        echo "❌ Missing Python dependencies"
        ISSUES=$((ISSUES + 1))
    fi
    
    if [ "$MISSING_PERMISSIONS" = true ]; then
        echo "❌ Insufficient system permissions"
        ISSUES=$((ISSUES + 1))
    fi
    
    if [ $ISSUES -eq 0 ]; then
        echo "✅ Server is ready for Enhanced Accident Monitor deployment!"
        echo ""
        echo "🚀 You can now run the deployment script:"
        echo "   ./deploy_ssh.sh (Linux/Mac)"
        echo "   deploy_ssh.bat (Windows)"
    else
        echo "⚠️  Found $ISSUES issue(s) that need to be resolved"
        show_installation_commands
        echo ""
        echo "After installing missing dependencies, run this script again to verify."
    fi
}

# Run the checks
main