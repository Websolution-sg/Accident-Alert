@echo off
echo 🚀 Starting Dual Accident Alert System
echo =====================================
echo.
echo Channel 1: -1003329968129 (Primary)
echo Channel 2: -1003683261194 (Secondary)
echo.

echo Starting Primary Instance (Channel 1)...
start "Accident Monitor - Primary" python waze_accident_monitor.py

timeout /t 3 /nobreak >nul

echo Starting Secondary Instance (Channel 2)...
start "Accident Monitor - Secondary" python waze_accident_monitor_secondary.py

echo.
echo ✅ Both accident monitoring systems are now running!
echo.
echo 📊 Monitor Status:
echo   • Primary Channel: -1003329968129
echo   • Secondary Channel: -1003683261194
echo   • Both monitoring: Waze API + @sgaccident channel
echo   • Duplicate prevention: Active on both instances
echo.
echo To stop both instances, close their terminal windows.
echo.
pause