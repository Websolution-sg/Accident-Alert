# Google Cloud VM Deployment Instructions

## Quick Deploy Commands

### 1. Create Google Cloud VM
```bash
# Create a small VM instance (f1-micro for testing, e1-small for production)
gcloud compute instances create accident-monitor-vm \
    --zone=asia-southeast1-a \
    --machine-type=e1-small \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=10GB \
    --boot-disk-type=pd-standard \
    --metadata-from-file startup-script=vm-setup.sh \
    --tags=http-server,https-server \
    --scopes=cloud-platform
```

### 2. Alternative: Manual Setup
If you prefer to set up manually:

```bash
# SSH into your VM
gcloud compute ssh accident-monitor-vm --zone=asia-southeast1-a

# Run the setup commands
curl -O https://raw.githubusercontent.com/Websolution-sg/Accident-Alert/main/vm-setup.sh
chmod +x vm-setup.sh
sudo ./vm-setup.sh
```

### 3. Upload the Monitor Script
```bash
# Copy the monitor script to VM
gcloud compute scp vm_accident_monitor.py accident-monitor-vm:/tmp/ --zone=asia-southeast1-a

# SSH in and move it to the right location
gcloud compute ssh accident-monitor-vm --zone=asia-southeast1-a
sudo mv /tmp/vm_accident_monitor.py /opt/accident-monitor/
sudo chmod +x /opt/accident-monitor/vm_accident_monitor.py
```

### 4. Start the Service
```bash
# Start the accident monitoring service
sudo systemctl start accident-monitor.service

# Enable auto-start on boot
sudo systemctl enable accident-monitor.service

# Check status
sudo systemctl status accident-monitor.service

# View live logs
sudo journalctl -u accident-monitor.service -f
```

## Alternative: One-Command Deployment

Create this script locally and run it:

```bash
#!/bin/bash
# Complete deployment script

VM_NAME="accident-monitor-vm"
ZONE="asia-southeast1-a"

# Create VM with startup script
gcloud compute instances create $VM_NAME \
    --zone=$ZONE \
    --machine-type=e1-small \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=10GB \
    --metadata-from-file startup-script=vm-setup.sh \
    --scopes=cloud-platform

# Wait for VM to be ready
echo "Waiting for VM to start..."
sleep 60

# Copy monitor script
gcloud compute scp vm_accident_monitor.py $VM_NAME:/tmp/ --zone=$ZONE

# SSH in and complete setup
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
sudo mv /tmp/vm_accident_monitor.py /opt/accident-monitor/
sudo chmod +x /opt/accident-monitor/vm_accident_monitor.py
sudo systemctl start accident-monitor.service
sudo systemctl enable accident-monitor.service
"

echo "Deployment complete!"
echo "Check status: gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo systemctl status accident-monitor.service'"
```

## Monitoring Commands

```bash
# Check service status
sudo systemctl status accident-monitor.service

# View logs (live)
sudo journalctl -u accident-monitor.service -f

# View logs (last 100 lines)
sudo journalctl -u accident-monitor.service -n 100

# Restart service
sudo systemctl restart accident-monitor.service

# Stop service
sudo systemctl stop accident-monitor.service

# View application logs
tail -f /tmp/accident_monitor.log
```

## VM Management

```bash
# SSH into VM
gcloud compute ssh accident-monitor-vm --zone=asia-southeast1-a

# Stop VM (to save costs)
gcloud compute instances stop accident-monitor-vm --zone=asia-southeast1-a

# Start VM
gcloud compute instances start accident-monitor-vm --zone=asia-southeast1-a

# Delete VM (permanent)
gcloud compute instances delete accident-monitor-vm --zone=asia-southeast1-a
```

## Cost Optimization

- **f1-micro**: $0.006/hour (~$4.35/month) - Good for testing
- **e1-small**: $0.025/hour (~$18.25/month) - Recommended for production
- **Region**: Use `asia-southeast1` (Singapore) for best performance

## Troubleshooting

1. **Service won't start**: Check logs with `sudo journalctl -u accident-monitor.service`
2. **No accidents detected**: Check if bot can access @sgaccident channel
3. **High CPU usage**: Consider upgrading to e1-small or e1-medium
4. **Network issues**: Ensure VM has internet access and correct firewall rules

## Security Notes

- The VM runs with minimal privileges
- Bot token is in the code (consider using environment variables for production)
- Logs are automatically rotated to prevent disk space issues
- Service automatically restarts if it crashes