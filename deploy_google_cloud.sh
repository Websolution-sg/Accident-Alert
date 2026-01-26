#!/bin/bash

# Google Cloud VM Deployment Script for Enhanced Accident Monitor
# This script creates a VM and deploys the accident monitoring system

echo "🚀 Google Cloud VM Deployment - Enhanced Accident Monitor"
echo "========================================================="

# Configuration
PROJECT_ID=""
VM_NAME="accident-monitor"
ZONE="asia-southeast1-a"  # Singapore region
MACHINE_TYPE="e2-micro"   # Free tier eligible
IMAGE_FAMILY="ubuntu-2204-lts"
IMAGE_PROJECT="ubuntu-os-cloud"

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

# Check if gcloud is installed
check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        print_error "Google Cloud SDK not found!"
        echo ""
        echo "Please install Google Cloud SDK:"
        echo "https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    print_success "Google Cloud SDK found"
}

# Get project configuration
get_project_config() {
    echo ""
    echo "📋 Google Cloud Configuration"
    echo "============================="
    
    # Get current project
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
    
    if [ -n "$CURRENT_PROJECT" ]; then
        print_status "Current project: $CURRENT_PROJECT"
        read -p "Use this project? (Y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            read -p "Enter project ID: " PROJECT_ID
        else
            PROJECT_ID=$CURRENT_PROJECT
        fi
    else
        read -p "Enter your Google Cloud project ID: " PROJECT_ID
    fi
    
    # Set project
    gcloud config set project $PROJECT_ID
    
    echo ""
    echo "📋 Deployment Configuration:"
    echo "   Project: $PROJECT_ID"
    echo "   VM Name: $VM_NAME"
    echo "   Zone: $ZONE (Singapore)"
    echo "   Machine Type: $MACHINE_TYPE (Free tier)"
    echo "   OS: Ubuntu 22.04 LTS"
    echo ""
}

# Enable required APIs
enable_apis() {
    print_status "Enabling required Google Cloud APIs..."
    
    gcloud services enable compute.googleapis.com
    
    if [ $? -eq 0 ]; then
        print_success "APIs enabled successfully"
    else
        print_error "Failed to enable APIs"
        return 1
    fi
}

