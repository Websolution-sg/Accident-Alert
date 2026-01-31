#!/bin/bash
# One-command deployment to Google Cloud VM

VM_NAME="sg-accident-monitor"
ZONE="asia-southeast1-a"  # Singapore region
PROJECT_ID=$(gcloud config get-value project)

echo "🚀 Deploying Singapore Accident Monitor to Google Cloud VM"
echo "Project: $PROJECT_ID"
echo "VM Name: $VM_NAME"
echo "Zone: $ZONE"

# Check if gcloud is configured
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: gcloud not configured. Run 'gcloud init' first."
    exit 1
fi

# Create VM with startup script
echo "🔧 Creating VM instance..."
gcloud compute instances create $VM_NAME \
    --zone=$ZONE \
    --machine-type=e1-small \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-standard \
    --metadata-from-file startup-script=vm-setup.sh \
    --tags=http-server,https-server \
    --scopes=cloud-platform

if [ $? -ne 0 ]; then
    echo "❌ Failed to create VM. Check your gcloud configuration."
    exit 1
fi

# Wait for VM to be ready
echo "⏳ Waiting for VM to start and run setup script..."
sleep 90

# Check if VM is running
echo "🔍 Checking VM status..."
gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(status)"

# Copy monitor script to VM
echo "📤 Uploading monitor script..."
gcloud compute scp vm_accident_monitor.py $VM_NAME:/tmp/ --zone=$ZONE

if [ $? -ne 0 ]; then
    echo "❌ Failed to upload script. Trying with internal IP..."
    gcloud compute scp vm_accident_monitor.py $VM_NAME:/tmp/ --zone=$ZONE --internal-ip
fi

# SSH in and complete setup
echo "🔧 Completing setup on VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
echo '📁 Setting up monitor script...'
sudo mv /tmp/vm_accident_monitor.py /opt/accident-monitor/
sudo chmod +x /opt/accident-monitor/vm_accident_monitor.py
sudo chown nobody:nogroup /opt/accident-monitor/vm_accident_monitor.py

echo '🚀 Starting accident monitor service...'
sudo systemctl start accident-monitor.service
sudo systemctl enable accident-monitor.service

echo '✅ Checking service status...'
sudo systemctl status accident-monitor.service --no-pager
"

# Get VM external IP
EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

echo ""
echo "🎉 Deployment Complete!"
echo "=================================="
echo "VM Name: $VM_NAME"
echo "External IP: $EXTERNAL_IP"
echo "Zone: $ZONE"
echo ""
echo "📊 Monitor Commands:"
echo "gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo systemctl status accident-monitor.service'"
echo "gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo journalctl -u accident-monitor.service -f'"
echo ""
echo "🔧 Management Commands:"
echo "Start:   gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo systemctl start accident-monitor.service'"
echo "Stop:    gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo systemctl stop accident-monitor.service'"
echo "Restart: gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo systemctl restart accident-monitor.service'"
echo ""
echo "💰 Estimated Cost: ~$18/month (e1-small instance)"
echo "⚠️  Remember to stop the VM when not needed to save costs!"