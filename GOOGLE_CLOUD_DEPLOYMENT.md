# Google Cloud VM Deployment Guide

Deploy your Enhanced Accident Monitor to Google Cloud VM for 24/7 operation without keeping your local PC running.

## 🚀 Quick Deployment

### Windows Users
```cmd
deploy_google_cloud.bat
```

### Linux/Mac Users
```bash
chmod +x deploy_google_cloud.sh
./deploy_google_cloud.sh
```

## 📋 Prerequisites

### 1. Google Cloud Account
- Create account at https://cloud.google.com
- Enable billing (required for VM creation)
- $300 free credits for new users

### 2. Google Cloud SDK
- Download from https://cloud.google.com/sdk/docs/install
- Run `gcloud auth login` to authenticate
- Run `gcloud config set project YOUR_PROJECT_ID`

### 3. Local Files
- `waze_accident_monitor.py`
- `waze_accident_monitor_secondary.py`
- `requirements.txt`

## 🎯 What Gets Deployed

### VM Specifications
- **Machine Type:** e2-micro (Free tier eligible)
- **OS:** Ubuntu 22.04 LTS
- **Location:** Singapore (asia-southeast1-a)
- **Storage:** 10GB SSD
- **Cost:** ~$0.40/month (or free with credits)

### Services Created
- **Primary Service:** accident-monitor-primary
  - Bot: `8339261439:AAG1DdDGnd_vY6QPBk9zsZFEL9obtncSXQA`
  - Channel: `-1003329968129`
  
- **Secondary Service:** accident-monitor-secondary
  - Bot: `8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U`
  - Channel: `-1003683261194`

## 🔧 VM Management

### Connect to VM
```bash
gcloud compute ssh accident-monitor --zone=asia-southeast1-a
```

### Service Management
```bash
# Check status
sudo systemctl status accident-monitor-primary accident-monitor-secondary

# View logs
sudo journalctl -u accident-monitor-primary -u accident-monitor-secondary -f

# Stop services
sudo systemctl stop accident-monitor-primary accident-monitor-secondary

# Start services
sudo systemctl start accident-monitor-primary accident-monitor-secondary

# Restart services
sudo systemctl restart accident-monitor-primary accident-monitor-secondary
```

### Remote Management (from your local PC)
```bash
# Check service status remotely
gcloud compute ssh accident-monitor --zone=asia-southeast1-a --command="sudo systemctl status accident-monitor-primary accident-monitor-secondary --no-pager"

# View recent logs remotely
gcloud compute ssh accident-monitor --zone=asia-southeast1-a --command="sudo journalctl -u accident-monitor-primary -u accident-monitor-secondary -n 50 --no-pager"

# Restart services remotely
gcloud compute ssh accident-monitor --zone=asia-southeast1-a --command="sudo systemctl restart accident-monitor-primary accident-monitor-secondary"
```

## 📊 Monitoring & Maintenance

### Check System Resources
```bash
# Memory usage
free -h

# Disk usage
df -h

# System uptime
uptime

# Process status
htop
```

### Update Application Code
```bash
# Upload new files from local PC
gcloud compute scp waze_accident_monitor.py accident-monitor:/home/accident-monitor/app/ --zone=asia-southeast1-a
gcloud compute scp waze_accident_monitor_secondary.py accident-monitor:/home/accident-monitor/app/ --zone=asia-southeast1-a

# Restart services to use new code
gcloud compute ssh accident-monitor --zone=asia-southeast1-a --command="sudo systemctl restart accident-monitor-primary accident-monitor-secondary"
```

## 💰 Cost Management

### Free Tier Benefits
- **e2-micro VM:** 744 hours/month free (24/7 operation)
- **30GB storage:** Free allowance
- **1GB network egress:** Free per month

### Estimated Costs (after free tier)
- **VM:** $0 (within free tier limits)
- **Storage:** ~$0.40/month for 10GB SSD
- **Network:** <$1/month for API calls
- **Total:** ~$1-2/month maximum

### Cost Optimization
```bash
# Stop VM when not needed (saves compute costs)
gcloud compute instances stop accident-monitor --zone=asia-southeast1-a

# Start VM when needed
gcloud compute instances start accident-monitor --zone=asia-southeast1-a

# Delete VM completely (if no longer needed)
gcloud compute instances delete accident-monitor --zone=asia-southeast1-a
```

## 🔐 Security Best Practices

### Firewall Configuration
The VM is configured with minimal access:
- Only outbound connections allowed
- No incoming ports opened (only SSH)
- Google Cloud firewall protection

### User Security
- Services run under dedicated `accident-monitor` user
- No root privileges for application
- Automatic security updates enabled

## 🛠️ Troubleshooting

### Service Not Starting
```bash
# Check service logs for errors
sudo journalctl -u accident-monitor-primary -n 20

# Check if Python files are present
ls -la /home/accident-monitor/app/

# Test Python script manually
cd /home/accident-monitor/app/
python3 waze_accident_monitor.py
```

### Network Issues
```bash
# Test internet connectivity
ping google.com

# Test Telegram API access
curl -s "https://api.telegram.org/bot8339261439:AAG1DdDGnd_vY6QPBk9zsZFEL9obtncSXQA/getMe"

# Test Waze API access
curl -s "https://www.waze.com/live-map/api/georss?bottom=1.1&left=103.6&right=104.1&top=1.5&env=row&types=alerts"
```

### VM Performance Issues
```bash
# Check memory usage
free -h

# Check disk space
df -h

# Check system load
htop

# View system logs
sudo journalctl -n 50
```

## 🔄 Backup & Recovery

### Application Backup
```bash
# Backup application files
gcloud compute scp accident-monitor:/home/accident-monitor/app/* ./backup/ --zone=asia-southeast1-a --recurse

# Backup systemd service files
gcloud compute ssh accident-monitor --zone=asia-southeast1-a --command="sudo cp /etc/systemd/system/accident-monitor-*.service /tmp/"
gcloud compute scp accident-monitor:/tmp/accident-monitor-*.service ./backup/ --zone=asia-southeast1-a
```

### VM Snapshots
```bash
# Create VM snapshot
gcloud compute disks snapshot accident-monitor --zone=asia-southeast1-a --snapshot-names=accident-monitor-backup

# List snapshots
gcloud compute snapshots list

# Restore from snapshot (create new VM)
gcloud compute instances create accident-monitor-restored --zone=asia-southeast1-a --source-snapshot=accident-monitor-backup
```

## 🎉 Benefits

✅ **24/7 Operation** - Runs continuously without your PC
✅ **Auto-Restart** - Services restart automatically if they crash
✅ **Free Tier** - Runs within Google Cloud free tier limits
✅ **Reliable** - Google's enterprise-grade infrastructure
✅ **Remote Management** - Control everything from anywhere
✅ **Automatic Updates** - Security updates applied automatically
✅ **Scalable** - Easy to upgrade if needed

Your Enhanced Accident Monitor will now run independently on Google Cloud, monitoring both channels 24/7 with smart duplicate prevention!