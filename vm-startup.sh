#!/bin/bash

# Startup script for Google Cloud VM
# This script sets up the cleaned accident monitoring system

# Update system
apt-get update -y
apt-get install -y python3 python3-pip

# Install Python dependencies
pip3 install requests==2.31.0 pytz==2023.3

# Create application directory
mkdir -p /home/accident-monitor
cd /home/accident-monitor

# Create the monitoring script with the cleaned version
cat > waze_accident_monitor.py << 'EOF'