# Create startup script
create_startup_script() {
    print_status "Creating VM startup script..."
    
    cat > startup-script.sh << 'EOF'
#!/bin/bash

# VM Startup Script for Enhanced Accident Monitor
exec > >(tee /var/log/startup-script.log) 2>&1

echo "🚀 Starting Enhanced Accident Monitor Setup..."
echo "=============================================="

# Update system
echo "📦 Updating system packages..."
apt-get update -y
apt-get upgrade -y

# Install required packages
echo "🛠️ Installing required packages..."
apt-get install -y python3 python3-pip python3-venv git htop nano curl wget

# Create application user
echo "👤 Creating application user..."
useradd -m -s /bin/bash accident-monitor
usermod -aG sudo accident-monitor

# Setup application directory
APP_DIR="/home/accident-monitor/app"
mkdir -p $APP_DIR
chown accident-monitor:accident-monitor $APP_DIR

# Clone or copy application files (will be uploaded separately)
echo "📁 Setting up application directory structure..."

# Install Python dependencies globally for the user
echo "🐍 Installing Python dependencies..."
pip3 install requests

# Create systemd service for primary channel
cat > /etc/systemd/system/accident-monitor-primary.service << 'EOFS'
[Unit]
Description=Enhanced Accident Monitor - Primary Channel
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=accident-monitor
Group=accident-monitor
WorkingDirectory=/home/accident-monitor/app
ExecStart=/usr/bin/python3 /home/accident-monitor/app/waze_accident_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=TELEGRAM_BOT_TOKEN=8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U
Environment=TELEGRAM_CHANNEL_ID=-1003683261194

[Install]
WantedBy=multi-user.target
EOFS

# Create systemd service for secondary channel
cat > /etc/systemd/system/accident-monitor-secondary.service << 'EOFS'
[Unit]
Description=Enhanced Accident Monitor - Secondary Channel
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=accident-monitor
Group=accident-monitor
WorkingDirectory=/home/accident-monitor/app
ExecStart=/usr/bin/python3 /home/accident-monitor/app/waze_accident_monitor_secondary.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=TELEGRAM_BOT_TOKEN=8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U
Environment=TELEGRAM_CHANNEL_ID=-1003683261194

[Install]
WantedBy=multi-user.target
EOFS

# Reload systemd
systemctl daemon-reload

# Create management scripts
cat > /home/accident-monitor/start_services.sh << 'EOFS'
#!/bin/bash
echo "🚀 Starting Enhanced Accident Monitor Services..."
sudo systemctl enable accident-monitor-primary
sudo systemctl enable accident-monitor-secondary
sudo systemctl start accident-monitor-primary
sudo systemctl start accident-monitor-secondary
echo "✅ Services started and enabled for auto-start"
sleep 3
echo ""
echo "📊 Service Status:"
sudo systemctl status accident-monitor-primary --no-pager -l
echo ""
sudo systemctl status accident-monitor-secondary --no-pager -l
EOFS

cat > /home/accident-monitor/stop_services.sh << 'EOFS'
#!/bin/bash
echo "🛑 Stopping Enhanced Accident Monitor Services..."
sudo systemctl stop accident-monitor-primary
sudo systemctl stop accident-monitor-secondary
echo "✅ Services stopped"
echo ""
echo "📊 Service Status:"
sudo systemctl status accident-monitor-primary --no-pager -l
echo ""
sudo systemctl status accident-monitor-secondary --no-pager -l
EOFS

cat > /home/accident-monitor/view_logs.sh << 'EOFS'
#!/bin/bash
echo "📋 Enhanced Accident Monitor Logs"
echo "=================================="
echo ""
echo "🔵 Primary Channel (Recent 20 lines):"
echo "--------------------------------------"
sudo journalctl -u accident-monitor-primary -n 20 --no-pager
echo ""
echo "🟢 Secondary Channel (Recent 20 lines):"
echo "----------------------------------------"
sudo journalctl -u accident-monitor-secondary -n 20 --no-pager
echo ""
echo "💡 For live logs, run:"
echo "   sudo journalctl -u accident-monitor-primary -u accident-monitor-secondary -f"
EOFS

cat > /home/accident-monitor/status.sh << 'EOFS'
#!/bin/bash
echo "📊 Enhanced Accident Monitor Status"
echo "==================================="
echo ""
echo "🔵 Primary Channel:"
sudo systemctl status accident-monitor-primary --no-pager -l
echo ""
echo "🟢 Secondary Channel:"
sudo systemctl status accident-monitor-secondary --no-pager -l
echo ""
echo "📈 Resource Usage:"
echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2 " (" $3/$2*100.0 "%)"}' | cut -d'(' -f2 | cut -d')' -f1)"
echo "Disk: $(df -h / | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')"
echo "Uptime: $(uptime -p)"
EOFS

