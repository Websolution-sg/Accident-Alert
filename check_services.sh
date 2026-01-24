#!/bin/bash
echo "=== Checking Google Cloud VM Services ==="
echo "Date: $(date)"
echo

echo "=== Service Status ==="
sudo systemctl status accident-monitor accident-monitor-secondary --no-pager
echo

echo "=== Running Python Processes ==="
ps aux | grep python3 | grep -v grep
echo

echo "=== Recent Service Logs (Primary) ==="
sudo journalctl -u accident-monitor --since="5 minutes ago" --no-pager | tail -5
echo

echo "=== Recent Service Logs (Secondary) ==="
sudo journalctl -u accident-monitor-secondary --since="5 minutes ago" --no-pager | tail -5
echo

echo "=== Network Test ==="
python3 -c "import requests; print('Testing connectivity...'); r = requests.get('https://httpbin.org/get', timeout=10); print(f'HTTP Status: {r.status_code}')" 2>/dev/null || echo "Network test failed"
echo

echo "=== Memory Usage ==="
free -h
echo

echo "=== Done ==="