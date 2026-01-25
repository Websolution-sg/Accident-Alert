#!/usr/bin/env python3
import requests
import json
import time
import datetime
import os
import re
from urllib.parse import quote

# Configuration
BOT_TOKEN = "8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U"
CHAT_ID = "-1003683261194"
SGACCIDENT_CHAT_ID = "-1001486947378"
WAZE_API_URL = "https://www.waze.com/live-map/api/georss"
SINGAPORE_BOUNDS = {
    "north": 1.4784,
    "south": 1.1496,
    "east": 104.0853,
    "west": 103.6065
}

# File to store processed accident IDs and duplicate tracking
PROCESSED_FILE = "processed_accidents.json"
TELEGRAM_OFFSET_FILE = "telegram_offset.json"

def log_message(message):
    """Log messages with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_processed_accidents():
    """Load the list of processed accident IDs"""
    try:
        if os.path.exists(PROCESSED_FILE):
            with open(PROCESSED_FILE, 'r') as f:
                data = json.load(f)
                return data.get('waze_accidents', set()), data.get('telegram_accidents', set())
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

def normalize_address(address):
    """Normalize address for duplicate detection"""
    if not address:
        return ""
    
    # Convert to lowercase
    address = address.lower()
    
    # Remove common words and standardize
    replacements = {
        r'\brd\b': 'road',
        r'\bst\b': 'street',
        r'\bave\b': 'avenue',
        r'\bdr\b': 'drive',
        r'\bblvd\b': 'boulevard',
        r'\bhwy\b': 'highway',
        r'\bpkwy\b': 'parkway',
        r'\bln\b': 'lane',
        r'\bpl\b': 'place',
        r'\bct\b': 'court',
        r'\bcir\b': 'circle',
        r'\bsq\b': 'square'
    }
    
    for pattern, replacement in replacements.items():
        address = re.sub(pattern, replacement, address)
    
    # Remove special characters and extra spaces
    address = re.sub(r'[^\w\s]', ' ', address)
    address = re.sub(r'\s+', ' ', address)
    
    return address.strip()

def addresses_similar(addr1, addr2, threshold=0.7):
    """Check if two addresses are similar enough to be considered duplicates"""
    if not addr1 or not addr2:
        return False
    
    norm1 = normalize_address(addr1)
    norm2 = normalize_address(addr2)
    
    if norm1 == norm2:
        return True
    
    # Simple similarity check
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if len(words1) == 0 and len(words2) == 0:
        return True
    if len(words1) == 0 or len(words2) == 0:
        return False
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    similarity = intersection / union if union > 0 else 0
    return similarity >= threshold

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

def get_waze_accidents():
    """Fetch accidents from Waze API"""
    try:
        params = {
            "top": SINGAPORE_BOUNDS["north"],
            "bottom": SINGAPORE_BOUNDS["south"],
            "left": SINGAPORE_BOUNDS["west"],
            "right": SINGAPORE_BOUNDS["east"],
            "env": "row",
            "types": "alerts"
        }
        
        response = requests.get(WAZE_API_URL, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            log_message(f"Failed to fetch Waze data: {response.status_code}")
            return None
    except Exception as e:
        log_message(f"Error fetching Waze accidents: {e}")
        return None

def get_telegram_updates(offset=0):
    """Get updates from Telegram bot API"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {
            "offset": offset,
            "limit": 100,
            "timeout": 30
        }
        response = requests.get(url, params=params, timeout=35)
        if response.status_code == 200:
            return response.json()
        else:
            log_message(f"Failed to get telegram updates: {response.text}")
            return None
    except Exception as e:
        log_message(f"Error getting telegram updates: {e}")
        return None

