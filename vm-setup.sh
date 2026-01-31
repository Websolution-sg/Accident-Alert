#!/bin/bash
# Google Cloud VM Startup Script for Singapore Accident Monitor

# Update system
sudo apt-get update -y

# Install Python 3 and pip if not already installed
sudo apt-get install -y python3 python3-pip git

# Create application directory
sudo mkdir -p /opt/accident-monitor
cd /opt/accident-monitor

# Copy the monitoring script (you'll upload this manually or via git)
# For now, we'll create a placeholder
echo "Upload vm_accident_monitor.py to /opt/accident-monitor/"

# Install Python dependencies
cat > requirements.txt << EOF
requests==2.31.0
pytz==2023.3
EOF

sudo pip3 install -r requirements.txt

# Create systemd service file
sudo tee /etc/systemd/system/accident-monitor.service > /dev/null << EOF
[Unit]
Description=Singapore Accident Monitor Service
After=network.target

[Service]
Type=simple
User=nobody
WorkingDirectory=/opt/accident-monitor
ExecStart=/usr/bin/python3 /opt/accident-monitor/vm_accident_monitor.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

# Environment variables (optional)
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable accident-monitor.service

# Create log rotation
sudo tee /etc/logrotate.d/accident-monitor > /dev/null << EOF
/tmp/accident_monitor.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF

echo "Setup complete! To start the service:"
echo "1. Upload vm_accident_monitor.py to /opt/accident-monitor/"
echo "2. Run: sudo systemctl start accident-monitor.service"
echo "3. Check status: sudo systemctl status accident-monitor.service"
echo "4. View logs: sudo journalctl -u accident-monitor.service -f"