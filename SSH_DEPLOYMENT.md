# SSH Deployment Guide - Enhanced Accident Monitor

Deploy your Enhanced Accident Monitor to any Linux server using SSH.

## 🚀 Quick Start

### Windows Users
```cmd
deploy_ssh.bat
```

### Linux/Mac Users
```bash
chmod +x deploy_ssh.sh
./deploy_ssh.sh
```

## 📋 Prerequisites

### Local Machine
- SSH client installed
- SCP support
- Access to this repository

### Target Server
- Linux server (Ubuntu/Debian recommended)
- SSH access with sudo privileges
- Internet connectivity
- Python 3.7+ (will be installed if missing)

## 🔧 Deployment Process

The deployment script will:

1. **📡 Test SSH Connection**
   - Verify server connectivity
   - Validate credentials

2. **🛠️ Setup Server Environment**
   - Update system packages
   - Install Python 3 and pip
   - Install required system dependencies

3. **📦 Deploy Application**
   - Upload application files
   - Install Python dependencies
   - Create systemd service files

4. **⚙️ Configure Services**
   - Setup systemd services for both channels
   - Configure auto-start on boot
   - Start monitoring services

5. **✅ Verification**
   - Check service status
   - Display management commands

## 🎯 What Gets Deployed

### Primary Service
- **File:** `waze_accident_monitor.py`
- **Bot:** `8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U` (Active Bot)
- **Channel:** `-1003683261194` (Active Channel)
- **Service:** `accident-monitor-primary`

### Secondary Service
- **File:** `waze_accident_monitor_secondary.py`
- **Bot:** `8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U`
- **Channel:** `-1003683261194`
- **Service:** `accident-monitor-secondary`

## 🔧 Management Commands

Once deployed, use these SSH commands to manage your services:

### Service Control
```bash
# Start services
ssh user@server "cd /home/user/accident-alert && ./start_services.sh"

# Stop services
ssh user@server "cd /home/user/accident-alert && ./stop_services.sh"

# Check status
ssh user@server "sudo systemctl status accident-monitor-primary accident-monitor-secondary"
```

### View Logs
```bash
# Recent logs
ssh user@server "cd /home/user/accident-alert && ./logs.sh"

# Live logs (follow)
ssh user@server "sudo journalctl -u accident-monitor-primary -u accident-monitor-secondary -f"
```

### Direct systemctl Commands
```bash
# Individual service control
sudo systemctl start accident-monitor-primary
sudo systemctl start accident-monitor-secondary
sudo systemctl stop accident-monitor-primary
sudo systemctl stop accident-monitor-secondary

# View specific service logs
sudo journalctl -u accident-monitor-primary -f
sudo journalctl -u accident-monitor-secondary -f
```

## 🔒 SSH Authentication Options

### Password Authentication
- Simply provide username and server IP
- You'll be prompted for password during deployment

### SSH Key Authentication
- Provide path to your SSH private key
- More secure and automated

### Example with SSH Key
```bash
./deploy_ssh.sh --server 192.168.1.100 --user ubuntu --key ~/.ssh/my-key.pem
```

## 🌟 Server Requirements

### Minimum Specifications
- **RAM:** 512MB (1GB recommended)
- **CPU:** 1 vCPU
- **Storage:** 2GB free space
- **Network:** Internet connectivity

### Supported OS
- Ubuntu 18.04+
- Debian 9+
- CentOS 7+
- Any systemd-based Linux distribution

## 🔍 Troubleshooting

### Connection Issues
```bash
# Test SSH connection manually
ssh user@server "echo 'Connection test'"

# Check if server is reachable
ping server-ip
```

### Service Issues
```bash
# Check service status
sudo systemctl status accident-monitor-primary

# View detailed logs
sudo journalctl -u accident-monitor-primary -n 50

# Restart service
sudo systemctl restart accident-monitor-primary
```

### Python Dependencies
```bash
# Reinstall dependencies
cd /home/user/accident-alert
python3 -m pip install --user -r requirements.txt --force-reinstall
```

## 📊 Monitoring

### Service Status
Both services run as systemd services and will:
- ✅ Auto-start on server boot
- ✅ Auto-restart if they crash
- ✅ Log all activity to systemd journal
- ✅ Run with proper user permissions

### Health Checks
The services are monitored by systemd and will restart automatically if they fail.

### Resource Usage
Each instance typically uses:
- **Memory:** ~50-100MB
- **CPU:** <5% on average
- **Network:** Minimal (API calls only)

## 🎉 Benefits of SSH Deployment

✅ **Full Control** - Complete access to your server
✅ **Cost Effective** - Use any VPS provider
✅ **Scalable** - Easy to modify and extend
✅ **Transparent** - Full visibility into operations
✅ **Flexible** - Deploy to multiple servers if needed

Your Enhanced Accident Monitor will run 24/7, monitoring both Waze API and @sgaccident channel, posting to both your Telegram channels with smart duplicate prevention!