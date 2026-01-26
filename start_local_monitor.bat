@echo off
REM Accident Monitor - Local Backup Startup Script
REM Use this script to run the accident monitor locally when Google Cloud is down

echo ========================================
echo Singapore Accident Monitor - Local Mode  
echo ========================================
echo.
echo Starting local accident monitoring...
echo Press Ctrl+C to stop
echo.

REM Activate Python virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating Python virtual environment...
    call .venv\Scripts\activate.bat
)

REM Run the accident monitor
python waze_accident_monitor_latest.py

pause