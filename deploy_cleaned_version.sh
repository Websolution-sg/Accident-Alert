#!/bin/bash

# Deploy Cleaned Accident Monitor to Google Cloud VM
# This script creates/updates a VM with the latest cleaned version

echo "🚀 Deploying Cleaned Accident Monitor to Google Cloud VM"
echo "======================================================="

# Configuration
PROJECT_ID="verdant-petal-485213-h2"
VM_NAME="waze-monitor"
ZONE="asia-southeast1-a"  # Singapore region (closer to target area)
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

# Check if gcloud is configured
print_status "Checking Google Cloud configuration..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    print_error "Not authenticated to Google Cloud. Run 'gcloud auth login'"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID
print_success "Project set to $PROJECT_ID"

# Delete old VM if it exists
print_status "Cleaning up old VM..."
if gcloud compute instances describe $VM_NAME --zone=us-central1-c &>/dev/null; then
    print_warning "Found existing VM in us-central1-c. Deleting..."
    gcloud compute instances delete $VM_NAME --zone=us-central1-c --quiet
    print_success "Old VM deleted"
fi

# Create startup script for the VM
print_status "Creating startup script..."
cat > startup-script.sh << 'EOF'
#!/bin/bash

# Update system
apt-get update
apt-get install -y python3 python3-pip git

# Create user for the application
useradd -m -s /bin/bash wazeuser
cd /home/wazeuser

# Clone/copy the application files (we'll upload them)
# Install Python dependencies
pip3 install requests==2.31.0 pytz==2023.3

# Create the monitoring script
cat > waze_accident_monitor.py << 'PYTHON_SCRIPT'
EOF

# Add the Python script content to the startup script
print_status "Adding Python script to startup script..."
cat waze_accident_monitor.py >> startup-script.sh

cat >> startup-script.sh << 'EOF'
PYTHON_SCRIPT

# Make script executable
chmod +x waze_accident_monitor.py

# Create systemd service
cat > /etc/systemd/system/waze-accident-monitor.service << 'SERVICE_FILE'
[Unit]
Description=Waze Accident Monitor - Secondary Channel
After=network.target

[Service]
Type=simple
User=wazeuser
WorkingDirectory=/home/wazeuser
ExecStart=/usr/bin/python3 waze_accident_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE_FILE

# Enable and start the service
systemctl enable waze-accident-monitor
systemctl start waze-accident-monitor

# Set ownership
chown -R wazeuser:wazeuser /home/wazeuser

echo "Startup script completed. Service should be running."
EOF

print_success "Startup script created"

# Create the VM
print_status "Creating new VM in Singapore region..."
gcloud compute instances create $VM_NAME \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --network-tier=PREMIUM \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=default \
    --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append \
    --tags=http-server,https-server \
    --create-disk=auto-delete=yes,boot=yes,device-name=$VM_NAME,image=projects/$IMAGE_PROJECT/global/images/family/$IMAGE_FAMILY,mode=rw,size=10,type=projects/$PROJECT_ID/zones/$ZONE/diskTypes/pd-balanced \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=environment=production,app=accident-monitor \
    --reservation-affinity=any \
    --metadata-from-file startup-script=startup-script.sh

if [ $? -eq 0 ]; then
    print_success "VM created successfully!"
    
    # Wait for VM to be ready
    print_status "Waiting for VM to start up and configure..."
    sleep 60
    
    # Check service status
    print_status "Checking service status..."
    gcloud compute ssh $VM_NAME --zone=$ZONE --command="sudo systemctl status waze-accident-monitor" || true
    
    # Show logs
    print_status "Showing recent logs..."
    gcloud compute ssh $VM_NAME --zone=$ZONE --command="sudo journalctl -u waze-accident-monitor -n 10" || true
    
    print_success "Deployment completed!"
    echo ""
    echo "🎯 VM Details:"
    echo "   Name: $VM_NAME"
    echo "   Zone: $ZONE"
    echo "   Type: $MACHINE_TYPE"
    echo "   Channel: -1003683261194"
    echo "   Bot: @WazeAccident_bot"
    echo ""
    echo "📊 Management Commands:"
    echo "   Check status: gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo systemctl status waze-accident-monitor'"
    echo "   View logs: gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo journalctl -u waze-accident-monitor -f'"
    echo "   Restart: gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo systemctl restart waze-accident-monitor'"
    echo "   Stop: gcloud compute instances stop $VM_NAME --zone=$ZONE"
    echo ""
else
    print_error "VM creation failed!"
    exit 1
fi

# Cleanup
rm startup-script.sh

echo "🎉 Deployment complete! Your accident monitor is now running 24x7 on Google Cloud."