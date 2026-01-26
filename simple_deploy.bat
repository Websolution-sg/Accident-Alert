@echo off
REM Simple deployment method - Copy content to clipboard for manual paste

echo 🚀 SIMPLE DEPLOYMENT METHOD
echo =============================
echo.
echo This script will help you deploy the Singapore Government API version
echo without requiring gcloud CLI installation.
echo.

echo 📋 DEPLOYMENT STEPS:
echo 1. The new code will be copied to your clipboard
echo 2. You'll get instructions to paste it manually
echo.

REM Copy the deployment file to clipboard
type DEPLOY_THIS_TO_VM.py | clip

echo ✅ Code copied to clipboard!
echo.
echo 📋 NOW FOLLOW THESE STEPS:
echo.
echo 1. Go to https://console.cloud.google.com
echo 2. Navigate to: Compute Engine ^> VM instances
echo 3. Find your VM 'waze-monitor' and click SSH
echo.
echo 4. In the VM terminal, run:
echo    sudo systemctl stop accident-monitor
echo    cp ~/waze_accident_monitor.py ~/backup_$(date +%%Y%%m%%d).py
echo    nano ~/waze_accident_monitor.py
echo.
echo 5. In nano editor:
echo    - Press Ctrl+A to select all
echo    - Press Delete to clear content  
echo    - Right-click and paste (or Ctrl+Shift+V)
echo    - Press Ctrl+X, then Y, then Enter to save
echo.
echo 6. Restart the service:
echo    sudo systemctl start accident-monitor
echo    sudo systemctl status accident-monitor
echo    sudo journalctl -u accident-monitor -f
echo.
echo 🎯 The new version includes:
echo    ✅ Singapore government traffic camera API
echo    ✅ Taxi availability analysis for congestion detection  
echo    ✅ Police website monitoring
echo    ✅ @sgaccident channel monitoring (continues working)
echo    ✅ Advanced Waze anti-blocking as backup
echo.
echo ✨ This solves the Waze 403 blocking issue!
echo.
pause