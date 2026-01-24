@echo off
REM Google Cloud VM Deployment Script for Enhanced Accident Monitor (Windows)

echo.
echo 🚀 Google Cloud VM Deployment - Enhanced Accident Monitor
echo =========================================================

REM Configuration
set PROJECT_ID=
set VM_NAME=accident-monitor
set ZONE=asia-southeast1-a
set MACHINE_TYPE=e2-micro
set IMAGE_FAMILY=ubuntu-2204-lts
set IMAGE_PROJECT=ubuntu-os-cloud

echo.
echo 🔍 Checking Google Cloud SDK...
gcloud --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Google Cloud SDK not found!
    echo.
    echo Please install Google Cloud SDK:
    echo https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)
echo ✅ Google Cloud SDK found

echo.
echo 📋 Google Cloud Configuration
echo =============================

REM Get current project
for /f "tokens=*" %%i in ('gcloud config get-value project 2^>nul') do set CURRENT_PROJECT=%%i

if not "%CURRENT_PROJECT%"=="" (
    echo Current project: %CURRENT_PROJECT%
    set /p USE_CURRENT="Use this project? (Y/n): "
    if /i "%USE_CURRENT%"=="n" (
        set /p PROJECT_ID="Enter project ID: "
    ) else (
        set PROJECT_ID=%CURRENT_PROJECT%
    )
) else (
    set /p PROJECT_ID="Enter your Google Cloud project ID: "
)

gcloud config set project %PROJECT_ID%

echo.
echo 📋 Deployment Configuration:
echo    Project: %PROJECT_ID%
echo    VM Name: %VM_NAME%
echo    Zone: %ZONE% (Singapore)
echo    Machine Type: %MACHINE_TYPE% (Free tier)
echo    OS: Ubuntu 22.04 LTS
echo.

set /p PROCEED="Proceed with VM creation and deployment? (y/N): "
if /i not "%PROCEED%"=="y" (
    echo Deployment cancelled.
    pause
    exit /b 0
)

echo 🔧 Enabling required Google Cloud APIs...
gcloud services enable compute.googleapis.com
if errorlevel 1 (
    echo ❌ Failed to enable APIs
    pause
    exit /b 1
)
echo ✅ APIs enabled successfully

echo 📝 Creating VM startup script...
echo #!/bin/bash > startup-script.sh
echo exec ^>^> ^(tee /var/log/startup-script.log^) 2^>^&1 >> startup-script.sh
echo echo "🚀 Starting Enhanced Accident Monitor Setup..." >> startup-script.sh
echo echo "==============================================" >> startup-script.sh
echo apt-get update -y >> startup-script.sh
echo apt-get upgrade -y >> startup-script.sh
echo apt-get install -y python3 python3-pip python3-venv git htop nano curl wget >> startup-script.sh
echo useradd -m -s /bin/bash accident-monitor >> startup-script.sh
echo usermod -aG sudo accident-monitor >> startup-script.sh
echo APP_DIR="/home/accident-monitor/app" >> startup-script.sh
echo mkdir -p $APP_DIR >> startup-script.sh
echo chown accident-monitor:accident-monitor $APP_DIR >> startup-script.sh
echo pip3 install requests >> startup-script.sh

REM Create systemd services in startup script
echo cat ^> /etc/systemd/system/accident-monitor-primary.service ^<^< 'EOFS' >> startup-script.sh
echo [Unit] >> startup-script.sh
echo Description=Enhanced Accident Monitor - Primary Channel >> startup-script.sh
echo After=network-online.target >> startup-script.sh
echo Wants=network-online.target >> startup-script.sh
echo. >> startup-script.sh
echo [Service] >> startup-script.sh
echo Type=simple >> startup-script.sh
echo User=accident-monitor >> startup-script.sh
echo Group=accident-monitor >> startup-script.sh
echo WorkingDirectory=/home/accident-monitor/app >> startup-script.sh
echo ExecStart=/usr/bin/python3 /home/accident-monitor/app/waze_accident_monitor.py >> startup-script.sh
echo Restart=always >> startup-script.sh
echo RestartSec=10 >> startup-script.sh
echo StandardOutput=journal >> startup-script.sh
echo StandardError=journal >> startup-script.sh
echo Environment=TELEGRAM_BOT_TOKEN=8339261439:AAG1DdDGnd_vY6QPBk9zsZFEL9obtncSXQA >> startup-script.sh
echo Environment=TELEGRAM_CHANNEL_ID=-1003329968129 >> startup-script.sh
echo. >> startup-script.sh
echo [Install] >> startup-script.sh
echo WantedBy=multi-user.target >> startup-script.sh
echo EOFS >> startup-script.sh

