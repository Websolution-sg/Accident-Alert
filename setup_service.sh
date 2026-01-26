#!/bin/bash

# Simple deployment script
echo "Creating systemd service and starting monitoring..."

# Create service file
sudo tee /etc/systemd/system/waze-accident-monitor.service > /dev/null <<EOF
[Unit]
Description=Waze Accident Monitor - Secondary Channel
After=network.target

[Service]
Type=simple
User=USER
WorkingDirectory=/home/USER
ExecStart=/usr/bin/python3 /home/USER/waze_accident_monitor.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable waze-accident-monitor
sudo systemctl start waze-accident-monitor
sudo systemctl status waze-accident-monitor

echo "Service configured and started!"
echo "Check logs with: sudo journalctl -u waze-accident-monitor -f"