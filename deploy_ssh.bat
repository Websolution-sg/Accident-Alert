@echo off
REM SSH Deployment Script for Enhanced Accident Monitor (Windows)

echo.
echo 🚀 SSH Deployment - Enhanced Accident Monitor
echo ==============================================

REM Configuration variables
set SERVER_IP=
set SERVER_USER=
set SSH_KEY=
set SERVER_PATH=

echo.
echo 📋 Server Configuration
echo =======================

if "%SERVER_IP%"=="" (
    set /p SERVER_IP="Enter server IP address: "
)

if "%SERVER_USER%"=="" (
    set /p SERVER_USER="Enter SSH username: "
)

if "%SSH_KEY%"=="" (
    set /p SSH_KEY="Enter SSH key path (leave empty for password auth): "
)

set SERVER_PATH=/home/%SERVER_USER%/accident-alert

echo.
echo 📋 Configuration Summary:
echo    Server: %SERVER_IP%
echo    User: %SERVER_USER%
echo    Deploy Path: %SERVER_PATH%
if "%SSH_KEY%"=="" (
    echo    SSH Key: Password authentication
) else (
    echo    SSH Key: %SSH_KEY%
)
echo.

pause

echo 🔍 Testing SSH connection...
if "%SSH_KEY%"=="" (
    ssh -o ConnectTimeout=10 %SERVER_USER%@%SERVER_IP% "echo Connection successful"
) else (
    ssh -i "%SSH_KEY%" -o ConnectTimeout=10 %SERVER_USER%@%SERVER_IP% "echo Connection successful"
)

if errorlevel 1 (
    echo ❌ SSH connection failed!
    echo Please check your server details and try again.
    pause
    exit /b 1
)

echo ✅ SSH connection successful!
echo.

set /p PROCEED="Proceed with deployment? (y/N): "
if /i not "%PROCEED%"=="y" (
    echo Deployment cancelled.
    pause
    exit /b 0
)

echo 📦 Creating deployment package...
if exist deploy_package rmdir /s /q deploy_package
mkdir deploy_package

REM Copy application files
copy waze_accident_monitor.py deploy_package\
copy waze_accident_monitor_secondary.py deploy_package\
copy requirements.txt deploy_package\
copy *.md deploy_package\ >nul 2>&1

REM Create systemd service file for primary
echo [Unit] > deploy_package\accident-monitor-primary.service
echo Description=Accident Monitor - Primary Channel >> deploy_package\accident-monitor-primary.service
echo After=network.target >> deploy_package\accident-monitor-primary.service
echo. >> deploy_package\accident-monitor-primary.service
echo [Service] >> deploy_package\accident-monitor-primary.service
echo Type=simple >> deploy_package\accident-monitor-primary.service
echo User=USER_PLACEHOLDER >> deploy_package\accident-monitor-primary.service
echo WorkingDirectory=PATH_PLACEHOLDER >> deploy_package\accident-monitor-primary.service
echo ExecStart=/usr/bin/python3 PATH_PLACEHOLDER/waze_accident_monitor.py >> deploy_package\accident-monitor-primary.service
echo Restart=always >> deploy_package\accident-monitor-primary.service
echo RestartSec=10 >> deploy_package\accident-monitor-primary.service
echo Environment=TELEGRAM_BOT_TOKEN=8339261439:AAG1DdDGnd_vY6QPBk9zsZFEL9obtncSXQA >> deploy_package\accident-monitor-primary.service
echo Environment=TELEGRAM_CHANNEL_ID=-1003329968129 >> deploy_package\accident-monitor-primary.service
echo. >> deploy_package\accident-monitor-primary.service
echo [Install] >> deploy_package\accident-monitor-primary.service
echo WantedBy=multi-user.target >> deploy_package\accident-monitor-primary.service

REM Create systemd service file for secondary
echo [Unit] > deploy_package\accident-monitor-secondary.service
echo Description=Accident Monitor - Secondary Channel >> deploy_package\accident-monitor-secondary.service
echo After=network.target >> deploy_package\accident-monitor-secondary.service
echo. >> deploy_package\accident-monitor-secondary.service
echo [Service] >> deploy_package\accident-monitor-secondary.service
echo Type=simple >> deploy_package\accident-monitor-secondary.service
echo User=USER_PLACEHOLDER >> deploy_package\accident-monitor-secondary.service
echo WorkingDirectory=PATH_PLACEHOLDER >> deploy_package\accident-monitor-secondary.service
echo ExecStart=/usr/bin/python3 PATH_PLACEHOLDER/waze_accident_monitor_secondary.py >> deploy_package\accident-monitor-secondary.service
echo Restart=always >> deploy_package\accident-monitor-secondary.service
echo RestartSec=10 >> deploy_package\accident-monitor-secondary.service
echo Environment=TELEGRAM_BOT_TOKEN=8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U >> deploy_package\accident-monitor-secondary.service
echo Environment=TELEGRAM_CHANNEL_ID=-1003683261194 >> deploy_package\accident-monitor-secondary.service
echo. >> deploy_package\accident-monitor-secondary.service
echo [Install] >> deploy_package\accident-monitor-secondary.service
echo WantedBy=multi-user.target >> deploy_package\accident-monitor-secondary.service

