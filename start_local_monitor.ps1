# Singapore Accident Monitor - Local Backup Startup Script
# Use this script to run the accident monitor locally when Google Cloud is down

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Singapore Accident Monitor - Local Mode" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting local accident monitoring..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>$null
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Please install Python first." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate Python virtual environment if it exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activating Python virtual environment..." -ForegroundColor Yellow
    & .venv\Scripts\Activate.ps1
}

# Check if the latest monitor file exists
if (-not (Test-Path "waze_accident_monitor_latest.py")) {
    Write-Host "ERROR: waze_accident_monitor_latest.py not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Run the accident monitor
Write-Host "Starting Singapore Accident Monitor..." -ForegroundColor Green
Write-Host "Monitoring Singapore accidents from Waze and @sgaccident channel" -ForegroundColor Cyan
Write-Host ""

try {
    python waze_accident_monitor_latest.py
} catch {
    Write-Host "ERROR: Failed to start accident monitor" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "Accident monitor stopped." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
}