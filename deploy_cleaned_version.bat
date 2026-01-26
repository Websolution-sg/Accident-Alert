@echo off
REM Deploy Cleaned Accident Monitor to Google Cloud VM (Windows version)

echo 🚀 Deploying Cleaned Accident Monitor to Google Cloud VM
echo =======================================================

REM Configuration
set PROJECT_ID=verdant-petal-485213-h2
set VM_NAME=waze-monitor
set ZONE=asia-southeast1-a
set MACHINE_TYPE=e2-micro
set IMAGE_FAMILY=ubuntu-2204-lts
set IMAGE_PROJECT=ubuntu-os-cloud

echo [INFO] Checking Google Cloud configuration...
gcloud config set project %PROJECT_ID%

echo [INFO] Cleaning up old VM...
gcloud compute instances delete %VM_NAME% --zone=us-central1-c --quiet 2>nul

echo [INFO] Creating startup script...

REM Create the startup script
(
echo #!/bin/bash
echo.
echo # Update system
echo apt-get update
echo apt-get install -y python3 python3-pip git
echo.
echo # Create user for the application
echo useradd -m -s /bin/bash wazeuser
echo cd /home/wazeuser
echo.
echo # Install Python dependencies
echo pip3 install requests==2.31.0 pytz==2023.3
echo.
echo # Create the monitoring script
echo cat ^> waze_accident_monitor.py ^<^< 'PYTHON_SCRIPT'
type waze_accident_monitor.py
echo PYTHON_SCRIPT
echo.
echo # Make script executable
echo chmod +x waze_accident_monitor.py
echo.
echo # Create systemd service
echo cat ^> /etc/systemd/system/waze-accident-monitor.service ^<^< 'SERVICE_FILE'
echo [Unit]
echo Description=Waze Accident Monitor - Secondary Channel
echo After=network.target
echo.
echo [Service]
echo Type=simple
echo User=wazeuser
echo WorkingDirectory=/home/wazeuser
echo ExecStart=/usr/bin/python3 waze_accident_monitor.py
echo Restart=always
echo RestartSec=10
echo StandardOutput=journal
echo StandardError=journal
echo.
echo [Install]
echo WantedBy=multi-user.target
echo SERVICE_FILE
echo.
echo # Enable and start the service
echo systemctl enable waze-accident-monitor
echo systemctl start waze-accident-monitor
echo.
echo # Set ownership
echo chown -R wazeuser:wazeuser /home/wazeuser
echo.
echo echo "Startup script completed. Service should be running."
) > startup-script.sh

echo [INFO] Creating new VM in Singapore region...

gcloud compute instances create %VM_NAME% ^
    --zone=%ZONE% ^
    --machine-type=%MACHINE_TYPE% ^
    --network-tier=PREMIUM ^
    --maintenance-policy=MIGRATE ^
    --provisioning-model=STANDARD ^
    --service-account=default ^
    --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append ^
    --tags=http-server,https-server ^
    --create-disk=auto-delete=yes,boot=yes,device-name=%VM_NAME%,image=projects/%IMAGE_PROJECT%/global/images/family/%IMAGE_FAMILY%,mode=rw,size=10,type=projects/%PROJECT_ID%/zones/%ZONE%/diskTypes/pd-balanced ^
    --no-shielded-secure-boot ^
    --shielded-vtpm ^
    --shielded-integrity-monitoring ^
    --labels=environment=production,app=accident-monitor ^
    --reservation-affinity=any ^
    --metadata-from-file startup-script=startup-script.sh

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] VM created successfully!
    echo.
    echo [INFO] Waiting for VM to start up and configure...
    timeout /t 60 /nobreak >nul
    
    echo [INFO] Checking service status...
    gcloud compute ssh %VM_NAME% --zone=%ZONE% --command="sudo systemctl status waze-accident-monitor"
    
    echo.
    echo ✅ Deployment completed!
    echo.
    echo 🎯 VM Details:
    echo    Name: %VM_NAME%
    echo    Zone: %ZONE%
    echo    Type: %MACHINE_TYPE%
    echo    Channel: -1003683261194
    echo    Bot: @WazeAccident_bot
    echo.
    echo 📊 Management Commands:
    echo    Check status: gcloud compute ssh %VM_NAME% --zone=%ZONE% --command="sudo systemctl status waze-accident-monitor"
    echo    View logs: gcloud compute ssh %VM_NAME% --zone=%ZONE% --command="sudo journalctl -u waze-accident-monitor -f"
    echo    Restart: gcloud compute ssh %VM_NAME% --zone=%ZONE% --command="sudo systemctl restart waze-accident-monitor"
    echo    Stop: gcloud compute instances stop %VM_NAME% --zone=%ZONE%
    echo.
) else (
    echo [ERROR] VM creation failed!
    exit /b 1
)

REM Cleanup
del startup-script.sh

echo 🎉 Deployment complete! Your accident monitor is now running 24x7 on Google Cloud.
pause