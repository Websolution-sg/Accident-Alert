#!/bin/bash

echo "=== Finding and Stopping Duplicate Monitoring Processes ==="

# Check current processes
echo "Current monitoring processes:"
ps aux | grep -E 'monitor|accident' | grep python

# Kill accident_monitor.py if running
echo "Stopping accident_monitor.py process..."
sudo pkill -f accident_monitor.py

# Kill any other accident monitoring processes except simple_waze_monitor.py
echo "Stopping any other accident monitoring processes..."
sudo pkill -f "python.*accident" | grep -v simple_waze

# Wait a moment
sleep 2

# Check what's left running
echo "Remaining monitoring processes:"
ps aux | grep -E 'monitor|accident' | grep python

echo "=== Duplicate monitoring cleanup completed ==="