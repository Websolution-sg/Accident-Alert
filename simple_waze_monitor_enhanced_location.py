#!/usr/bin/env python3
"""
Enhanced Waze Accident Monitor for Singapore - Simple Format with Improved Location Detection

This version:
- Uses simple "Accident on [location]" format (not @sgaccident descriptive style)
- Enhanced location detection: uses nearest street name or area instead of "unknown location"
- Coordinate-based fallback to Singapore areas/expressways when street data is poor
- Real-time filtering (only posts NEW & RECENT accidents)
- Duplicate prevention with enhanced coordinate-based IDs
- Proper Singapore timezone handling
"""

import requests
import json
import datetime
from datetime import timezone
import time
import os

# Configuration
BOT_TOKEN = "7801461213:AAFWWu-CEklMHDRU-7Hu0P4nX8SyJIB1UGA"
CHAT_ID = "-1003683261194"

# Singapore bounds for filtering
SINGAPORE_BOUNDS = {
    "north": 1.47,
    "south": 1.16, 
    "east": 104.0,
    "west": 103.5
}

# Waze API configuration
WAZE_API_URL = "https://www.waze.com/row-partnerhub-api/partners/11167547-8b2f-4a5d-8b34-99cc1b644de9/view"
WAZE_BBOX = {
    "bottom": SINGAPORE_BOUNDS["south"],
    "left": SINGAPORE_BOUNDS["west"], 
    "right": SINGAPORE_BOUNDS["east"],
    "top": SINGAPORE_BOUNDS["north"]
}

# Singapore timezone
SGT = timezone(datetime.timedelta(hours=8))

# File to store processed accident IDs
PROCESSED_WAZE_FILE = "processed_waze_accidents.json"

# Maximum age of accidents to post (in minutes) - only recent ones
MAX_ACCIDENT_AGE_MINUTES = 15

def log_message(message):
    """Log a message with timestamp"""
    timestamp = datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')
    print(f"[{timestamp}] WAZE: {message}")

def load_processed_waze_accidents():
    """Load processed Waze accident IDs"""
    try:
        if os.path.exists(PROCESSED_WAZE_FILE):
            with open(PROCESSED_WAZE_FILE, 'r') as f:
                data = json.load(f)
                log_message(f"📂 Loaded {len(data)} processed messages")
                return set(data)
    except Exception as e:
        log_message(f"Error loading processed messages: {e}")
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

def format_waze_accident_message(accident):
    """Format Waze accident using simple format with enhanced location detection"""
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
    
    # Format location - ENHANCED VERSION with coordinate-based fallback
    # Check if we have a meaningful street name
    meaningful_street = (street and 
                        street.lower() not in ['unknown location', 'unknown', ''] and 
                        len(street.strip()) > 2)
    
    if meaningful_street and city and city != 'Singapore':
        location_text = f"{street}, {city}"
    elif meaningful_street:
        location_text = street
    elif city and city != 'Singapore':
        location_text = city
    elif lat and lon:
        # Try to get better location from coordinates
        # First check if it's on an expressway
        expressway = get_singapore_expressway_from_coords(lat, lon)
        if expressway:
            location_text = expressway.split('(')[0].strip()  # Just get the name part
        else:
            # Get area/neighborhood from coordinates 
            area = get_singapore_location_from_coords(lat, lon)
            if area:
                location_text = area
            else:
                location_text = f"coordinates {lat:.4f}, {lon:.4f}"
    else:
        location_text = "Unknown location"
    
    # Build message using simple format
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
        
        if response.status_code == 200:
            data = response.json()
            if 'alerts' in data:
                # Filter for accidents only
                accidents = [alert for alert in data['alerts'] 
                           if alert.get('type') == 'ACCIDENT' and alert.get('subtype') == 'ACCIDENT_MINOR']
                return accidents
            log_message("⚠️ No 'alerts' key in response")
            return []
        else:
            log_message(f"❌ API request failed: {response.status_code}")
            return []
            
    except Exception as e:
        log_message(f"❌ Error fetching Waze data: {e}")
        return []

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
    
    waze_accidents = get_waze_alerts()
    log_message(f"Found {len(waze_accidents)} Waze accidents")
    
    for accident in waze_accidents:
        # Get coordinates and check if within Singapore
        location = accident.get('location', {})
        lat = location.get('y')
        lon = location.get('x')
        
        if not is_within_singapore(lat, lon):
            continue
            
        # Generate unique ID for duplicate checking
        accident_id = get_waze_accident_id(accident)
        
        # Skip if we've already processed this accident
        if accident_id in processed_accidents:
            continue
            
        # Check if accident is recent (REAL-TIME FILTERING)
        if not is_accident_recent(accident):
            continue
            
        # This is a NEW & RECENT accident!
        try:
            formatted_msg = format_waze_accident_message(accident)
            message_id = send_telegram_message(formatted_msg)
            
            if message_id:
                log_message(f"✅ Posted NEW & RECENT Waze accident (ID: {accident_id})")
                processed_accidents.add(accident_id)
                new_accidents += 1
            else:
                log_message(f"❌ Failed to post accident")
                
        except Exception as e:
            log_message(f"❌ Error processing accident: {e}")
    
    # Clean up old processed IDs (keep only last 24 hours)
    current_time = datetime.datetime.now()
    cutoff_time = current_time - datetime.timedelta(hours=24)
    cutoff_str = cutoff_time.strftime('%Y%m%d')
    
    processed_accidents = {pid for pid in processed_accidents 
                          if not any(cutoff_str > pid.split('_')[2] for _ in [None] if '_' in pid and len(pid.split('_')) >= 3)}
    
    # Save the updated processed accidents
    save_processed_waze_accidents(processed_accidents)
    
    if new_accidents > 0:
        log_message(f"🎯 Posted {new_accidents} NEW & RECENT accidents")
    else:
        log_message("🔄 No NEW & RECENT accidents to post (filtered: duplicates or old)")
    
    log_message(f"🎯 Total NEW & RECENT accidents posted this session: {new_accidents}")

def main():
    """Main monitoring loop"""
    log_message("🚨 Starting Waze Accident Monitor (Real-Time Mode)")
    log_message("⚡ Will only post NEW & RECENT accidents - no duplicates or old reports!")
    log_message(f"⏰ Age filter: Only accidents < {MAX_ACCIDENT_AGE_MINUTES} minutes old")
    log_message("🏢 Monitoring Singapore accidents only")
    log_message(f"📺 Target channel: {CHAT_ID}")
    
    # Send startup notification
    startup_msg = "🚨 **Enhanced Waze Monitor Started (Simple Format)**\n"
    startup_msg += "⚡ **Real-time mode**: Only NEW & RECENT accidents\n"
    startup_msg += f"⏰ **Age filter**: < {MAX_ACCIDENT_AGE_MINUTES} minutes old\n"
    startup_msg += "🎯 **Enhanced location detection**: Uses nearest streets/areas instead of 'unknown location'\n"
    startup_msg += f"🌏 **Region**: Singapore only\n"
    startup_msg += f"🕐 **Started**: {datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')}"
    
    send_telegram_message(startup_msg)
    log_message("📬 Startup notification sent")
    
    check_count = 0
    
    try:
        while True:
            check_count += 1
            log_message(f"\n=== Monitoring Check #{check_count} ===")
            
            process_waze_accidents()
            
            log_message("⏰ Waiting 60 seconds for next check...")
            time.sleep(60)
            
    except KeyboardInterrupt:
        log_message("\n🛑 Monitor stopped by user")
    except Exception as e:
        log_message(f"❌ Monitor crashed: {e}")
        raise

if __name__ == "__main__":
    main()