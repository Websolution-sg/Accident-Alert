#!/bin/bash

# SSH Deployment Script for Enhanced Accident Monitor
# This script deploys the accident monitoring system to a remote server via SSH

echo "🚀 SSH Deployment - Enhanced Accident Monitor"
echo "=============================================="

# Configuration
SERVER_IP=""
SERVER_USER=""
SERVER_PATH="/home/$SERVER_USER/accident-alert"
SSH_KEY=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to get user input
get_server_details() {
    echo ""
    echo "📋 Server Configuration"
    echo "======================="
    
    if [ -z "$SERVER_IP" ]; then
        read -p "Enter server IP address: " SERVER_IP
    fi
    
    if [ -z "$SERVER_USER" ]; then
        read -p "Enter SSH username: " SERVER_USER
    fi
    
    if [ -z "$SSH_KEY" ]; then
        read -p "Enter SSH key path (leave empty for password auth): " SSH_KEY
    fi
    
    SERVER_PATH="/home/$SERVER_USER/accident-alert"
    
    echo ""
    echo "📋 Configuration Summary:"
    echo "   Server: $SERVER_IP"
    echo "   User: $SERVER_USER"
    echo "   Deploy Path: $SERVER_PATH"
    echo "   SSH Key: ${SSH_KEY:-"Password authentication"}"
    echo ""
}

# Function to test SSH connection
test_ssh_connection() {
    print_status "Testing SSH connection..."
    
    SSH_CMD="ssh"
    if [ -n "$SSH_KEY" ]; then
        SSH_CMD="ssh -i $SSH_KEY"
    fi
    
    if $SSH_CMD -o ConnectTimeout=10 -o BatchMode=yes $SERVER_USER@$SERVER_IP "echo 'Connection successful'" 2>/dev/null; then
        print_success "SSH connection test passed"
        return 0
    else
        print_error "SSH connection failed"
        echo "Please check:"
        echo "  • Server IP and username are correct"
        echo "  • SSH key path is valid (if using key auth)"
        echo "  • Server is accessible from your network"
        return 1
    fi
}

# Function to setup server environment
setup_server_environment() {
    print_status "Setting up server environment..."
    
    SSH_CMD="ssh"
    if [ -n "$SSH_KEY" ]; then
        SSH_CMD="ssh -i $SSH_KEY"
    fi
    
    $SSH_CMD $SERVER_USER@$SERVER_IP << 'EOF'
        # Update system packages
        echo "📦 Updating system packages..."
        sudo apt-get update -y
        sudo apt-get upgrade -y
        
        # Install Python and pip
        echo "🐍 Installing Python and dependencies..."
        sudo apt-get install -y python3 python3-pip python3-venv git htop nano
        
        # Install process manager
        echo "⚙️ Installing PM2 for process management..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
        sudo npm install -g pm2
        
        echo "✅ Server environment setup complete"
EOF
    
    if [ $? -eq 0 ]; then
        print_success "Server environment setup completed"
    else
        print_error "Server environment setup failed"
        return 1
    fi
}

