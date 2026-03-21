#!/bin/bash
# Waze Monitor Startup Script - FIXED VERSION

echo "=== WAZE MONITOR STARTUP SCRIPT ==="
echo "Time: $(date)"
echo "Timezone: $(timedatectl | grep 'Time zone')"

# Kill any existing waze processes
echo "Stopping existing waze processes..."
pkill -f waze 2>/dev/null
sleep 2

# Check available scripts
echo "Available scripts:"
ls -la /tmp/*waze* 2>/dev/null

# Create the FIXED waze monitor script directly
echo "Creating FIXED waze monitor script..."
cat > /tmp/waze_monitor_fixed.py << 'EOF'
#!/usr/bin/env python3
import requests, json, datetime, sys, time
from datetime import timezone, timedelta

SGT = timezone(timedelta(hours=8))
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHAT_ID = "-1003683261194"
PROCESSED_FILE = "/tmp/processed_waze_accidents.json"

def load_processed():
    try:
        with open(PROCESSED_FILE, 'r') as f:
            return set(json.load(f))
    except: return set()

def save_processed(pset):
    try:
        with open(PROCESSED_FILE, 'w') as f:
            json.dump(list(pset), f); return True
    except: return False

def unique_id(acc):
    loc = acc.get('location', {})
    lat, lon = loc.get('y'), loc.get('x')
    pub = acc.get('pubMillis', 0)
    if lat and lon and pub:
        # FIXED: UTC->SGT conversion
        utc_t = datetime.datetime.fromtimestamp(pub / 1000, tz=timezone.utc)
        sgt_t = utc_t.astimezone(SGT)
        hr = sgt_t.strftime('%Y%m%d_%H')
        return f"waze_coord_{lat:.3f}_{lon:.3f}_{hr}"
    elif lat and lon:
        hr = datetime.datetime.now(SGT).strftime('%Y%m%d_%H')
        return f"waze_coord_{lat:.3f}_{lon:.3f}_{hr}"
    else:
        st, ct = acc.get('street',''), acc.get('city','')
        hr = datetime.datetime.now(SGT).strftime('%Y%m%d_%H')
        return f"waze_text_{st}_{ct}_{hr}"

def get_alerts():
    try:
        url = "https://www.waze.com/row-partnerhub-api/partners/10542088-7947-4b98-8dc0-e136fc424af1/waze-feeds/alerts"
        params = {"left":"103.692","bottom":"1.1304","right":"104.012","top":"1.4504"}
        r = requests.get(url, params=params, timeout=30)
        return [a for a in r.json().get('alerts',[]) if a.get('type')=='ACCIDENT']
    except: return []

def format_msg(acc):
    loc = acc.get('location', {})
    lat, lon = loc.get('y'), loc.get('x')
    street = acc.get('street', 'Unknown')
    pub = acc.get('pubMillis', 0)
    if pub:
        utc_t = datetime.datetime.fromtimestamp(pub / 1000, tz=timezone.utc)
        time_str = utc_t.astimezone(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')
    else:
        time_str = datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')
    
    msg = f"🚨 *WAZE ACCIDENT*\n📍 {street}\n🕐 {time_str}\n"
    if lat and lon:
        msg += f"🗺️ https://www.google.com/maps?q={lat},{lon}\n"
    return msg + "📡 Waze Reports"

def send_msg(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={'chat_id':CHAT_ID,'text':msg,'parse_mode':'Markdown'})
        return r.status_code == 200
    except: return False

print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')}] FIXED Waze Monitor Started")
processed = load_processed()
print(f"Loaded {len(processed)} processed accidents")

while True:
    try:
        alerts = get_alerts()
        print(f"[{datetime.datetime.now(SGT).strftime('%H:%M:%S')}] Found {len(alerts)} accidents")
        new = 0
        for a in alerts:
            aid = unique_id(a)
            if aid not in processed:
                if send_msg(format_msg(a)):
                    processed.add(aid); new += 1
                    print(f"Sent: {aid}")
        if new > 0: save_processed(processed)
        print(f"Summary: {new} new accidents")
    except KeyboardInterrupt: break
    except Exception as e: print(f"Error: {e}")
    time.sleep(60)
EOF

# Make executable
chmod +x /tmp/waze_monitor_fixed.py

# Start the fixed monitor
echo "Starting FIXED Waze monitor..."
nohup python3 /tmp/waze_monitor_fixed.py > /tmp/waze_fixed.log 2>&1 &

# Show status
sleep 3
echo "Process status:"
ps aux | grep waze_monitor_fixed | grep -v grep

echo "Recent log output:"
tail -5 /tmp/waze_fixed.log 2>/dev/null || echo "Log not available yet"

echo "=== STARTUP COMPLETE ==="