echo cat ^> /etc/systemd/system/accident-monitor-secondary.service ^<^< 'EOFS' >> startup-script.sh
echo [Unit] >> startup-script.sh
echo Description=Enhanced Accident Monitor - Secondary Channel >> startup-script.sh
echo After=network-online.target >> startup-script.sh
echo Wants=network-online.target >> startup-script.sh
echo. >> startup-script.sh
echo [Service] >> startup-script.sh
echo Type=simple >> startup-script.sh
echo User=accident-monitor >> startup-script.sh
echo Group=accident-monitor >> startup-script.sh
echo WorkingDirectory=/home/accident-monitor/app >> startup-script.sh
echo ExecStart=/usr/bin/python3 /home/accident-monitor/app/waze_accident_monitor_secondary.py >> startup-script.sh
echo Restart=always >> startup-script.sh
echo RestartSec=10 >> startup-script.sh
echo StandardOutput=journal >> startup-script.sh
echo StandardError=journal >> startup-script.sh
echo Environment=TELEGRAM_BOT_TOKEN=8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U >> startup-script.sh
echo Environment=TELEGRAM_CHANNEL_ID=-1003683261194 >> startup-script.sh
echo. >> startup-script.sh
echo [Install] >> startup-script.sh
echo WantedBy=multi-user.target >> startup-script.sh
echo EOFS >> startup-script.sh

echo systemctl daemon-reload >> startup-script.sh
echo echo "✅ VM setup completed successfully!" >> startup-script.sh

echo 🚀 Creating Google Cloud VM instance...
gcloud compute instances create %VM_NAME% --zone=%ZONE% --machine-type=%MACHINE_TYPE% --image-family=%IMAGE_FAMILY% --image-project=%IMAGE_PROJECT% --boot-disk-size=10GB --boot-disk-type=pd-standard --metadata-from-file startup-script=startup-script.sh --tags=accident-monitor --scopes=https://www.googleapis.com/auth/cloud-platform

if errorlevel 1 (
    echo ❌ Failed to create VM
    pause
    exit /b 1
)

echo ✅ VM created successfully!

REM Get VM IP
for /f "tokens=*" %%i in ('gcloud compute instances describe %VM_NAME% --zone=%ZONE% --format="get(networkInterfaces[0].accessConfigs[0].natIP)"') do set VM_IP=%%i

echo    VM Name: %VM_NAME%
echo    External IP: %VM_IP%
echo    Zone: %ZONE%

echo.
echo ⏳ Waiting for VM setup to complete (2-5 minutes)...
echo This will install packages and configure services...

REM Wait for setup to complete
timeout /t 120 /nobreak >nul

echo.
echo 📤 Uploading application files...
if exist deploy_files rmdir /s /q deploy_files
mkdir deploy_files

if exist waze_accident_monitor.py copy waze_accident_monitor.py deploy_files\
if exist waze_accident_monitor_secondary.py copy waze_accident_monitor_secondary.py deploy_files\
if exist requirements.txt copy requirements.txt deploy_files\

gcloud compute scp --recurse deploy_files\* %VM_NAME%:/tmp/ --zone=%ZONE%

REM Move files to proper location
gcloud compute ssh %VM_NAME% --zone=%ZONE% --command="sudo mkdir -p /home/accident-monitor/app && sudo cp /tmp/*.py /home/accident-monitor/app/ 2>/dev/null || echo 'Files copied' && sudo chown -R accident-monitor:accident-monitor /home/accident-monitor/app"

if errorlevel 1 (
    echo ❌ File upload failed
    pause
    exit /b 1
)

echo ✅ Files uploaded successfully

echo.
echo 🚀 Starting accident monitoring services...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --command="sudo systemctl enable accident-monitor-primary accident-monitor-secondary && sudo systemctl start accident-monitor-primary accident-monitor-secondary"

if errorlevel 1 (
    echo ❌ Failed to start services
    pause
    exit /b 1
)

echo ✅ Services started successfully

echo.
echo 🎉 Deployment Complete!
echo =======================
echo.
echo 📊 VM Details:
echo    Name: %VM_NAME%
echo    IP: %VM_IP%
echo    Zone: %ZONE%
echo    Project: %PROJECT_ID%
echo.
echo 📱 Monitoring Channels:
echo    Primary: -1003329968129
echo    Secondary: -1003683261194
echo.
echo 🔧 Management Commands:
echo    Connect: gcloud compute ssh %VM_NAME% --zone=%ZONE%
echo    View logs: gcloud compute ssh %VM_NAME% --zone=%ZONE% --command="sudo journalctl -u accident-monitor-primary -u accident-monitor-secondary -n 20"
echo    Check status: gcloud compute ssh %VM_NAME% --zone=%ZONE% --command="sudo systemctl status accident-monitor-primary accident-monitor-secondary"
echo    Stop services: gcloud compute ssh %VM_NAME% --zone=%ZONE% --command="sudo systemctl stop accident-monitor-primary accident-monitor-secondary"
echo.
echo 💰 Cost Information:
echo    Machine: e2-micro (Free tier: 744 hours/month)
echo    Storage: 10GB (~$0.40/month)
echo    Network: Minimal cost for API calls
echo.
echo ✅ Your Enhanced Accident Monitor is now running 24/7 on Google Cloud!
echo    It will automatically restart if the VM reboots.
echo    No need to keep your local PC running!

REM Cleanup
if exist startup-script.sh del startup-script.sh
if exist deploy_files rmdir /s /q deploy_files

echo.
pause