# Function to deploy application files
deploy_application() {
    print_status "Deploying application files..."
    
    # Create deployment package
    print_status "Creating deployment package..."
    rm -rf deploy_package
    mkdir -p deploy_package
    
    # Copy application files
    cp waze_accident_monitor.py deploy_package/
    cp waze_accident_monitor_secondary.py deploy_package/
    cp requirements.txt deploy_package/
    cp *.md deploy_package/ 2>/dev/null || true
    
    # Create systemd service files
    cat > deploy_package/accident-monitor-primary.service << 'EOF'
[Unit]
Description=Accident Monitor - Primary Channel
After=network.target

[Service]
Type=simple
User=USER_PLACEHOLDER
WorkingDirectory=PATH_PLACEHOLDER
ExecStart=/usr/bin/python3 PATH_PLACEHOLDER/waze_accident_monitor.py
Restart=always
RestartSec=10
Environment=TELEGRAM_BOT_TOKEN=8339261439:AAG1DdDGnd_vY6QPBk9zsZFEL9obtncSXQA
Environment=TELEGRAM_CHANNEL_ID=-1003329968129

[Install]
WantedBy=multi-user.target
EOF

    cat > deploy_package/accident-monitor-secondary.service << 'EOF'
[Unit]
Description=Accident Monitor - Secondary Channel
After=network.target

[Service]
Type=simple
User=USER_PLACEHOLDER
WorkingDirectory=PATH_PLACEHOLDER
ExecStart=/usr/bin/python3 PATH_PLACEHOLDER/waze_accident_monitor_secondary.py
Restart=always
RestartSec=10
Environment=TELEGRAM_BOT_TOKEN=8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U
Environment=TELEGRAM_CHANNEL_ID=-1003683261194

[Install]
WantedBy=multi-user.target
EOF

    # Create start/stop scripts
    cat > deploy_package/start_services.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Accident Monitor Services..."

sudo systemctl start accident-monitor-primary
sudo systemctl start accident-monitor-secondary

sudo systemctl enable accident-monitor-primary
sudo systemctl enable accident-monitor-secondary

echo "✅ Services started and enabled for auto-start"

echo ""
echo "📊 Service Status:"
sudo systemctl status accident-monitor-primary --no-pager -l
echo ""
sudo systemctl status accident-monitor-secondary --no-pager -l
EOF

    cat > deploy_package/stop_services.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Accident Monitor Services..."

sudo systemctl stop accident-monitor-primary
sudo systemctl stop accident-monitor-secondary

echo "✅ Services stopped"

echo ""
echo "📊 Service Status:"
sudo systemctl status accident-monitor-primary --no-pager -l
echo ""
sudo systemctl status accident-monitor-secondary --no-pager -l
EOF

    cat > deploy_package/logs.sh << 'EOF'
#!/bin/bash
echo "📋 Accident Monitor Logs"
echo "========================"

echo ""
echo "🔵 Primary Channel Logs:"
echo "------------------------"
sudo journalctl -u accident-monitor-primary -n 20 --no-pager

echo ""
echo "🟢 Secondary Channel Logs:"
echo "--------------------------"
sudo journalctl -u accident-monitor-secondary -n 20 --no-pager

echo ""
echo "📊 Live Logs (Ctrl+C to exit):"
echo "sudo journalctl -u accident-monitor-primary -u accident-monitor-secondary -f"
EOF

    chmod +x deploy_package/*.sh
    
    # Upload files to server
    print_status "Uploading files to server..."
    
    SCP_CMD="scp -r"
    if [ -n "$SSH_KEY" ]; then
        SCP_CMD="scp -i $SSH_KEY -r"
    fi
    
    $SCP_CMD deploy_package/ $SERVER_USER@$SERVER_IP:$SERVER_PATH/
    
    if [ $? -eq 0 ]; then
        print_success "Files uploaded successfully"
    else
        print_error "File upload failed"
        return 1
    fi
}

# Function to configure services on server
configure_services() {
    print_status "Configuring services on server..."
    
    SSH_CMD="ssh"
    if [ -n "$SSH_KEY" ]; then
        SSH_CMD="ssh -i $SSH_KEY"
    fi
    
    $SSH_CMD $SERVER_USER@$SERVER_IP << EOF
        cd $SERVER_PATH
        
        # Install Python dependencies
        echo "📦 Installing Python dependencies..."
        python3 -m pip install --user -r requirements.txt
        
        # Update service files with correct paths
        sed -i "s|USER_PLACEHOLDER|$SERVER_USER|g" *.service
        sed -i "s|PATH_PLACEHOLDER|$SERVER_PATH|g" *.service
        
        # Install systemd services
        echo "⚙️ Installing systemd services..."
        sudo cp accident-monitor-primary.service /etc/systemd/system/
        sudo cp accident-monitor-secondary.service /etc/systemd/system/
        
        # Reload systemd
        sudo systemctl daemon-reload
        
        echo "✅ Services configured successfully"
EOF
    
    if [ $? -eq 0 ]; then
        print_success "Services configured successfully"
    else
        print_error "Service configuration failed"
        return 1
    fi
}

# Function to start services
start_services() {
    print_status "Starting accident monitoring services..."
    
    SSH_CMD="ssh"
    if [ -n "$SSH_KEY" ]; then
        SSH_CMD="ssh -i $SSH_KEY"
    fi
    
    $SSH_CMD $SERVER_USER@$SERVER_IP << EOF
        cd $SERVER_PATH
        chmod +x *.sh
        ./start_services.sh
EOF
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        return 1
    fi
}

# Function to show deployment summary
show_summary() {
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================="
    echo ""
    echo "📊 Server Details:"
    echo "   • Server: $SERVER_IP"
    echo "   • Path: $SERVER_PATH"
    echo "   • Primary Channel: -1003329968129"
    echo "   • Secondary Channel: -1003683261194"
    echo ""
    echo "🔧 Management Commands:"
    echo "   • View logs: ssh $SERVER_USER@$SERVER_IP 'cd $SERVER_PATH && ./logs.sh'"
    echo "   • Stop services: ssh $SERVER_USER@$SERVER_IP 'cd $SERVER_PATH && ./stop_services.sh'"
    echo "   • Start services: ssh $SERVER_USER@$SERVER_IP 'cd $SERVER_PATH && ./start_services.sh'"
    echo ""
    echo "📋 Service Status:"
    if [ -n "$SSH_KEY" ]; then
        ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP "sudo systemctl status accident-monitor-primary accident-monitor-secondary --no-pager -l"
    else
        ssh $SERVER_USER@$SERVER_IP "sudo systemctl status accident-monitor-primary accident-monitor-secondary --no-pager -l"
    fi
}

# Main deployment process
main() {
    echo ""
    get_server_details
    
    if ! test_ssh_connection; then
        exit 1
    fi
    
    echo ""
    read -p "Proceed with deployment? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_server_environment || exit 1
        deploy_application || exit 1
        configure_services || exit 1
        start_services || exit 1
        show_summary
        
        echo ""
        print_success "🚀 SSH Deployment completed successfully!"
        echo ""
        echo "Your Enhanced Accident Monitor is now running on $SERVER_IP"
        echo "Both channels are being monitored 24/7 automatically!"
    else
        echo "Deployment cancelled."
    fi
    
    # Cleanup
    rm -rf deploy_package
}

# Check if running with parameters
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "SSH Deployment Script for Enhanced Accident Monitor"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --server IP    Set server IP address"
    echo "  --user USER    Set SSH username"
    echo "  --key PATH     Set SSH key path"
    echo ""
    echo "Environment variables:"
    echo "  SERVER_IP      Server IP address"
    echo "  SERVER_USER    SSH username"
    echo "  SSH_KEY        SSH key path"
    echo ""
    exit 0
fi

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --server)
            SERVER_IP="$2"
            shift 2
            ;;
        --user)
            SERVER_USER="$2"
            shift 2
            ;;
        --key)
            SSH_KEY="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if required tools are installed
if ! command -v ssh &> /dev/null; then
    print_error "SSH client not found. Please install OpenSSH client."
    exit 1
fi

if ! command -v scp &> /dev/null; then
    print_error "SCP not found. Please install OpenSSH client."
    exit 1
fi

# Run main deployment
main