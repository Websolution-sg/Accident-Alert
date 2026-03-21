#!/usr/bin/env python3
"""
Waze monitoring with duplicate prevention and real-time filtering
Only posts NEW accidents that are less than 30 minutes old for real-time traffic alerts
"""
import requests
import json
import datetime
import sys
import os
import math
import time
from datetime import timezone, timedelta

# Singapore timezone (UTC+8)
SGT = timezone(timedelta(hours=8))
from datetime import timezone, timedelta

# Singapore timezone (UTC+8)
SGT = timezone(timedelta(hours=8))

# Ensure unbuffered output for systemd logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHAT_ID = "-1003683261194"

# Monitoring interval
MONITOR_INTERVAL = 60  # Check every 1 minute

# Age filtering - only post recent accidents (in minutes)
MAX_ACCIDENT_AGE_MINUTES = 15  # Only post accidents less than 15 minutes old

# Waze API Configuration
WAZE_API_URL = "https://www.waze.com/live-map/api/georss"
WAZE_BBOX = {
    'bottom': 1.1304753,
    'left': 103.6055424,
    'right': 104.0945619,
    'top': 1.4764671
}

# Singapore bounds for filtering
SINGAPORE_BOUNDS = {
    "north": 1.4784,
    "south": 1.1496,
    "east": 104.0853,
    "west": 103.6065
}

# Data storage for tracking posted accidents
PROCESSED_WAZE_FILE = "processed_waze_accidents.json"

def log_message(message):
    """Log messages with timestamp (Singapore Time)"""
    timestamp = datetime.datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S SGT")
    print(f"[{timestamp}] WAZE: {message}", flush=True)

def load_processed_waze_accidents():
    """Load processed Waze accident IDs"""
    try:
        if os.path.exists(PROCESSED_WAZE_FILE):
            with open(PROCESSED_WAZE_FILE, 'r') as f:
                return set(json.load(f))
    except Exception as e:
        log_message(f"Error loading processed accidents: {e}")
    return set()

def save_processed_waze_accidents(processed_ids):
    """Save processed Waze accident IDs"""
    try:
        with open(PROCESSED_WAZE_FILE, 'w') as f:
            json.dump(list(processed_ids), f)
    except Exception as e:
        log_message(f"Error saving processed accidents: {e}")

def is_within_singapore(lat, lon):
    """Check if coordinates are within Singapore bounds"""
    if not lat or not lon:
        return False
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        return (SINGAPORE_BOUNDS["south"] <= lat_f <= SINGAPORE_BOUNDS["north"] and 
                SINGAPORE_BOUNDS["west"] <= lon_f <= SINGAPORE_BOUNDS["east"])
    except (ValueError, TypeError):
        return False

def is_accident_recent(accident, max_age_minutes=MAX_ACCIDENT_AGE_MINUTES):
    """Check if accident is recent enough to post (real-time filtering)"""
    pub_millis = accident.get('pubMillis')
    if not pub_millis:
        # If no timestamp, consider it recent (better to post than miss)
        log_message("⚠️ Accident has no timestamp - considering it recent")
        return True
    
    try:
        # Convert to Singapore time for comparison
        utc_time = datetime.datetime.fromtimestamp(pub_millis / 1000, tz=timezone.utc)
        accident_time = utc_time.astimezone(SGT)
        current_time = datetime.datetime.now(SGT)
        
        # Calculate age in minutes
        age_minutes = (current_time - accident_time).total_seconds() / 60
        
        is_recent = age_minutes <= max_age_minutes
        
        if is_recent:
            log_message(f"✅ Accident is {age_minutes:.1f} min old - RECENT (posting)")
        else:
            log_message(f"🕒 Accident is {age_minutes:.1f} min old - TOO OLD (filtering out)")
            
        return is_recent
        
    except Exception as e:
        log_message(f"Error checking accident age: {e} - considering it recent")
        return True