def extract_location_from_message(text):
    """Extract location information from @sgaccident message preserving original format"""
    if not text:
        return None
    
    # Split into lines and find the most likely location line
    lines = text.split('\n')
    
    # Look for lines that typically contain location in @sgaccident format
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip common non-location lines
        skip_patterns = [
            r'^(update|breaking|alert|attention)',
            r'^(time|date|reported)',
            r'^(source|via|from)',
            r'^\d{1,2}[:/]\d{1,2}',  # time stamps
            r'^@\w+',  # channel mentions
        ]
        
        should_skip = False
        for pattern in skip_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                should_skip = True
                break
                
        if should_skip:
            continue
            
        # Look for location indicators
        location_indicators = [
            'accident', 'crash', 'collision', 'jam', 'traffic',
            'road', 'street', 'avenue', 'drive', 'boulevard', 'highway',
            'expressway', 'at', 'along', 'near', 'towards'
        ]
        
        # Check if line contains location indicators
        has_location_indicator = any(indicator in line.lower() for indicator in location_indicators)
        
        # If line has good length and location indicators, use it
        if 10 <= len(line) <= 150 and has_location_indicator:
            return line
    
    # Fallback: look for location patterns in the full text
    location_patterns = [
        r'(?:accident|crash|collision)\s+(?:at|along|near)\s+([^\.!?\n]{10,100})',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Road|Street|Avenue|Drive|Boulevard|Highway|Expressway|Way|Lane|Place|Court|Circle))',
        r'(?:at|along|near)\s+([^\.!?\n]{10,100})',
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            location = matches[0].strip()
            if len(location) > 5:  # Filter out very short matches
                return location
    
    # Last resort: use first meaningful line
    for line in lines:
        line = line.strip()
        if 10 <= len(line) <= 100:
            return line
    
    return None

def format_sgaccident_message(original_text, location, timestamp):
    """Format @sgaccident message using original location header format"""
    # Use the original text format but add our enhancements
    # Keep the original location format from @sgaccident channel
    waze_message = f"🚨 <b>Accident Alert</b>\n\n"
    
    # Use original location format from @sgaccident channel if available
    if location and location in original_text:
        # Find the location context in original text to preserve formatting
        lines = original_text.split('\n')
        location_line = None
        for line in lines:
            if location.lower() in line.lower():
                location_line = line.strip()
                break
        
        if location_line:
            waze_message += f"{location_line}\n"
        else:
            waze_message += f"{location}\n"
    else:
        waze_message += f"{location}\n"
    
    waze_message += f"\n⏰ <b>Reported:</b> {timestamp}\n"
    waze_message += f"📱 <b>Source:</b> @sgaccident\n\n"
    waze_message += f"ℹ️ <i>Please drive safely and consider alternative routes</i>"
    
    return waze_message

def process_waze_accidents():
    """Process new accidents from Waze"""
    log_message("Checking Waze API for new accidents...")
    
    waze_processed, telegram_processed = load_processed_accidents()
    
    waze_data = get_waze_accidents()
    if not waze_data:
        return
    
    alerts = waze_data.get("alerts", [])
    new_accidents = 0
    
    for alert in alerts:
        if alert.get("type") == "ACCIDENT":
            accident_id = alert.get("uuid")
            if not accident_id or accident_id in waze_processed:
                continue
            
            location = alert.get("location", {})
            street = alert.get("street", "Unknown location")
            city = alert.get("city", "Singapore")
            country = alert.get("country", "SG")
            
            # Check for cross-source duplicates with telegram accidents
            is_duplicate = False
            for telegram_id in telegram_processed:
                if addresses_similar(street, telegram_id):
                    log_message(f"Skipping Waze accident - duplicate with Telegram: {street}")
                    is_duplicate = True
                    break
            
            if is_duplicate:
                waze_processed.add(accident_id)
                continue
            
            # Format the message
            message = f"🚨 <b>Accident Alert</b>\n\n"
            message += f"📍 <b>Location:</b> {street}, {city}\n"
            message += f"🗺️ <b>Coordinates:</b> {location.get('y', 'N/A')}, {location.get('x', 'N/A')}\n"
            message += f"⏰ <b>Reported:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"📱 <b>Source:</b> Waze\n\n"
            message += f"ℹ️ <i>Please drive safely and consider alternative routes</i>"
            
            if send_telegram_message(message):
                waze_processed.add(accident_id)
                new_accidents += 1
                log_message(f"New Waze accident reported: {street}")
                time.sleep(1)  # Rate limiting
    
    save_processed_accidents(waze_processed, telegram_processed)
    if new_accidents > 0:
        log_message(f"Processed {new_accidents} new Waze accidents")

