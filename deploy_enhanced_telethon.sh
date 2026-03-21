#!/bin/bash
# Enhanced Telethon Monitor Deployment Script

echo "=== ENHANCED TELETHON DEPLOYMENT ==="
echo "Time: $(date)"
echo "Current directory: $(pwd)"

# Stop any existing telethon processes
echo "Stopping existing processes..."
pkill -f telethon 2>/dev/null
pkill -f telethon_monitor_updated.py 2>/dev/null
pkill -f telethon_waze_format.py 2>/dev/null
sleep 3

# Check available files
echo "Available Telethon files:"
ls -la /tmp/telethon* 2>/dev/null

# Start the enhanced monitor
echo "Starting enhanced Telethon monitor..."
cd /tmp
nohup python3 telethon_waze_format.py > telethon_enhanced.log 2>&1 &
sleep 5

# Check status
echo "Process status:"
ps aux | grep python3 | grep telethon | head -3

echo "Recent log output:"
tail -5 telethon_enhanced.log 2>/dev/null || echo "Log not available yet"

echo "=== DEPLOYMENT COMPLETE ==="