# Dual Channel Accident Alert System

This setup allows you to run the Enhanced Accident Monitoring System on **two separate Telegram channels simultaneously**.

## 🎯 Channel Configuration

### Primary Channel (Original)
- **Bot Token:** `8339261439:AAG1DdDGnd_vY6QPBk9zsZFEL9obtncSXQA`
- **Channel ID:** `-1003329968129`
- **File:** `waze_accident_monitor.py`
- **Config:** `app.yaml`

### Secondary Channel (New)
- **Bot Token:** `8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U`
- **Channel ID:** `-1003683261194`
- **File:** `waze_accident_monitor_secondary.py`
- **Config:** `app_secondary.yaml`

## 🚀 Local Testing

### Option 1: Run Both Instances at Once
```bash
# Windows - Automated start
start_dual_monitoring.bat

# Manual start
python waze_accident_monitor.py           # Terminal 1
python waze_accident_monitor_secondary.py # Terminal 2
```

### Option 2: Run Individual Instances
```bash
# Primary channel only
python waze_accident_monitor.py

# Secondary channel only  
python waze_accident_monitor_secondary.py
```

## ☁️ Google Cloud Deployment

### Deploy Primary Instance
```bash
gcloud app deploy app.yaml --service primary
```

### Deploy Secondary Instance
```bash
gcloud app deploy app_secondary.yaml --service secondary
```

### Deploy Both (Advanced)
```bash
# Deploy primary service
gcloud app deploy app.yaml --service primary --no-promote

# Deploy secondary service
gcloud app deploy app_secondary.yaml --service secondary --no-promote

# Check status
gcloud app services list
```

## 📊 Features (Both Instances)

✅ **Dual Source Monitoring**
- Monitors Waze API for real-time accidents
- Monitors @sgaccident Telegram channel

✅ **Smart Duplicate Prevention**
- Prevents same accident being posted twice
- Address normalization and comparison

✅ **Enhanced Messaging**
- Formatted accident alerts
- Google Maps and Waze navigation links
- Coordinate extraction from text

✅ **Robust Operation**
- 24/7 automated monitoring
- Error handling and auto-recovery
- Memory management

## 🔧 Configuration

Each instance maintains its own:
- Posted accident tracking
- Address duplicate prevention
- Message processing history
- API rate limiting

This ensures both channels operate independently without interference.

## 📈 Monitoring

### View Logs
```bash
# Primary instance
gcloud app logs tail -s primary

# Secondary instance  
gcloud app logs tail -s secondary
```

### Check Status
```bash
gcloud app services list
gcloud app versions list
```

## 🎉 Result

You now have **two independent accident monitoring systems** running simultaneously:
- Both monitor the same sources (Waze + @sgaccident)
- Each posts to its respective Telegram channel
- Smart duplicate prevention on each channel
- Fully automated 24/7 operation