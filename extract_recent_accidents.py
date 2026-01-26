#!/usr/bin/env python3
import requests
import json
import datetime
import time
import re
import math

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
SGACCIDENT_CHAT_ID = "-1001486947378"  # Source channel
TARGET_CHAT_ID = "-1003683261194"      # Target channel

SINGAPORE_BOUNDS = {
    "north": 1.4784,
    "south": 1.1496,
    "east": 104.0853,
    "west": 103.6065
}

def log_message(message):
    """Log messages with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

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

def contains_malaysia_keywords(text):
    """Check if text contains Malaysia-related keywords"""
    if not text:
        return False
    text_lower = text.lower()
    malaysia_keywords = ['malaysia', 'johor', 'kl', 'kuala lumpur', 'selangor', 'penang', 'perak', 'kedah', 'terengganu', 'kelantan', 'pahang', 'negeri sembilan', 'melaka', 'sabah', 'sarawak']
    return any(keyword in text_lower for keyword in malaysia_keywords)

def is_accident_related(text):
    """Check if text is related to accidents"""
    if not text:
        return False
    
    text_lower = text.lower()
    accident_keywords = [
        'accident', 'crash', 'collision', 'hit', 'injured', 'ambulance', 
        'police', 'traffic police', 'scdf', 'emergency', 'road block',
        'breakdown', 'stalled', 'blocked', 'lane closed', 'diversions',
        'jam', 'congestion', 'incident', 'alert'
    ]
    
    return any(keyword in text_lower for keyword in accident_keywords)

def format_accident_message(original_text, coordinates=None, original_date=None):
    """Format accident message for reposting"""
    message = "🚨 <b>HISTORICAL ACCIDENT ALERT</b> 🚨\n\n"
    
    # Add the original message content
    message += f"📄 <b>Details:</b> {original_text}\n"
    
    # Add coordinates if available
    if coordinates and len(coordinates) == 2:
        lat, lon = coordinates
        message += f"🗺️ <b>Coordinates:</b> {lat}, {lon}\n"
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        message += f"🔗 <b>View on Maps:</b> <a href='{maps_url}'>Open Location</a>\n"
    
    # Add original date if available
    if original_date:
        message += f"📅 <b>Original Post:</b> {original_date}\n"
    
    message += f"⏰ <b>Extracted:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    message += f"🔗 <b>Source:</b> @sgaccident Channel (Historical)"
    
    return message

def send_telegram_message(message):
    """Send message to target channel"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TARGET_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            log_message("Message sent successfully")
            return True
        else:
            log_message(f"Failed to send message: {response.text}")
            return False
    except Exception as e:
        log_message(f"Error sending message: {e}")
        return False

def get_channel_history():
    """Get recent message history from @sgaccident channel"""
    log_message("Fetching message history from @sgaccident channel...")
    
    # We'll use getUpdates to get recent messages
    # Note: This method has limitations and may not get all historical messages
    # For full history, we'd need different approach
    
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {
            'limit': 100,  # Get up to 100 recent updates
            'timeout': 10
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            log_message(f"Failed to get updates: {response.status_code}")
            return []
        
        data = response.json()
        if not data.get('ok'):
            log_message(f"API error: {data.get('description', 'Unknown error')}")
            return []
        
        updates = data.get('result', [])
        messages = []
        
        for update in updates:
            if 'channel_post' in update:
                post = update['channel_post']
                chat_id = str(post.get('chat', {}).get('id', ''))
                
                # Only process @sgaccident channel
                if chat_id == SGACCIDENT_CHAT_ID:
                    message_id = post.get('message_id')
                    text = post.get('text', '') or post.get('caption', '')
                    date = post.get('date')
                    
                    if text:
                        # Convert Unix timestamp to readable date
                        post_date = datetime.datetime.fromtimestamp(date) if date else None
                        messages.append({
                            'message_id': message_id,
                            'text': text,
                            'date': post_date,
                            'unix_date': date
                        })
        
        # Sort by date (newest first)
        messages.sort(key=lambda x: x['unix_date'] or 0, reverse=True)
        log_message(f"Found {len(messages)} total messages from @sgaccident")
        
        return messages
        
    except Exception as e:
        log_message(f"Error fetching channel history: {e}")
        return []

def main():
    """Extract and repost last 5 accident posts"""
    log_message("Starting historical accident extraction...")
    log_message(f"Source: @sgaccident channel ({SGACCIDENT_CHAT_ID})")
    log_message(f"Target: {TARGET_CHAT_ID}")
    
    # Get message history
    messages = get_channel_history()
    
    if not messages:
        log_message("No messages found or error occurred")
        return
    
    # Filter for accident-related messages
    accident_messages = []
    for msg in messages:
        text = msg['text']
        if is_accident_related(text) and not contains_malaysia_keywords(text):
            accident_messages.append(msg)
    
    log_message(f"Found {len(accident_messages)} accident-related messages")
    
    # Get last 5 accident posts
    recent_accidents = accident_messages[:5]
    
    if not recent_accidents:
        log_message("No recent accident posts found to extract")
        return
    
    log_message(f"Extracting and reposting {len(recent_accidents)} recent accidents...")
    
    posted_count = 0
    for i, msg in enumerate(recent_accidents, 1):
        text = msg['text']
        post_date = msg['date']
        
        log_message(f"Processing accident {i}/{len(recent_accidents)}: {text[:60]}...")
        
        # Extract coordinates
        lat, lon = extract_coordinates_from_text(text)
        
        # Format message
        date_str = post_date.strftime('%Y-%m-%d %H:%M:%S') if post_date else 'Unknown'
        formatted_message = format_accident_message(
            text, 
            (lat, lon) if lat and lon else None,
            date_str
        )
        
        # Send message
        if send_telegram_message(formatted_message):
            posted_count += 1
            log_message(f"✅ Posted accident {i}: {text[:50]}...")
            time.sleep(2)  # Delay between posts to avoid rate limits
        else:
            log_message(f"❌ Failed to post accident {i}")
    
    log_message(f"✅ Extraction complete! Posted {posted_count}/{len(recent_accidents)} accidents")
    
    if posted_count < len(recent_accidents):
        log_message(f"⚠️ Some posts failed to send. Check Telegram bot permissions.")

if __name__ == "__main__":
    main()