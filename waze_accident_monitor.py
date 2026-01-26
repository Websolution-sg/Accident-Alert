#!/usr/bin/env python3
import requests
import json
import time
import datetime
import os
import re
import sys
import random
import math
from typing import List, Dict

# Ensure unbuffered output for systemd logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHAT_ID = "-1003683261194"
SGACCIDENT_CHAT_ID = "-1001486947378"

# Waze API Configuration
WAZE_API_URL = "https://www.waze.com/live-map/api/georss"
WAZE_BBOX = {
    'bottom': 1.1304753,
    'left': 103.6055424,
    'right': 104.0945619,
    'top': 1.4764671
}
SINGAPORE_BOUNDS = {
    "north": 1.4784,
    "south": 1.1496,
    "east": 104.0853,
    "west": 103.6065
}

# Data storage files
PROCESSED_FILE = "processed_accidents.json"
TELEGRAM_OFFSET_FILE = "telegram_offset.json"

def log_message(message):
    """Log messages with timestamp and immediate flush"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)

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

def contains_malaysia_keywords(text):
    """Check if text contains Malaysia-related keywords"""
    if not text:
        return False
    text_lower = text.lower()
    malaysia_keywords = ['malaysia', 'johor', 'kl', 'kuala lumpur', 'selangor', 'penang', 'perak', 'kedah', 'terengganu', 'kelantan', 'pahang', 'negeri sembilan', 'melaka', 'sabah', 'sarawak']
    return any(keyword in text_lower for keyword in malaysia_keywords)

def load_processed_accidents():
    """Load the list of processed accident IDs"""
    try:
        if os.path.exists(PROCESSED_FILE):
            with open(PROCESSED_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get('waze_accidents', [])), set(data.get('telegram_accidents', []))
    except Exception as e:
        log_message(f"Error loading processed accidents: {e}")
    return set(), set()

def save_processed_accidents(waze_accidents, telegram_accidents):
    """Save the list of processed accident IDs"""
    try:
        data = {
            'waze_accidents': list(waze_accidents),
            'telegram_accidents': list(telegram_accidents)
        }
        with open(PROCESSED_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        log_message(f"Error saving processed accidents: {e}")

def load_telegram_offset():
    """Load the last processed telegram update ID"""
    try:
        if os.path.exists(TELEGRAM_OFFSET_FILE):
            with open(TELEGRAM_OFFSET_FILE, 'r') as f:
                return json.load(f).get('offset', 0)
    except Exception as e:
        log_message(f"Error loading telegram offset: {e}")
    return 0

def save_telegram_offset(offset):
    """Save the telegram update offset"""
    try:
        with open(TELEGRAM_OFFSET_FILE, 'w') as f:
            json.dump({'offset': offset}, f)
    except Exception as e:
        log_message(f"Error saving telegram offset: {e}")

def coordinates_similar(lat1, lon1, lat2, lon2, radius_meters=100):
    """Check if two coordinates are within specified radius (default 100m)"""
    if not all([lat1, lon1, lat2, lon2]):
        return False
    
    # Convert to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = 6371000 * c  # Earth's radius in meters
    
    return distance <= radius_meters

def get_waze_alerts() -> List[Dict]:
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
        
        response = requests.get(WAZE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('alerts', [])
    except Exception as e:
        log_message(f"Error fetching Waze data: {e}")
        return []

def filter_waze_accidents(alerts: List[Dict]) -> List[Dict]:
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

def get_waze_accident_id(accident: Dict) -> str:
    """Generate unique ID for Waze accident"""
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

def format_waze_accident_message(accident: Dict) -> str:
    """Format Waze accident information for Telegram using consistent format"""
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
        utc_time = datetime.datetime.fromtimestamp(pub_millis / 1000)
        report_time = utc_time.strftime('%Y-%m-%d %H:%M:%S SGT')
    else:
        report_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S SGT')
    
    # Format location
    if street and city and city != 'Singapore':
        location_text = f"{street}, {city}"
    elif street:
        location_text = street
    elif city:
        location_text = city
    else:
        location_text = "Unknown location"
    
    # Build message using consistent format
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
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            log_message(f"Message sent successfully")
            return True
        else:
            log_message(f"Failed to send message: {response.text}")
            return False
    except Exception as e:
        log_message(f"Error sending message: {e}")
        return False

def extract_coordinates_from_text(text):
    """Extract coordinates from text using various patterns"""
    if not text:
        return None, None
    
    # Pattern 1: Standard decimal degrees (1.234567, 103.789012)
    pattern1 = r'(\d+\.\d+),\s*(\d+\.\d+)'
    match1 = re.search(pattern1, text)
    if match1:
        lat, lon = float(match1.group(1)), float(match1.group(2))
        if is_within_singapore(lat, lon):
            return lat, lon
    
    # Pattern 2: Coordinates with direction indicators or in parentheses
    pattern2 = r'\(?(\d+\.\d+)\s*[,\s]\s*(\d+\.\d+)\)?'
    matches2 = re.finditer(pattern2, text)
    for match in matches2:
        lat, lon = float(match.group(1)), float(match.group(2))
        if is_within_singapore(lat, lon):
            return lat, lon
    
    return None, None

def is_accident_related(text):
    """Check if text is related to accidents"""
    if not text:
        return False
    
    text_lower = text.lower()
    accident_keywords = [
        'accident', 'crash', 'collision', 'hit', 'injured', 'ambulance', 
        'police', 'traffic police', 'scdf', 'emergency', 'road block',
        'breakdown', 'stalled', 'blocked', 'lane closed', 'diversions'
    ]
    
    return any(keyword in text_lower for keyword in accident_keywords)

def format_accident_message(original_text, coordinates=None, source="@sgaccident"):
    """Format accident message for forwarding using consistent format"""
    # Extract location from text
    lines = original_text.strip().split('\n')
    location_text = "Unknown location"
    
    # Look for location patterns in the text
    for line in lines:
        line = line.strip()
        if any(keyword in line.lower() for keyword in ['road', 'rd', 'street', 'st', 'avenue', 'ave', 'expressway', 'highway', 'pie', 'cte', 'aye', 'bke', 'sle', 'tpe']):
            location_text = line
            break
        elif len(line) > 10 and not line.startswith('🚨') and not line.startswith('Traffic'):
            location_text = line
            break
    
    # If still no good location, use first meaningful line
    if location_text == "Unknown location" and lines:
        for line in lines:
            line = line.strip()
            if len(line) > 5 and not line.startswith('🚨'):
                location_text = line[:100]  # Limit length
                break
    
    # Format timestamp with SGT
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S SGT')
    
    # Determine reporter based on source
    if source.lower() == "waze":
        reporter = "Waze user"
    else:
        reporter = source
    
    # Build the message using consistent format
    message = f"Accident on {location_text}\n"
    message += f"🕐 Reported: {timestamp}\n"
    message += f"👤 Reported by: {reporter}\n"
    message += f"📈 Confidence: N/A\n"
    message += f"✅ Reliability: N/A\n\n"
    
    # Add coordinates if available
    if coordinates and len(coordinates) == 2:
        lat, lon = coordinates
        google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        waze_url = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
        message += f"🗺️ [View on Google Maps ({lat}, {lon})]({google_maps_url})\n"
        message += f"🚗 [Open in Waze ({lat}, {lon})]({waze_url})"
    else:
        message += f"🗺️ Location coordinates not available"
    
    return message

def process_waze_accidents():
    """Process Waze accidents and post new ones"""
    log_message("Checking Waze for new accidents...")
    
    waze_processed, telegram_processed = load_processed_accidents()
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
        
        for accident in accidents:
            # Generate unique ID
            accident_id = get_waze_accident_id(accident)
            
            # Check if already processed
            if accident_id in waze_processed:
                continue
            
            # Check coordinates are in Singapore
            location = accident.get('location', {})
            lat = location.get('y', 0)
            lon = location.get('x', 0)
            
            if lat and lon and not is_within_singapore(lat, lon):
                log_message(f"Skipping accident outside Singapore: {lat}, {lon}")
                continue
            
            # Check for duplicates with existing accidents
            is_duplicate = False
            if lat and lon:
                for existing_id in list(waze_processed) + list(telegram_processed):
                    # Extract coordinates from existing IDs to check for duplicates
                    if "coord_" in existing_id:
                        try:
                            parts = existing_id.split("_")
                            if len(parts) >= 4:
                                existing_lat = float(parts[2])
                                existing_lon = float(parts[3])
                                if coordinates_similar(lat, lon, existing_lat, existing_lon):
                                    is_duplicate = True
                                    log_message(f"Waze accident is duplicate of existing: {existing_id}")
                                    break
                        except (ValueError, IndexError):
                            continue
            
            if is_duplicate:
                # Mark as processed even if duplicate to avoid repeated checks
                waze_processed.add(accident_id)
                continue
            
            # Format and send message
            message = format_waze_accident_message(accident)
            if send_telegram_message(message):
                waze_processed.add(accident_id)
                new_accidents += 1
                log_message(f"Posted new Waze accident: {accident_id}")
            else:
                log_message(f"Failed to post Waze accident: {accident_id}")
        
        # Save processed accidents
        save_processed_accidents(waze_processed, telegram_processed)
        
    except Exception as e:
        log_message(f"Error processing Waze accidents: {e}")
    
    return new_accidents

def process_sgaccident_updates():
    """Process messages from @sgaccident channel"""
    log_message("Checking @sgaccident channel for new accidents...")
    
    waze_processed, telegram_processed = load_processed_accidents()
    offset = load_telegram_offset()
    new_accidents = 0
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {
            'offset': offset + 1,
            'limit': 100,
            'timeout': 10
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            log_message(f"Failed to get updates: {response.status_code}")
            return
        
        data = response.json()
        if not data.get('ok'):
            log_message(f"API error: {data.get('description', 'Unknown error')}")
            return
        
        updates = data.get('result', [])
        
        if not updates:
            log_message("No new updates from @sgaccident")
            return
        
        log_message(f"Processing {len(updates)} updates...")
        
        for update in updates:
            update_id = update.get('update_id')
            
            # Update offset
            if update_id > offset:
                offset = update_id
            
            # Check for channel posts
            if 'channel_post' in update:
                post = update['channel_post']
                chat_id = str(post.get('chat', {}).get('id', ''))
                
                # Only process @sgaccident channel
                if chat_id == SGACCIDENT_CHAT_ID:
                    message_id = post.get('message_id')
                    text = post.get('text', '') or post.get('caption', '')
                    
                    if text and is_accident_related(text):
                        # Create unique accident ID
                        accident_id = f"sgaccident_{chat_id}_{message_id}"
                        
                        if accident_id in telegram_processed:
                            continue
                        
                        # Extract coordinates
                        lat, lon = extract_coordinates_from_text(text)
                        
                        # Check for duplicate coordinates
                        is_duplicate = False
                        if lat and lon:
                            for processed_id in telegram_processed:
                                if '|' in processed_id:
                                    parts = processed_id.split('|')
                                    if len(parts) >= 2:
                                        coord_part = parts[1]
                                        if ',' in coord_part:
                                            try:
                                                existing_lat, existing_lon = map(float, coord_part.split(','))
                                                if coordinates_similar(lat, lon, existing_lat, existing_lon):
                                                    is_duplicate = True
                                                    log_message(f"Skipping duplicate location: {lat}, {lon}")
                                                    break
                                            except ValueError:
                                                pass
                        
                        if is_duplicate:
                            continue
                        
                        # Skip Malaysia-related accidents
                        if contains_malaysia_keywords(text):
                            log_message("Skipping Malaysia-related accident")
                            continue
                        
                        # Format and send message
                        formatted_message = format_accident_message(text, (lat, lon) if lat and lon else None, "@sgaccident")
                        
                        if send_telegram_message(formatted_message):
                            telegram_processed.add(accident_id)
                            new_accidents += 1
                            
                            # Store with coordinates for duplicate checking
                            if lat and lon:
                                coord_id = f"{accident_id}|{lat},{lon}|{datetime.datetime.now().isoformat()}"
                                telegram_processed.add(coord_id)
                            
                            log_message(f"New @sgaccident accident reported: {text[:100]}...")
                        else:
                            log_message(f"Failed to send @sgaccident message")
        
        # Save progress
        save_telegram_offset(offset)
        save_processed_accidents(waze_processed, telegram_processed)
        
        if new_accidents > 0:
            log_message(f"✅ Processed {new_accidents} new @sgaccident accidents")
        else:
            log_message("No new @sgaccident accidents to report")
            
    except Exception as e:
        log_message(f"Error processing @sgaccident updates: {e}")
        return 0
    
    return new_accidents

def main():
    """Main monitoring loop for both Waze and @sgaccident"""
    log_message("Starting Dual Accident Monitor (Waze + @sgaccident)...")
    log_message("Data sources: Waze API + @sgaccident channel")
    log_message(f"Target channel: {CHAT_ID}")
    
    cycle_count = 0
    
    while True:
        try:
            total_new = 0
            
            # Check Waze every 2 cycles (120 seconds)
            if cycle_count % 2 == 0:
                waze_count = process_waze_accidents()
                waze_count = waze_count or 0  # Handle None return
                total_new += waze_count
                if waze_count > 0:
                    log_message(f"✅ Processed {waze_count} new accidents from Waze")
            
            # Check @sgaccident every cycle (60 seconds)
            telegram_count = process_sgaccident_updates()
            telegram_count = telegram_count or 0  # Handle None return
            total_new += telegram_count
            
            if total_new == 0:
                log_message("No new accidents found from any source")
            
            # Simple cleanup - keep last 500 processed IDs for each source
            waze_processed, telegram_processed = load_processed_accidents()
            if len(waze_processed) > 1000:
                waze_list = list(waze_processed)
                waze_processed = set(waze_list[-500:])
            if len(telegram_processed) > 1000:
                telegram_list = list(telegram_processed) 
                telegram_processed = set(telegram_list[-500:])
            save_processed_accidents(waze_processed, telegram_processed)
            
            cycle_count += 1
            
            # 60 second monitoring cycle
            sleep_time = 60
            log_message(f"Monitoring cycle {cycle_count} complete, sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            log_message("Monitoring stopped by user")
            break
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            # Random sleep on error to avoid rapid retries
            error_sleep = random.randint(120, 180)
            log_message(f"Waiting {error_sleep} seconds after error...")
            time.sleep(error_sleep)

if __name__ == "__main__":
    main()