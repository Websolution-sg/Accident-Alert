# Singapore Accident Monitor - Local Backup Instructions

## Overview
This folder contains a complete backup of your Singapore Accident Monitor system that runs on Google Cloud. Use this local version as a backup when the cloud service is unavailable.

## Files
- `waze_accident_monitor_latest.py` - Latest working version from Google Cloud
- `waze_accident_monitor_backup.py` - Exact copy of cloud version  
- `start_local_monitor.bat` - Easy startup script for Windows
- `processed_accidents.json` - Will be created to track processed accidents
- `telegram_offset.json` - Will be created to track Telegram message offsets

## Quick Start
1. **Double-click** `start_local_monitor.bat` to start the local monitor
2. **Press Ctrl+C** to stop the monitor when done
3. The system will automatically create tracking files to prevent duplicates

## Features (Same as Google Cloud)
- ✅ Singapore-only accident filtering
- ✅ Dual source monitoring (Waze API + @sgaccident channel)
- ✅ Advanced duplicate prevention
- ✅ Malaysia location filtering  
- ✅ Clean message formatting without "🚨 Accident Alert"
- ✅ Google Maps and Waze navigation links
- ✅ Cross-source duplicate detection

## Configuration
- **Bot Token**: 8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U
- **Target Channel**: -1003683261194  
- **Source Channel**: -1001486947378 (@sgaccident)
- **Monitoring Interval**: 30 seconds
- **Singapore Bounds**: Lat 1.1496-1.4784, Lon 103.6065-104.0853

## When to Use Local Backup
- Google Cloud service is down
- Cloud VM is not responding  
- Network issues with cloud provider
- Testing new features locally first
- Emergency backup scenarios

## Notes
- Only run LOCAL OR CLOUD, never both at the same time to avoid duplicates
- Local version will create its own tracking files  
- Stop local monitor before restarting cloud service
- Same bot token works for both local and cloud versions

## Last Updated
Version synced with Google Cloud on: January 25, 2026
Includes all latest fixes: country code support, location detection, duplicate prevention