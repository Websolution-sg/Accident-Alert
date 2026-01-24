@echo off
REM Enhanced Waze Accident Monitor - Google Cloud Deployment Script (Windows)
REM This script helps deploy the enhanced accident monitoring system to Google Cloud

echo.
echo 🚀 Enhanced Waze Accident Monitor - Google Cloud Deployment
echo ============================================================

REM Check if gcloud is installed
gcloud --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Google Cloud SDK is not installed.
    echo Please install it from: https://cloud.google.com/sdk/docs/install
    pause
    exit /b 1
)

echo ✅ Google Cloud SDK found

REM Get current project
for /f "tokens=*" %%i in ('gcloud config get-value project 2^>nul') do set PROJECT=%%i

echo 📋 Current project: %PROJECT%

if "%PROJECT%"=="" (
    echo ❌ No project set. Please set a project:
    echo gcloud config set project YOUR_PROJECT_ID
    pause
    exit /b 1
)

echo.
echo 🔄 Deployment Options:
echo 1. Deploy to App Engine (Serverless)
echo 2. Deploy to Cloud Run (Container)
echo 3. Show VM instructions
echo.
set /p choice="Choose deployment option (1-3): "

if "%choice%"=="1" goto appengine
if "%choice%"=="2" goto cloudrun
if "%choice%"=="3" goto vminfo
echo ❌ Invalid choice. Please select 1, 2, or 3.
pause
exit /b 1

:appengine
echo 🚀 Deploying to App Engine...
echo.
echo 📦 Features included:
echo    ✅ Monitors Waze API for Singapore accidents
echo    ✅ Monitors @sgaccident Telegram channel
echo    ✅ Extracts coordinates and creates map links
echo    ✅ Prevents duplicate alerts by address
echo    ✅ Auto-restarts if it crashes
echo.

REM Deploy to App Engine
gcloud app deploy --quiet

if errorlevel 0 (
    echo ✅ Deployment successful!
    echo.
    echo 📊 View your application:
    echo    • App Engine Console: https://console.cloud.google.com/appengine
    echo    • View Logs: gcloud app logs tail -s default
    echo    • Check Status: gcloud app versions list
    echo.
    echo 🎉 Your Enhanced Accident Monitor is now running on Google Cloud!
) else (
    echo ❌ Deployment failed. Check the error messages above.
)
goto end

:cloudrun
echo 🚀 Deploying to Cloud Run...

set SERVICE_NAME=accident-monitor
set REGION=asia-southeast1

echo 📦 Building container...
gcloud builds submit --tag gcr.io/%PROJECT%/%SERVICE_NAME%

echo 🚀 Deploying to Cloud Run...
gcloud run deploy %SERVICE_NAME% --image gcr.io/%PROJECT%/%SERVICE_NAME% --platform managed --region %REGION% --allow-unauthenticated --set-env-vars="TELEGRAM_BOT_TOKEN=8339261439:AAG1DdDGnd_vY6QPBk9zsZFEL9obtncSXQA,TELEGRAM_CHANNEL_ID=-1003329968129" --cpu=1 --memory=512Mi --timeout=3600 --max-instances=1 --min-instances=1

if errorlevel 0 (
    echo ✅ Cloud Run deployment successful!
    echo.
    echo 📊 Manage your service:
    echo    • Cloud Run Console: https://console.cloud.google.com/run
    echo    • View Logs: gcloud run services logs tail %SERVICE_NAME% --region=%REGION%
) else (
    echo ❌ Cloud Run deployment failed.
)
goto end

:vminfo
echo 🖥️  VM Deployment Instructions:
echo.
echo 1. Create a VM in Google Cloud Console
echo 2. SSH into the VM
echo 3. Run these commands:
echo.
echo    sudo apt-get update
echo    sudo apt-get install -y python3-pip git
echo    git clone https://github.com/Websolution-sg/Accident-Alert.git
echo    cd Accident-Alert
echo    pip3 install -r requirements.txt
echo    python3 waze_accident_monitor.py
echo.
echo 📖 See DEPLOYMENT.md for detailed VM setup instructions.

:end
echo.
echo 📚 For more information, see:
echo    • DEPLOYMENT.md - Detailed deployment guide
echo    • README.md - Application documentation
echo    • GitHub: https://github.com/Websolution-sg/Accident-Alert
echo.
pause