def process_sgaccident_updates():
    """Process updates from @sgaccident channel"""
    log_message("Checking @sgaccident channel for new posts...")
    
    waze_processed, telegram_processed = load_processed_accidents()
    current_offset = load_telegram_offset()
    
    updates = get_telegram_updates(current_offset)
    if not updates or not updates.get('ok'):
        return
    
    new_accidents = 0
    latest_offset = current_offset
    
    for update in updates.get('result', []):
        update_id = update.get('update_id')
        latest_offset = max(latest_offset, update_id + 1)
        
        # Check if it's a channel post from @sgaccident
        channel_post = update.get('channel_post')
        if not channel_post:
            continue
        
        chat = channel_post.get('chat', {})
        if str(chat.get('id')) != SGACCIDENT_CHAT_ID:
            continue
        
        text = channel_post.get('text', '')
        if not text:
            continue
        
        # Check for accident-related keywords
        accident_keywords = ['accident', 'crash', 'collision', 'jam', 'traffic']
        if not any(keyword in text.lower() for keyword in accident_keywords):
            continue
        
        # Create a unique ID for this telegram message
        message_id = f"telegram_{chat.get('id')}_{channel_post.get('message_id')}"
        if message_id in telegram_processed:
            continue
        
        # Extract location
        location = extract_location_from_message(text)
        if not location:
            continue
        
        # Check for cross-source duplicates with Waze accidents
        is_duplicate = False
        for waze_id in waze_processed:
            if addresses_similar(location, waze_id):
                log_message(f"Skipping Telegram accident - duplicate with Waze: {location}")
                is_duplicate = True
                break
        
        if is_duplicate:
            telegram_processed.add(message_id)
            continue
        
        # Format and send message
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = format_sgaccident_message(text, location, timestamp)
        
        if send_telegram_message(formatted_message):
            telegram_processed.add(message_id)
            new_accidents += 1
            log_message(f"New @sgaccident report: {location}")
            time.sleep(1)  # Rate limiting
    
    # Save the new offset and processed IDs
    save_telegram_offset(latest_offset)
    save_processed_accidents(waze_processed, telegram_processed)
    
    if new_accidents > 0:
        log_message(f"Processed {new_accidents} new @sgaccident reports")

def main():
    """Main monitoring loop"""
    log_message("Starting enhanced accident monitoring with dual sources...")
    log_message(f"Monitoring Waze API and @sgaccident channel")
    log_message(f"Target channel: {CHAT_ID}")
    
    while True:
        try:
            # Process both sources
            process_waze_accidents()
            process_sgaccident_updates()
            
            # Clean up old processed accidents (keep last 1000)
            waze_processed, telegram_processed = load_processed_accidents()
            if len(waze_processed) > 1000:
                waze_processed = set(list(waze_processed)[-500:])
            if len(telegram_processed) > 1000:
                telegram_processed = set(list(telegram_processed)[-500:])
            save_processed_accidents(waze_processed, telegram_processed)
            
            log_message("Monitoring cycle complete, sleeping for 30 seconds...")
            time.sleep(30)
            
        except KeyboardInterrupt:
            log_message("Monitoring stopped by user")
            break
        except Exception as e:
            log_message(f"Error in main loop: {e}")
            time.sleep(60)  # Wait longer on error

if __name__ == "__main__":
    main()