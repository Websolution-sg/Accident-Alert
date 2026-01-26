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

# Ensure unbuffered output for systemd logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHAT_ID = "-1003683261194"
SGACCIDENT_CHAT_ID = "-1001486947378"
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

def send_telegram_message(message):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
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

def format_accident_message(original_text, coordinates=None):
    """Format accident message for forwarding"""
    message = "🚨 <b>ACCIDENT ALERT</b> 🚨\n\n"
    
    # Extract location info from text
    lines = original_text.strip().split('\n')
    clean_text = original_text
    
    # Add the original message content
    message += f"📄 <b>Details:</b> {clean_text}\n"
    
    # Add coordinates if available
    if coordinates and len(coordinates) == 2:
        lat, lon = coordinates
        message += f"🗺️ <b>Coordinates:</b> {lat}, {lon}\n"
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        message += f"🔗 <b>View on Maps:</b> <a href='{maps_url}'>Open Location</a>\n"
    
    message += f"⏰ <b>Time:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    message += f"🔗 <b>Source:</b> @sgaccident Channel"
    
    return message

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
                        formatted_message = format_accident_message(text, (lat, lon) if lat and lon else None)
                        
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

def main():
    """Main monitoring loop - @sgaccident channel ONLY"""
    log_message("Starting accident monitoring with @sgaccident channel ONLY...")
    log_message("Data source: @sgaccident channel ONLY")
    log_message(f"Target channel: {CHAT_ID}")
    
    while True:
        try:
            # Process @sgaccident channel ONLY
            process_sgaccident_updates()
            
            # Simple cleanup - keep last 500 processed IDs for each source
            waze_processed, telegram_processed = load_processed_accidents()
            if len(waze_processed) > 1000:
                waze_list = list(waze_processed)
                waze_processed = set(waze_list[-500:])
            if len(telegram_processed) > 1000:
                telegram_list = list(telegram_processed) 
                telegram_processed = set(telegram_list[-500:])
            save_processed_accidents(waze_processed, telegram_processed)
            
            # 1 minute monitoring cycle for @sgaccident priority
            sleep_time = 60
            log_message(f"Monitoring cycle complete, sleeping for {sleep_time} seconds...")
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