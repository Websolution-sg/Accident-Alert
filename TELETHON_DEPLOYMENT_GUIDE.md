Is # Telethon-Only VM Deployment Guide

🚀 **Complete migration from dual Waze+Telethon monitoring to Telethon-only real-time monitoring**

## ✅ Pre-Deployment Checklist

- [x] **VM Status**: `sg-accident-monitor` is running in `us-central1-a`
- [x] **Session File**: `pukiboi_unlocked.session` is working and authorized  
- [x] **Channel Access**: Can access @sgaccident source and target channels
- [x] **Scripts Ready**: All deployment files prepared
- [x] **Requirements**: Telethon-only dependencies defined

## 📋 What's Been Prepared

### 🆕 New Files Created
1. **[requirements-telethon-only.txt](requirements-telethon-only.txt)** - Lightweight Python dependencies
2. **[accident-monitor-telethon.service](accident-monitor-telethon.service)** - Systemd service configuration
3. **[deploy-telethon-only.sh](deploy-telethon-only.sh)** - Complete deployment script
4. **[prepare_vm_session.py](prepare_vm_session.py)** - Session testing and preparation

### 🔄 Existing Files to Use
- **[clean_telethon_monitor.py](clean_telethon_monitor.py)** - Main Telethon monitoring script
- **[pukiboi_unlocked.session](pukiboi_unlocked.session)** - Working Telethon session file

## 🚀 Deployment Steps

### Step 1: Make deployment script executable
```bash
chmod +x deploy-telethon-only.sh
```

### Step 2: Run deployment
```bash
./deploy-telethon-only.sh
```

### Step 3: Monitor deployment
The script will automatically:
1. Stop existing Waze + Telethon services
2. Upload Telethon-only files to VM
3. Install lightweight dependencies
4. Configure systemd service
5. Test Telethon connection
6. Start real-time monitoring
7. Show status and logs

## 📊 What Changes

### ❌ REMOVED (Waze Browser Automation)
- Selenium, WebDriver dependencies (~200MB)
- Chrome browser automation
- 60-second polling intervals
- Browser memory overhead
- Waze web scraping complexity

### ✅ ADDED (Telethon Real-Time)
- Direct Telegram API access
- 0-1 second message forwarding
- Lightweight Python-only operation
- Real-time event handling
- Much lower resource usage

## 🔧 Post-Deployment Management

### Check service status
```bash
gcloud compute ssh sg-accident-monitor --zone=us-central1-a --command="sudo systemctl status accident-monitor.service"
```

### View real-time logs
```bash
gcloud compute ssh sg-accident-monitor --zone=us-central1-a --command="sudo journalctl -u accident-monitor.service -f"
```

### Restart service if needed
```bash
gcloud compute ssh sg-accident-monitor --zone=us-central1-a --command="sudo systemctl restart accident-monitor.service"
```

### Check system resources
```bash
gcloud compute ssh sg-accident-monitor --zone=us-central1-a --command="free -h && ps aux | grep python"
```

## ⚡ Performance Benefits

| Aspect | Waze (Old) | Telethon (New) |
|--------|------------|----------------|
| **Latency** | 60 seconds | 0-1 seconds |
| **CPU Usage** | High (browser) | Low (Python only) |
| **Memory** | ~500MB+ | ~50MB |
| **Dependencies** | 20+ packages | 4 packages |
| **Reliability** | Web scraping | Direct API |
| **Maintenance** | Complex | Simple |

## 🔍 Troubleshooting

### If deployment fails:
1. Check VM is running: `gcloud compute instances list --filter=name~accident`
2. Verify session file works: Run session test locally first
3. Check VM connectivity: `gcloud compute ssh sg-accident-monitor --zone=us-central1-a`
4. Review logs: `sudo journalctl -u accident-monitor.service -n 50`

### If session stops working:
1. Session might be used simultaneously elsewhere
2. Create new session: `python create_telethon_session.py`
3. Re-run deployment with new session

## 📱 Expected Output

Once deployed successfully, you should see logs like:
```
[TIMESTAMP] TELETHON: Starting Clean Telethon Monitor
[TIMESTAMP] TELETHON: Connected to @sgaccident with @pukiboi credentials  
[TIMESTAMP] TELETHON: Real-time monitoring ACTIVE
[TIMESTAMP] TELETHON: Message #1 received (ID: 12345)
[TIMESTAMP] TELETHON: Message forwarded (Total: 1)
```

## 🎯 Success Criteria

✅ **Service running**: `systemctl is-active accident-monitor.service` shows `active`  
✅ **Real-time forwarding**: New messages appear instantly in target channel  
✅ **Low resource usage**: Python process uses <100MB memory  
✅ **Stable operation**: Service stays running without restarts  
✅ **Clean logs**: No errors in `journalctl` output

---

**Ready to deploy!** Run `./deploy-telethon-only.sh` when you're ready to migrate to real-time Telethon monitoring.