# Make scripts executable
chmod +x /home/accident-monitor/*.sh
chown accident-monitor:accident-monitor /home/accident-monitor/*.sh

echo "✅ VM setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Upload application files to /home/accident-monitor/app/"
echo "2. Run /home/accident-monitor/start_services.sh to start monitoring"
echo ""
echo "🎉 Your Enhanced Accident Monitor VM is ready!"
EOF

    chmod +x startup-script.sh
    print_success "Startup script created"
}

# Create VM instance
create_vm() {
    print_status "Creating Google Cloud VM instance..."
    
    gcloud compute instances create $VM_NAME \
        --zone=$ZONE \
        --machine-type=$MACHINE_TYPE \
        --image-family=$IMAGE_FAMILY \
        --image-project=$IMAGE_PROJECT \
        --boot-disk-size=10GB \
        --boot-disk-type=pd-standard \
        --metadata-from-file startup-script=startup-script.sh \
        --tags=accident-monitor \
        --scopes=https://www.googleapis.com/auth/cloud-platform
    
    if [ $? -eq 0 ]; then
        print_success "VM created successfully!"
        
        # Wait for VM to be ready
        print_status "Waiting for VM to initialize (this may take 2-3 minutes)..."
        sleep 30
        
        # Get VM external IP
        VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
        
        echo ""
        print_success "VM is ready!"
        echo "   VM Name: $VM_NAME"
        echo "   External IP: $VM_IP"
        echo "   Zone: $ZONE"
    else
        print_error "Failed to create VM"
        return 1
    fi
}

# Wait for startup script to complete
wait_for_setup() {
    print_status "Waiting for VM setup to complete..."
    
    VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
    
    echo "This will take 2-5 minutes while the VM installs packages..."
    
    for i in {1..60}; do
        if gcloud compute ssh $VM_NAME --zone=$ZONE --command="test -f /var/log/startup-script.log && grep -q 'VM setup completed successfully' /var/log/startup-script.log" --quiet 2>/dev/null; then
            print_success "VM setup completed!"
            return 0
        fi
        
        echo -n "."
        sleep 5
    done
    
    print_warning "Setup is taking longer than expected. You can check manually later."
    return 1
}

# Upload application files
upload_files() {
    print_status "Uploading application files..."
    
    # Create local deployment package
    rm -rf deploy_files
    mkdir -p deploy_files
    
    cp waze_accident_monitor.py deploy_files/ 2>/dev/null || echo "Primary monitor file not found"
    cp waze_accident_monitor_secondary.py deploy_files/ 2>/dev/null || echo "Secondary monitor file not found"
    cp requirements.txt deploy_files/ 2>/dev/null || echo "Requirements file not found"
    
    # Upload files
    gcloud compute scp --recurse deploy_files/* $VM_NAME:/tmp/ --zone=$ZONE
    
    # Move files to proper location and set ownership
    gcloud compute ssh $VM_NAME --zone=$ZONE --command="
        sudo mkdir -p /home/accident-monitor/app
        sudo cp /tmp/*.py /home/accident-monitor/app/ 2>/dev/null || echo 'No Python files to copy'
        sudo cp /tmp/requirements.txt /home/accident-monitor/app/ 2>/dev/null || echo 'No requirements.txt'
        sudo chown -R accident-monitor:accident-monitor /home/accident-monitor/app
        sudo chmod +x /home/accident-monitor/app/*.py 2>/dev/null || true
    "
    
    # Cleanup
    rm -rf deploy_files
    
    if [ $? -eq 0 ]; then
        print_success "Files uploaded successfully"
    else
        print_error "File upload failed"
        return 1
    fi
}

# Start services
start_services() {
    print_status "Starting accident monitoring services..."
    
    gcloud compute ssh $VM_NAME --zone=$ZONE --command="
        cd /home/accident-monitor
        sudo ./start_services.sh
    "
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        return 1
    fi
}

# Show summary
show_summary() {
    VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
    
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================="
    echo ""
    echo "📊 VM Details:"
    echo "   Name: $VM_NAME"
    echo "   IP: $VM_IP"
    echo "   Zone: $ZONE"
    echo "   Project: $PROJECT_ID"
    echo ""
    echo "📱 Monitoring Channels:"
    echo "   Active: -1003683261194"
    echo "   Source: -1001486947378 (@sgaccident)"
    echo ""
    echo "🔧 Management Commands:"
    echo "   Connect: gcloud compute ssh $VM_NAME --zone=$ZONE"
    echo "   View logs: gcloud compute ssh $VM_NAME --zone=$ZONE --command='./view_logs.sh'"
    echo "   Check status: gcloud compute ssh $VM_NAME --zone=$ZONE --command='./status.sh'"
    echo "   Stop services: gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo ./stop_services.sh'"
    echo "   Start services: gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo ./start_services.sh'"
    echo ""
    echo "💰 Cost Information:"
    echo "   Machine: e2-micro (Free tier: 744 hours/month)"
    echo "   Storage: 10GB (~$0.40/month)"
    echo "   Network: Minimal cost for API calls"
    echo ""
    echo "✅ Your Enhanced Accident Monitor is now running 24/7 on Google Cloud!"
    echo "   It will automatically restart if the VM reboots."
    echo "   No need to keep your local PC running!"
}

# Main deployment process
main() {
    check_gcloud
    get_project_config
    
    echo ""
    read -p "Proceed with VM creation and deployment? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        enable_apis || exit 1
        create_startup_script || exit 1
        create_vm || exit 1
        wait_for_setup
        upload_files || exit 1
        start_services || exit 1
        show_summary
        
        print_success "🚀 Google Cloud deployment completed successfully!"
    else
        echo "Deployment cancelled."
    fi
    
    # Cleanup
    rm -f startup-script.sh
}

# Check if running with help parameter
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Google Cloud VM Deployment Script for Enhanced Accident Monitor"
    echo ""
    echo "This script will:"
    echo "  1. Create a Google Cloud VM instance (e2-micro, free tier)"
    echo "  2. Install required software and dependencies"
    echo "  3. Upload your accident monitoring applications"
    echo "  4. Configure systemd services for 24/7 operation"
    echo "  5. Start monitoring both Telegram channels"
    echo ""
    echo "Requirements:"
    echo "  - Google Cloud SDK installed and authenticated"
    echo "  - Active Google Cloud project with billing enabled"
    echo "  - Application files in current directory"
    echo ""
    echo "Usage: $0"
    exit 0
fi

# Run main deployment
main