REM Create management scripts
echo #!/bin/bash > deploy_package\start_services.sh
echo echo "🚀 Starting Accident Monitor Services..." >> deploy_package\start_services.sh
echo sudo systemctl start accident-monitor-primary >> deploy_package\start_services.sh
echo sudo systemctl start accident-monitor-secondary >> deploy_package\start_services.sh
echo sudo systemctl enable accident-monitor-primary >> deploy_package\start_services.sh
echo sudo systemctl enable accident-monitor-secondary >> deploy_package\start_services.sh
echo echo "✅ Services started and enabled" >> deploy_package\start_services.sh

echo #!/bin/bash > deploy_package\stop_services.sh
echo echo "🛑 Stopping Accident Monitor Services..." >> deploy_package\stop_services.sh
echo sudo systemctl stop accident-monitor-primary >> deploy_package\stop_services.sh
echo sudo systemctl stop accident-monitor-secondary >> deploy_package\stop_services.sh
echo echo "✅ Services stopped" >> deploy_package\stop_services.sh

echo #!/bin/bash > deploy_package\logs.sh
echo echo "📋 Primary Channel Logs:" >> deploy_package\logs.sh
echo sudo journalctl -u accident-monitor-primary -n 20 --no-pager >> deploy_package\logs.sh
echo echo "" >> deploy_package\logs.sh
echo echo "📋 Secondary Channel Logs:" >> deploy_package\logs.sh
echo sudo journalctl -u accident-monitor-secondary -n 20 --no-pager >> deploy_package\logs.sh

echo 📤 Uploading files to server...
if "%SSH_KEY%"=="" (
    scp -r deploy_package %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/
) else (
    scp -i "%SSH_KEY%" -r deploy_package %SERVER_USER%@%SERVER_IP%:%SERVER_PATH%/
)

if errorlevel 1 (
    echo ❌ File upload failed!
    pause
    exit /b 1
)

echo ✅ Files uploaded successfully!

echo 🔧 Setting up server environment and services...
if "%SSH_KEY%"=="" (
    ssh %SERVER_USER%@%SERVER_IP% "sudo apt-get update -y && sudo apt-get install -y python3 python3-pip && cd %SERVER_PATH% && python3 -m pip install --user -r requirements.txt && sed -i 's|USER_PLACEHOLDER|%SERVER_USER%|g' *.service && sed -i 's|PATH_PLACEHOLDER|%SERVER_PATH%|g' *.service && sudo cp *.service /etc/systemd/system/ && sudo systemctl daemon-reload && chmod +x *.sh && ./start_services.sh"
) else (
    ssh -i "%SSH_KEY%" %SERVER_USER%@%SERVER_IP% "sudo apt-get update -y && sudo apt-get install -y python3 python3-pip && cd %SERVER_PATH% && python3 -m pip install --user -r requirements.txt && sed -i 's|USER_PLACEHOLDER|%SERVER_USER%|g' *.service && sed -i 's|PATH_PLACEHOLDER|%SERVER_PATH%|g' *.service && sudo cp *.service /etc/systemd/system/ && sudo systemctl daemon-reload && chmod +x *.sh && ./start_services.sh"
)

if errorlevel 1 (
    echo ❌ Server setup failed!
    pause
    exit /b 1
)

echo.
echo 🎉 Deployment Complete!
echo =======================
echo.
echo 📊 Server Details:
echo    • Server: %SERVER_IP%
echo    • Path: %SERVER_PATH%
echo    • Primary Channel: -1003329968129
echo    • Secondary Channel: -1003683261194
echo.
echo 🔧 Management Commands:
echo    • View logs: ssh %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && ./logs.sh"
echo    • Stop services: ssh %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && ./stop_services.sh"
echo    • Start services: ssh %SERVER_USER%@%SERVER_IP% "cd %SERVER_PATH% && ./start_services.sh"
echo.
echo ✅ Your Enhanced Accident Monitor is now running on %SERVER_IP%!
echo    Both channels are being monitored 24/7 automatically!

REM Cleanup
if exist deploy_package rmdir /s /q deploy_package

echo.
pause