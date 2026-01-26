@echo off
REM Simple Web-Based Deployment for Google Cloud VM

echo.
echo *** SIMPLE GOOGLE CLOUD VM DEPLOYMENT ***
echo ==========================================
echo.
echo Since direct SSH connection failed, here's the EASIEST way to deploy:
echo.
echo 1. OPEN TWO WINDOWS:
echo    - This PowerShell window (to copy the code)
echo    - Google Cloud Console in your browser
echo.
echo 2. COPY THE NEW CODE:
pause
type DEPLOY_THIS_TO_VM.py | clip
echo.
echo *** CODE COPIED TO CLIPBOARD! ***
echo.
echo 3. NOW GO TO GOOGLE CLOUD:
echo    - Open: https://console.cloud.google.com
echo    - Go to: Compute Engine ^> VM instances
echo    - Find: waze-monitor
echo    - Click: SSH (opens web terminal)
echo.
echo 4. IN THE WEB TERMINAL, RUN:
echo.
echo    sudo systemctl stop accident-monitor
echo    cp ~/waze_accident_monitor.py ~/backup_today.py  
echo    nano ~/waze_accident_monitor.py
echo.
echo    Then:
echo    - Press Ctrl+A to select all
echo    - Press Delete to clear
echo    - Press Ctrl+Shift+V to paste (or right-click ^> Paste)
echo    - Press Ctrl+X, then Y, then Enter to save
echo.
echo 5. RESTART THE SERVICE:
echo.
echo    sudo systemctl start accident-monitor
echo    sudo systemctl status accident-monitor
echo    sudo journalctl -u accident-monitor -f
echo.
echo *** The new code is already in your clipboard! ***
echo Go to Google Cloud Console now and follow steps 3-5.
echo.
pause