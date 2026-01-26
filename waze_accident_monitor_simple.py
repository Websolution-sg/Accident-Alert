#!/usr/bin/env python3
"""
Simple Accident Monitor - @sgaccident Channel Only
Monitors only the @sgaccident Telegram channel and forwards alerts
"""
import requests
import json
import time
import datetime
import random
import math

# Configuration
TELEGRAM_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
CHAT_ID = "-1003683261194"  # Target channel
SGACCIDENT_CHAT_ID = "-1001486947378"  # @sgaccident channel
PROCESSED_FILE = "processed_accidents.json"

def log_message(message):
    """Print timestamped log message"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def coordinates_similar(lat1, lon1, lat2, lon2, radius_meters=100):
    """Check if two coordinates are within specified radius using Haversine formula"""
    if not all([lat1, lon1, lat2, lon2]):
        return False
    
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = 6371000 * c  # Earth's radius in meters
    
    return distance <= radius_meters

def send_telegram_message(message):
    """Send message to Telegram channel"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': CHAT_ID,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return True
        else:
            log_message(f"Failed to send message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        log_message(f"Error sending Telegram message: {e}")
        return False

def load_processed_accidents():
    """Load processed accident IDs"""
    try:
        with open(PROCESSED_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('waze_accidents', [])), set(data.get('telegram_accidents', []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set(), set()

def save_processed_accidents(waze_processed, telegram_processed):
    """Save processed accident IDs"""
    data = {
        'waze_accidents': list(waze_processed),
        'telegram_accidents': list(telegram_processed)
    }
    try:
        with open(PROCESSED_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log_message(f"Error saving processed accidents: {e}")

def get_telegram_updates():
    """Get updates from Telegram, including channel posts"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {'limit': 100, 'timeout': 10}
        
        response = requests.get(url, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                return data.get('result', [])
            else:
                log_message(f"Telegram API error: {data.get('description', 'Unknown error')}")
        else:
            log_message(f"Failed to get updates: {response.status_code}")
    except Exception as e:
        log_message(f"Error getting Telegram updates: {e}")
    
    return []

def extract_coordinates_from_text(text):
    """Extract coordinates from message text"""
    if not text:
        return None, None
    
    import re
    
    # Look for coordinate patterns
    patterns = [
        r'(\d+\.\d+),\s*(\d+\.\d+)',  # Basic decimal coordinates
        r'maps\.google\.com[^\s]*[@,](-?\d+\.\d+),(-?\d+\.\d+)',  # Google Maps
        r'waze\.com[^\s]*ll=(-?\d+\.\d+),(-?\d+\.\d+)'  # Waze links
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                lat, lon = float(match.group(1)), float(match.group(2))
                # Validate Singapore coordinates
                if 1.0 <= lat <= 1.5 and 103.6 <= lon <= 104.1:
                    return lat, lon
            except (ValueError, IndexError):
                continue
    
    return None, None

def format_accident_message(original_text, lat=None, lon=None):
    """Format accident message for posting"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    message = f"🚨 <b>ACCIDENT ALERT</b> (@sgaccident)\n\n"
    message += f"📍 <b>Details:</b>\n{original_text}\n\n"
    message += f"⏰ <b>Reported:</b> {timestamp}\n\n"
    
    if lat and lon:
        google_maps_link = f"https://www.google.com/maps?q={lat},{lon}"
        waze_link = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
        message += f"🗺️ <a href='{google_maps_link}'>View on Google Maps</a>\n"
        message += f"🚗 <a href='{waze_link}'>Open in Waze</a>\n\n"
    
    message += f"🔗 <b>Source:</b> @sgaccident"
    
    return message

def process_sgaccident_updates():
    """Process new messages from @sgaccident channel"""
    log_message("Checking @sgaccident channel for new posts...")
    
    updates = get_telegram_updates()
    waze_processed, telegram_processed = load_processed_accidents()
    
    new_posts = 0
    posted_coords = []
    
    for update in updates:
        if 'channel_post' not in update:
            continue
        
        post = update['channel_post']
        chat = post.get('chat', {})
        
        # Check if it's from @sgaccident channel
        if str(chat.get('id')) != SGACCIDENT_CHAT_ID:
            continue
        
        message_id = str(post.get('message_id', ''))
        message_text = post.get('text', '')
        
        if not message_text or message_id in telegram_processed:
            continue
        
        # Extract coordinates for duplicate detection
        lat, lon = extract_coordinates_from_text(message_text)
        
        # Check for coordinate duplicates
        is_duplicate = False
        if lat and lon:
            for prev_lat, prev_lon in posted_coords:
                if coordinates_similar(lat, lon, prev_lat, prev_lon, 100):  # 100m radius
                    is_duplicate = True
                    log_message(f"Skipping duplicate coordinates: {lat:.4f}, {lon:.4f}")
                    break
        
        if is_duplicate:
            telegram_processed.add(message_id)
            continue
        
        # Format and send message
        formatted_message = format_accident_message(message_text, lat, lon)
        
        if send_telegram_message(formatted_message):
            log_message(f"✓ Posted @sgaccident update: {message_text[:50]}...")
            telegram_processed.add(message_id)
            new_posts += 1
            
            if lat and lon:
                posted_coords.append((lat, lon))
            
            time.sleep(2)  # Avoid rapid posting
        else:
            log_message("✗ Failed to post @sgaccident update")
    
    save_processed_accidents(waze_processed, telegram_processed)
    
    if new_posts > 0:
        log_message(f"Posted {new_posts} new @sgaccident updates")
    
    return new_posts

def main():
    """Main monitoring loop - @sgaccident channel only"""
    log_message("Starting accident monitoring with @sgaccident ONLY...")
    log_message("Data source: @sgaccident channel ONLY")
    log_message(f"Target channel: {CHAT_ID}")
    log_message(f"Monitoring: https://web.telegram.org/a/#-1001486947378")
    
    while True:
        try:
            # Process @sgaccident channel ONLY
            process_sgaccident_updates()
            
            # Simple cleanup - keep last 500 processed IDs
            waze_processed, telegram_processed = load_processed_accidents()
            if len(telegram_processed) > 500:
                telegram_processed = set(list(telegram_processed)[-250:])
            save_processed_accidents(waze_processed, telegram_processed)
            
            # 1 minute monitoring cycle for @sgaccident priority
            sleep_time = 60
            log_message(f"Monitoring cycle complete, sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            log_message("Monitoring stopped by user")
            break
        except Exception as e:
            log_message(f"Error in monitoring loop: {e}")
            error_sleep = random.randint(120, 180)
            log_message(f"Error recovery, waiting {error_sleep} seconds...")
            time.sleep(error_sleep)

if __name__ == "__main__":
    main()