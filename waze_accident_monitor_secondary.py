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
    """Extract location information from @sgaccident message"""
    if not text:
        return None
    
    # Look for location patterns
    location_patterns = [
        r'(?:at|near|along)\s+([^\.!?\n]+?)(?:\.|!|\?|$|\n)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Road|Street|Avenue|Drive|Boulevard|Highway|Expressway|Way|Lane|Place|Court|Circle))',
        r'(\w+\s+\w+(?:\s+\w+)*)\s*(?:accident|crash|collision)',
    ]
    
    for pattern in location_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            location = matches[0].strip()
            if len(location) > 3:  # Filter out very short matches
                return location
    
    # If no specific location pattern, try to extract from the first sentence
    sentences = text.split('.')
    if sentences:
        first_sentence = sentences[0].strip()
        # Remove common prefixes
        prefixes = ['accident', 'crash', 'collision', 'reported', 'alert']
        for prefix in prefixes:
            first_sentence = re.sub(f'^{prefix}\\s*', '', first_sentence, flags=re.IGNORECASE)
        
        if len(first_sentence) > 5 and len(first_sentence) < 100:
            return first_sentence
    
    return None

def format_sgaccident_message(original_text, location, timestamp):
    """Format @sgaccident message to match Waze format"""
    # Create a Waze-style message
    waze_message = f"🚨 <b>Accident Alert</b>\n\n"
    waze_message += f"📍 <b>Location:</b> {location}\n"
    waze_message += f"⏰ <b>Reported:</b> {timestamp}\n"
    waze_message += f"📱 <b>Source:</b> Community Report\n\n"
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
                
                # Filter for accidents
                accidents = self.filter_accidents(alerts)
                print(f"Found {len(accidents)} accidents")
                
                # Post new accidents
                waze_posted = 0
                for accident in accidents:
                    accident_id = self.get_accident_id(accident)
                    
                    # First check: accident ID already posted
                    if accident_id in self.posted_accidents:
                        print(f"⚠️ Skipping duplicate accident ID: {accident_id}")
                        continue
                    
                    # Second check: address already posted  
                    address = self.extract_address_from_waze(accident)
                    normalized_address = self.normalize_address(address)
                    print(f"🔍 Checking Waze accident: {address} (normalized: {normalized_address[:50]}...)")
                    
                    if address and (address in self.posted_addresses or normalized_address in self.posted_addresses):
                        # Show which source reported it first
                        source = self.address_sources.get(normalized_address, "unknown source")
                        print(f"⚠️ Skipping duplicate Waze accident at: {address} (already reported from {source})")
                        continue
                    
                    # Third check: similar address exists
                    is_duplicate = False
                    for existing_addr in self.posted_addresses:
                        if self.addresses_similar(normalized_address, existing_addr):
                            print(f"⚠️ Skipping similar Waze accident: {address} (similar to {existing_addr})")
                            is_duplicate = True
                            break
                    
                    if is_duplicate:
                        continue
                    
                    # All checks passed - post the accident
                    print(f"🔍 Processing accident: {accident.get('street', 'Unknown')} (ID: {accident_id[:8]}...)")
                    message = self.format_accident_message(accident)
                    if self.send_telegram_message(message):
                        print(f"✓ Posted Waze accident: {accident.get('street', 'Unknown')}")
                        print(f"  Address: {address}")
                        print(f"  Normalized: {normalized_address}")
                        print(f"  Accident ID: {accident_id}")
                        print(f"  Total addresses tracked: {len(self.posted_addresses)}")
                        print(f"  Total accident IDs tracked: {len(self.posted_accidents)}")
                        
                        # Add to tracking sets immediately to prevent race conditions
                        self.posted_accidents.add(accident_id)
                        if address:
                            self.posted_addresses.add(address)
                            self.address_sources[address] = "Waze API"
                            if normalized_address != address:
                                self.posted_addresses.add(normalized_address)
                                self.address_sources[normalized_address] = "Waze API"
                        waze_posted += 1
                    else:
                        print(f"✗ Failed to post Waze accident: {accident.get('street', 'Unknown')}")
                
                # Clean up old accident IDs and addresses (keep only last 1000)
                if len(self.posted_accidents) > 1000:
                    self.posted_accidents = set(list(self.posted_accidents)[-500:])
                
                if len(self.posted_addresses) > 1000:
                    self.posted_addresses = set(list(self.posted_addresses)[-500:])
                
                # Summary
                total_posted = sg_processed + waze_posted
                if total_posted > 0:
                    print(f"Total alerts posted this cycle: {total_posted}")
                
                print(f"Waiting {check_interval} seconds until next check...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\nStopping monitor...")
                break
            except Exception as e:
                print(f"Error in monitor loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying


def main():
    """
    Main function to run the monitor
    """
    # Get credentials from environment variables or set them here
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8500211695:AAFBFHrFII_ygxnmBjcFy0QsQqZQKfztV3U')
    TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '-1003683261194')
    
    # Bot token and channel ID are already configured
    
    # Create monitor and start
    monitor = WazeAccidentMonitor(TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID)
    
    # Check every 1 minute (60 seconds)
    monitor.monitor_and_post(check_interval=60)


if __name__ == "__main__":
    main()