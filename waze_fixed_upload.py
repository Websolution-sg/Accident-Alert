#!/usr/bin/env python3
"""
FIXED Waze monitoring with consistent Singapore timezone
"""
import requests
import json
import datetime
import sys
import os
import time
from datetime import timezone, timedelta

# Singapore timezone (UTC+8)
SGT = timezone(timedelta(hours=8))

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHAT_ID = "-1003683261194"
MONITOR_INTERVAL = 60
PROCESSED_FILE = "/tmp/processed_waze_accidents.json"

def load_processed_accidents():
    try:
        with open(PROCESSED_FILE, 'r') as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_processed_accidents(processed_set):
    try:
        with open(PROCESSED_FILE, 'w') as f:
            json.dump(list(processed_set), f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving: {e}")
        return False

def generate_unique_id(accident):
    """FIXED: Generate consistent unique ID using Singapore timezone"""
    location = accident.get('location', {})
    lat = location.get('y')
    lon = location.get('x')
    pub_millis = accident.get('pubMillis', 0)
    
    if lat and lon and pub_millis:
        # FIXED: Always convert UTC to SGT consistently  
        utc_time = datetime.datetime.fromtimestamp(pub_millis / 1000, tz=timezone.utc)
        sgt_time = utc_time.astimezone(SGT)
        time_hour = sgt_time.strftime('%Y%m%d_%H')
        return f"waze_coord_{lat:.3f}_{lon:.3f}_{time_hour}"
    elif lat and lon:
        # FIXED: Use SGT consistently
        current_sgt = datetime.datetime.now(SGT)
        time_hour = current_sgt.strftime('%Y%m%d_%H')
        return f"waze_coord_{lat:.3f}_{lon:.3f}_{time_hour}"
    else:
        # FIXED: Use SGT consistently
        street = accident.get('street', '')
        city = accident.get('city', '')
        current_sgt = datetime.datetime.now(SGT)
        time_hour = current_sgt.strftime('%Y%m%d_%H')
        return f"waze_text_{street}_{city}_{time_hour}"

def get_waze_alerts():
    url = "https://www.waze.com/row-partnerhub-api/partners/10542088-7947-4b98-8dc0-e136fc424af1/waze-feeds/alerts"
    params = {
        "left": "103.6920", "bottom": "1.1304",
        "right": "104.0120", "top": "1.4504"
    }
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return [alert for alert in data.get('alerts', []) if alert.get('type') == 'ACCIDENT']
    except Exception as e:
        print(f"Error fetching Waze data: {e}")
        return []

def format_accident_message(accident):
    location = accident.get('location', {})
    lat = location.get('y')
    lon = location.get('x')
    street = accident.get('street', 'Unknown location')
    city = accident.get('city', 'Singapore')
    pub_millis = accident.get('pubMillis', 0)
    
    if pub_millis:
        # FIXED: Convert to SGT consistently
        utc_time = datetime.datetime.fromtimestamp(pub_millis / 1000, tz=timezone.utc)
        sgt_time = utc_time.astimezone(SGT)
        time_str = sgt_time.strftime('%Y-%m-%d %H:%M:%S SGT')
    else:
        time_str = datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')
    
    message = f"🚨 *WAZE ACCIDENT ALERT*\n\n"
    message += f"📍 *Location:* {street}\n"
    if city and city != street:
        message += f"🏙️ *Area:* {city}\n"
    message += f"🕐 *Time:* {time_str}\n"
    
    if lat and lon:
        message += f"🗺️ *Coordinates:* {lat:.6f}, {lon:.6f}\n"
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        message += f"🔗 *Maps:* {maps_url}\n"
    
    message += f"📡 *Source:* Waze Community Reports"
    return message

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False

def main():
    print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] 🚨 FIXED Waze Monitor Started")
    print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] ✅ TIMEZONE FIX: Consistent Singapore timezone")
    print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] 🔧 Fixed duplicate prevention logic")
    
    processed_accidents = load_processed_accidents()
    print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] 📋 Loaded {len(processed_accidents)} processed accidents")
    
    while True:
        try:
            print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] 🔍 Checking for new Waze accidents...")
            accidents = get_waze_alerts()
            print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] 📊 Found {len(accidents)} Waze accidents")
            
            new_accidents_count = 0
            for accident in accidents:
                accident_id = generate_unique_id(accident)
                if accident_id not in processed_accidents:
                    print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] 🆕 NEW accident: {accident_id}")
                    message = format_accident_message(accident)
                    if send_telegram_message(message):
                        processed_accidents.add(accident_id)
                        new_accidents_count += 1
                        print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] ✅ Sent: {accident_id}")
                    else:
                        print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] ❌ Failed to send: {accident_id}")
                else:
                    print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] 🔄 Already processed: {accident_id}")
            
            if new_accidents_count > 0:
                if save_processed_accidents(processed_accidents):
                    print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] 💾 Processed list updated ({len(processed_accidents)} total)")
            
            print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] 📈 Summary: {new_accidents_count} new accidents sent")
            
        except KeyboardInterrupt:
            print(f"\n[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] 🛑 Monitor stopped by user")
            break
        except Exception as e:
            print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] ❌ Error in monitoring loop: {e}")
        
        print(f"[{datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S %Z')}] ⏳ Waiting {MONITOR_INTERVAL} seconds...")
        time.sleep(MONITOR_INTERVAL)

if __name__ == "__main__":
    main()