def get_waze_accident_id(accident):
    """Generate unique ID for Waze accident to prevent duplicates"""
    location = accident.get('location', {})
    lat = location.get('y', 0)
    lon = location.get('x', 0)
    pub_millis = accident.get('pubMillis', 0)
    
    if lat and lon and pub_millis:
        # Round coordinates to catch nearby duplicates and group by hour
        utc_time = datetime.datetime.fromtimestamp(pub_millis / 1000)
        time_hour = utc_time.strftime('%Y%m%d_%H')
        return f"waze_coord_{lat:.3f}_{lon:.3f}_{time_hour}"
    elif lat and lon:
        # Fallback without timestamp
        current_time = datetime.datetime.now()
        time_hour = current_time.strftime('%Y%m%d_%H')
        return f"waze_coord_{lat:.3f}_{lon:.3f}_{time_hour}"
    else:
        # Fallback to street-based ID
        street = accident.get('street', '')
        city = accident.get('city', '')
        current_time = datetime.datetime.now()
        time_hour = current_time.strftime('%Y%m%d_%H')
        return f"waze_text_{street}_{city}_{time_hour}"

def get_waze_alerts():
    """Fetch alerts from Waze API for Singapore"""
    try:
        params = {
            'bottom': WAZE_BBOX['bottom'],
            'left': WAZE_BBOX['left'], 
            'right': WAZE_BBOX['right'],
            'top': WAZE_BBOX['top'],
            'env': 'row',
            'types': 'alerts,traffic'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.waze.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        
        response = requests.get(WAZE_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('alerts', [])
    except Exception as e:
        log_message(f"Error fetching Waze data: {e}")
        return []

def filter_waze_accidents(alerts):
    """Filter alerts to get only accidents in Singapore"""
    accident_types = ['ACCIDENT', 'ACCIDENT_MINOR', 'ACCIDENT_MAJOR']
    accidents = [
        alert for alert in alerts 
        if (alert.get('type', '').upper() in accident_types or 
            alert.get('subtype', '').upper() in accident_types) and
           (alert.get('country', '').upper() in ['SG', 'SN'] or 
            'SINGAPORE' in alert.get('city', '').upper())
    ]
    return accidents

def get_singapore_location_from_coords(lat, lon):
    """Get Singapore location name from coordinates using area mapping"""
    if not lat or not lon:
        return None
        
    # Singapore area mapping based on coordinate ranges
    singapore_areas = {
        # Central Region
        (1.2700, 1.3200, 103.8200, 103.8700): "Orchard Road area",
        (1.2800, 1.3200, 103.8400, 103.8800): "Marina Bay area", 
        (1.2900, 1.3100, 103.8500, 103.8600): "CBD/Raffles Place area",
        (1.3000, 1.3400, 103.8300, 103.8700): "Bugis/Little India area",
        
        # North Region  
        (1.4000, 1.4500, 103.7800, 103.8300): "Woodlands area",
        (1.3800, 1.4200, 103.8400, 103.8900): "Yishun area",
        (1.3600, 1.4000, 103.8200, 103.8800): "Ang Mo Kio area",
        (1.3700, 1.4100, 103.7900, 103.8400): "Sembawang area",
        
        # East Region
        (1.3200, 1.3600, 103.8800, 103.9300): "Tampines area",
        (1.3000, 1.3400, 103.9200, 103.9700): "Changi area", 
        (1.3100, 1.3500, 103.9000, 103.9500): "Pasir Ris area",
        (1.3200, 1.3600, 103.9300, 103.9800): "Bedok area",
        
        # West Region
        (1.3200, 1.3700, 103.6800, 103.7300): "Jurong West area",
        (1.3000, 1.3500, 103.7200, 103.7700): "Jurong East area",
        (1.3300, 1.3800, 103.7400, 103.7900): "Bukit Batok area",
        (1.3400, 1.3900, 103.7600, 103.8100): "Clementi area",
        
        # South Region
        (1.2700, 1.3100, 103.8000, 103.8500): "Tanjong Pagar area",
        (1.2600, 1.3000, 103.7800, 103.8300): "Sentosa/HarbourFront area",
    }
    
    # Check which area the coordinates fall into
    for (min_lat, max_lat, min_lon, max_lon), area_name in singapore_areas.items():
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return area_name
            
    # Fallback to general regions if no specific area found
    if lat > 1.38:
        return "Northern Singapore"
    elif lat < 1.29:
        return "Southern Singapore" 
    elif lon > 103.86:
        return "Eastern Singapore"
    elif lon < 103.77:
        return "Western Singapore"
    else:
        return "Central Singapore"

def get_singapore_expressway_from_coords(lat, lon):
    """Identify Singapore expressways from coordinates"""
    if not lat or not lon:
        return None
        
    # Major Singapore expressways coordinate ranges
    expressways = {
        # PIE (Pan Island Expressway) - runs east-west
        (1.31, 1.35, 103.65, 103.95): "PIE (Pan Island Expressway)",
        # CTE (Central Expressway) - runs north-south  
        (1.29, 1.42, 103.82, 103.86): "CTE (Central Expressway)",
        # AYE (Ayer Rajah Expressway) - southern route
        (1.26, 1.32, 103.72, 103.84): "AYE (Ayer Rajah Expressway)",
        # BKE (Bukit Timah Expressway) - northwest
        (1.33, 1.44, 103.76, 103.82): "BKE (Bukit Timah Expressway)",
        # TPE (Tampines Expressway) - northeast
        (1.33, 1.39, 103.87, 103.96): "TPE (Tampines Expressway)",
        # SLE (Seletar Expressway) - north
        (1.38, 1.43, 103.82, 103.89): "SLE (Seletar Expressway)",
        # ECP (East Coast Parkway) - southeast coastal
        (1.29, 1.32, 103.86, 103.96): "ECP (East Coast Parkway)",
        # KPE (Kallang-Paya Lebar Expressway) 
        (1.31, 1.36, 103.86, 103.91): "KPE (Kallang-Paya Lebar Expressway)",
    }
    
    # Find matching expressway
    for (min_lat, max_lat, min_lon, max_lon), expressway_name in expressways.items():
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            return expressway_name
            
    return None

def get_singapore_expressway_with_direction(lat, lon):
    """Get Singapore expressway with directional context and area information"""
    if not lat or not lon:
        return None
        
    # Expressway definitions with directional context
    # PIE (Pan Island Expressway) - runs east-west
    if 1.31 <= lat <= 1.35 and 103.65 <= lon <= 103.95:
        # Determine direction based on longitude position
        if lon < 103.78:
            direction = "towards Tuas"
        else:
            direction = "towards Changi"
        expressway = f"PIE {direction}"
        
    # CTE (Central Expressway) - runs north-south
    elif 1.29 <= lat <= 1.42 and 103.82 <= lon <= 103.86:
        # Determine direction based on latitude position  
        if lat < 1.35:
            direction = "towards town"
        else:
            direction = "towards Woodlands"
        expressway = f"CTE {direction}"
        
    # AYE (Ayer Rajah Expressway) - southern route, east-west
    elif 1.26 <= lat <= 1.32 and 103.72 <= lon <= 103.84:
        if lon < 103.78:
            direction = "towards Jurong"
        else:
            direction = "towards town"
        expressway = f"AYE {direction}"
        
    # BKE (Bukit Timah Expressway) - northwest, north-south
    elif 1.33 <= lat <= 1.44 and 103.76 <= lon <= 103.82:
        if lat < 1.38:
            direction = "towards town"
        else:
            direction = "towards Woodlands"
        expressway = f"BKE {direction}"
        
    # TPE (Tampines Expressway) - northeast, east-west
    elif 1.33 <= lat <= 1.39 and 103.87 <= lon <= 103.96:
        if lon < 103.91:
            direction = "towards SLE"
        else:
            direction = "towards Changi"
        expressway = f"TPE {direction}"
        
    # SLE (Seletar Expressway) - north, east-west
    elif 1.38 <= lat <= 1.43 and 103.82 <= lon <= 103.89:
        if lon < 103.85:
            direction = "towards BKE"
        else:
            direction = "towards TPE"
        expressway = f"SLE {direction}"
        
    # ECP (East Coast Parkway) - southeast coastal, east-west
    elif 1.29 <= lat <= 1.32 and 103.86 <= lon <= 103.96:
        if lon < 103.91:
            direction = "towards town"
        else:
            direction = "towards Changi"
        expressway = f"ECP {direction}"
        
    # KPE (Kallang-Paya Lebar Expressway) - generally north-south
    elif 1.31 <= lat <= 1.36 and 103.86 <= lon <= 103.91:
        if lat < 1.33:
            direction = "towards Marina Bay"
        else:
            direction = "towards Defu"
        expressway = f"KPE {direction}"
        
    else:
        return None
    
    # Add area context to expressway
    area = get_singapore_location_from_coords(lat, lon)
    if area and area not in expressway:
        return f"{expressway}, {area}"
    else:
        return expressway

def format_waze_accident_message(accident):
    """Format Waze accident using original simple format"""
    # Extract information
    street = accident.get('street', 'Unknown location')
    city = accident.get('city', 'Singapore')
    reported_by = accident.get('reportBy', 'Waze user')
    confidence = accident.get('confidence', 0)
    reliability = accident.get('reliability', 0)
    
    # Get coordinates
    location = accident.get('location', {})
    lat = location.get('y', 0)
    lon = location.get('x', 0)
    
    # Get timestamp
    pub_millis = accident.get('pubMillis', 0)
    if pub_millis:
        utc_time = datetime.datetime.fromtimestamp(pub_millis / 1000, tz=timezone.utc)
        sgt_time = utc_time.astimezone(SGT)
        report_time = sgt_time.strftime('%Y-%m-%d %H:%M:%S SGT')
    else:
        report_time = datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')
    
    # Format location - STREET NAME FIRST, then EXPRESSWAY with DIRECTIONAL CONTEXT, then AREA
    # New Priority Order: 1. Street Name 2. Expressway+Direction 3. Area Detection
    
    # Priority 1: Check for STREET NAME first (when available and meaningful)
    if street and street.lower() not in ['unknown location', 'unknown', ''] and len(street.strip()) > 2:
        if city and city != 'Singapore':
            location_text = f"{street}, {city}"
        else:
            location_text = street
    
    # Priority 2: EXPRESSWAY with DIRECTIONAL CONTEXT (if no good street name)
    elif lat and lon:
        expressway_info = get_singapore_expressway_with_direction(lat, lon)
        if expressway_info:
            # expressway_info returns: "PIE towards Changi, Tampines area"
            location_text = expressway_info
        # Priority 3: AREA DETECTION (if not on expressway)
        else:
            area = get_singapore_location_from_coords(lat, lon)
            if area:
                location_text = area
            else:
                location_text = f"coordinates {lat:.4f}, {lon:.4f}"
    
    # Priority 4: City name (if no coordinates)  
    elif city and city != 'Singapore':
        location_text = city
    
    # Final fallback
    else:
        location_text = "Unknown location"
    
    # Build message using original simple format
    message = f"Accident on {location_text}\n"
    message += f"🕐 Reported: {report_time}\n"
    message += f"👤 Reported by: {reported_by}\n"
    message += f"📈 Confidence: {confidence}/10\n"
    message += f"✅ Reliability: {reliability}/10\n\n"
    
    if lat and lon:
        google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        waze_url = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
        message += f"🗺️ [View on Google Maps ({lat:.6f}, {lon:.6f})]({google_maps_url})\n"
        message += f"🚗 [Open in Waze ({lat:.6f}, {lon:.6f})]({waze_url})"
    else:
        message += f"🗺️ Location coordinates not available"
    
    return message



def send_telegram_message(message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result['result']['message_id']
        else:
            log_message(f"Failed to send message: {response.status_code}")
            return None
    except Exception as e:
        log_message(f"Error sending message: {e}")
        return None

def process_waze_accidents():
    """Process Waze accidents - only post NEW & RECENT accidents (duplicate prevention + real-time filtering)"""
    log_message("Checking Waze for NEW & RECENT accidents...")
    
    processed_accidents = load_processed_waze_accidents()
    new_accidents = 0
    
    try:
        # Get Waze alerts
        alerts = get_waze_alerts()
        if not alerts:
            log_message("No Waze alerts received")
            return new_accidents
        
        # Filter for accidents
        accidents = filter_waze_accidents(alerts)
        log_message(f"Found {len(accidents)} Waze accidents")
        
        # Process accidents - only post NEW ones and RECENT ones
        for accident in accidents:
            # Generate unique ID for duplicate checking
            accident_id = get_waze_accident_id(accident)
            
            # Check if already processed (duplicate prevention)
            if accident_id in processed_accidents:
                continue
            
            # Check if accident is recent enough (real-time filtering)
            if not is_accident_recent(accident):
                log_message(f"🕒 Skipping old accident (ID: {accident_id})")
                continue
            
            # Check coordinates are in Singapore
            location = accident.get('location', {})
            lat = location.get('y', 0)
            lon = location.get('x', 0)
            
            if lat and lon and not is_within_singapore(lat, lon):
                continue
            
            log_message(f"📨 NEW & RECENT Waze accident found (ID: {accident_id})")
            
            # Format and send NEW accident
            formatted_msg = format_waze_accident_message(accident)
            sent_id = send_telegram_message(formatted_msg)
            
            if sent_id:
                # Mark as processed to prevent duplicates
                processed_accidents.add(accident_id)
                new_accidents += 1
                log_message(f"✅ Posted NEW & RECENT Waze accident (Telegram ID: {sent_id})")
            else:
                log_message("❌ Failed to post accident")
        
        if new_accidents > 0:
            # Save processed accidents to prevent duplicates
            save_processed_waze_accidents(processed_accidents)
            log_message(f"📊 Posted {new_accidents} NEW & RECENT Waze accidents")
        else:
            log_message("📊 No NEW & RECENT accidents to post (filtered: duplicates or old)")
                
    except Exception as e:
        log_message(f"Error processing Waze accidents: {e}")
    
    return new_accidents

def main():
    """Main monitoring function with duplicate prevention and real-time filtering - Only posts NEW & RECENT accidents"""
    log_message("🚨 Starting Waze Accident Monitor (Real-Time Mode)")
    log_message("✅ Will only post NEW & RECENT accidents - no duplicates or old reports!")
    log_message(f"⏰ Age filter: Only accidents < {MAX_ACCIDENT_AGE_MINUTES} minutes old")
    log_message("📍 Monitoring Singapore accidents only")
    log_message(f"🎯 Target channel: {CHAT_ID}")
    
    # Send startup notification
    startup_message = f"""🔄 **Waze Monitor Restarted** - {datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')}

**Method:** Waze API → Bot API → Channel
**VM:** sg-accident-monitor (us-central1-a)
**Target:** 🇸🇬Sg accidents  
**Source:** Waze Live Map API
**Mode:** ⚡ Real-Time - NEW & RECENT accidents only
**Age Filter:** < {MAX_ACCIDENT_AGE_MINUTES} minutes old
**Status:** ✅ Active and ready

*This version prevents duplicates AND filters out old accident reports for real-time alerts*"""
    
    send_telegram_message(startup_message)
    log_message("📢 Startup notification sent")
    
    check_count = 0
    total_posted = 0
    
    # Main monitoring loop
    while True:
        try:
            check_count += 1
            log_message(f"\n=== Monitoring Check #{check_count} ===")
            
            # Process NEW accidents only (duplicate prevention active)
            new_accidents = process_waze_accidents()
            total_posted += new_accidents
            
            log_message(f"📊 Total NEW & RECENT accidents posted this session: {total_posted}")
            log_message(f"⏰ Waiting {MONITOR_INTERVAL} seconds for next check...")
            
            time.sleep(MONITOR_INTERVAL)
            
        except KeyboardInterrupt:
            log_message("\n🛑 Monitor stopped by user")
            log_message(f"📈 Session summary: {total_posted} NEW & RECENT accidents posted in {check_count} checks")
            break
        except Exception as e:
            log_message(f"Monitoring error: {e}")
            time.sleep(60)  # Wait before retry

if __name__ == "__main__":
    main()