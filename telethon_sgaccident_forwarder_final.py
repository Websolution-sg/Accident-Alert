#!/usr/bin/env python3
"""
Enhanced Telethon monitor for @sgaccident channel with Waze-style formatting
Uses @pukiboi user account authentication
Formats posts with same structure as Waze monitoring
"""
import asyncio
import json
import os
import datetime
import re
import requests
from datetime import timezone, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel

# Singapore timezone (UTC+8)
SGT = timezone(timedelta(hours=8))

# Configuration
API_ID = 37340693
API_HASH = "59c3213333e09271844a64d38be167a4"
PHONE_NUMBER = "+6598590227"  # @pukiboi's phone number

# Channel IDs
SGACCIDENT_CHANNEL_ID = -1001486947378  # @sgaccident (source)
TARGET_CHANNEL_ID = -1003683261194      # Your target channel (where to post)

# Bot token for posting
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"

# Session file
SESSION_FILE = "pukiboi_final_session"

# Data files
USER_PROCESSED_FILE = "telethon_processed_accidents.json"

def log_message(message):
    """Log messages with timestamp (Singapore Time)"""
    timestamp = datetime.datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S SGT")    
    print(f"[{timestamp}] TELETHON: {message}", flush=True)

def extract_location_from_text(text):
    """Extract location information from @sgaccident text with enhanced coordinate detection"""
    if not text:
        return None, None, None  # street, coordinates, area
    
    # Enhanced coordinate extraction patterns for @sgaccident messages
    coordinate_patterns = [
        # Google Maps URLs - various formats
        r'google\.com/maps[^\s]*[?&]q=([+-]?\d+\.\d+),([+-]?\d+\.\d+)',
        r'maps\.google\.com[^\s]*[?&]q=([+-]?\d+\.\d+),([+-]?\d+\.\d+)',
        r'google\.com/maps/place/([+-]?\d+\.\d+),([+-]?\d+\.\d+)',
        r'maps\.app\.goo\.gl[^\s]*',  # Short Google Maps links (need geocoding)
        # Direct coordinate patterns
        r'([+-]?\d+\.\d{4,}),\s*([+-]?\d+\.\d{4,})',  # High precision coords
        r'(\d+\.\d+),\s*(\d+\.\d+)',  # Basic lat,lon format
    ]
    
    # Try to extract coordinates first (higher priority for @sgaccident)
    for pattern in coordinate_patterns:
        coord_match = re.search(pattern, text)
        if coord_match:
            try:
                if 'goo.gl' in coord_match.group(0):
                    # Skip short URLs for now (would need API to resolve)
                    continue
                lat = float(coord_match.group(1))
                lon = float(coord_match.group(2))
                # Validate Singapore coordinates
                if 1.1 <= lat <= 1.5 and 103.6 <= lon <= 104.1:
                    return None, (lat, lon), None
            except (ValueError, IndexError):
                continue
    
    # Common location patterns in Singapore accident reports
    location_patterns = [
        r'(?i)(?:accident|crash)\s+(?:at|on|near|along)\s+([^,\n\r]+)(?:[,\n\r]|$)',
        r'(?i)(?:at|near|along|on)\s+([^,\n\r]+?)(?:\s+(?:exit|entrance|junction|towards))?[,\n\r]',
        r'(?i)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Road|Rd|Street|St|Avenue|Ave|Highway|Expressway|PIE|KPE|AYE|CTE|BKE|SLE|TPE)',
        r'(?i)([\w\s]+(?:Road|Rd|Street|St|Avenue|Ave|Highway|Expressway))(?:\s+(?:exit|entrance))?',
        r'(?i)(PIE|CTE|AYE|BKE|SLE|TPE|KPE|ECP)(?:\s+\([^)]+\))?(?:\s+(?:at|near|after|before)\s+([^,\n\r]+))?',
        r'(?i)(Jurong|Woodlands|Tampines|Bedok|Toa Payoh|Ang Mo Kio|Bishan|Clementi|Sembawang|Punggol|Sengkang|Hougang|Serangoon|Marine Parade|Kallang|Novena|Orchard|Bugis|Marina|Sentosa)(?:\s+([^,\n\r]+))?',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, text)
        if match:
            location_parts = [part for part in match.groups() if part and part.strip()]
            if location_parts:
                location = ' '.join(location_parts).strip()
                if len(location) > 3:  # Filter out very short matches
                    return location, None, None
    
    # Fallback - try to extract any meaningful location text from first line
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    for line in lines[:2]:  # Check first 2 lines only
        if any(word in line.lower() for word in ['road', 'street', 'avenue', 'expressway', 'highway', 'mrt', 'station', 'cte', 'pie', 'aye']):
            # Clean up the line
            clean_line = re.sub(r'^[^a-zA-Z]*', '', line)  # Remove leading non-letters
            clean_line = re.sub(r'\s+', ' ', clean_line)    # Normalize spaces
            if len(clean_line) > 5:
                return clean_line, None, None
    
    return None, None, None

def extract_time_from_text(text):
    """Extract timestamp from @sgaccident text if available"""
    if not text:
        return datetime.datetime.now(SGT)
    
    # Look for time patterns like "12:34 PM" or "15:30"
    time_patterns = [
        r'(\d{1,2}):(\d{2})\s*(AM|PM)',
        r'(\d{1,2})\.(\d{2})\s*(AM|PM)', 
        r'(\d{1,2}):(\d{2})',
        r'(\d{2})(\d{2})\s*hrs?',
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                hour = int(match.group(1))
                minute = int(match.group(2))
                
                # Handle AM/PM
                if len(match.groups()) > 2 and match.group(3):
                    if match.group(3).upper() == 'PM' and hour != 12:
                        hour += 12
                    elif match.group(3).upper() == 'AM' and hour == 12:
                        hour = 0
                
                # Create datetime with today's date
                now = datetime.datetime.now(SGT)
                extracted_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # If extracted time is in future, assume it's from yesterday
                if extracted_time > now:
                    extracted_time -= timedelta(days=1)
                
                return extracted_time
            except (ValueError, IndexError):
                continue
    
    return datetime.datetime.now(SGT)

def format_sgaccident_message(original_text, message_date):
    """Use original @sgaccident first line header with enhanced coordinate formatting"""
    # Extract the first line from @sgaccident message
    lines = original_text.strip().split('\n')
    first_line = lines[0].strip() if lines else "Accident in Singapore"
    
    # Extract coordinates from Google Maps URLs if present
    coordinates = None
    
    # Enhanced coordinate extraction patterns for @sgaccident messages
    coordinate_patterns = [
        # Google Maps URLs - various formats
        r'google\.com/maps[^\s]*[?&]q=([+-]?\d+\.\d+),([+-]?\d+\.\d+)',
        r'maps\.google\.com[^\s]*[?&]q=([+-]?\d+\.\d+),([+-]?\d+\.\d+)',
        r'google\.com/maps/place/([+-]?\d+\.\d+),([+-]?\d+\.\d+)',
        # Direct coordinate patterns
        r'([+-]?\d+\.\d{4,}),\s*([+-]?\d+\.\d{4,})',  # High precision coords
        r'(\d+\.\d+),\s*(\d+\.\d+)',  # Basic lat,lon format
    ]
    
    # Try to extract coordinates from the message
    for pattern in coordinate_patterns:
        coord_match = re.search(pattern, original_text)
        if coord_match:
            try:
                lat = float(coord_match.group(1))
                lon = float(coord_match.group(2))
                # Validate Singapore coordinates
                if 1.1 <= lat <= 1.5 and 103.6 <= lon <= 104.1:
                    coordinates = (lat, lon)
                    break
            except (ValueError, IndexError):
                continue
    
    # Start with the original @sgaccident first line
    message = first_line + "\n"
    
    # Add timestamp
    timestamp = datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')
    message += f"🕐 Reported: {timestamp}\n"
    message += f"👤 Reported by: @sgaccident community\n"
    message += f"📈 Confidence: Community verified\n"
    message += f"✅ Reliability: Community verified\n\n"
    
    # Add coordinate links if coordinates were found
    if coordinates:
        lat, lon = coordinates
        google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        waze_url = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
        
        # Add coordinate links in same format as Enhanced Waze Monitor
        message += f"🗺️ [View on Google Maps ({lat:.6f}, {lon:.6f})]({google_maps_url})\n"
        message += f"🚗 [Open in Waze ({lat:.6f}, {lon:.6f})]({waze_url})"
    else:
        # Fallback for Singapore general area
        message += f"🗺️ [View on Google Maps (Singapore)](https://www.google.com/maps/place/Singapore)\n"
        message += f"🚗 [Open in Waze (Singapore)](https://www.waze.com/ul?q=Singapore&navigate=yes)"
    
    return message

def send_telegram_message(message):
    """Send message to target Telegram channel using bot API"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': TARGET_CHANNEL_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        log_message(f"❌ Failed to send message: {e}")
        return False

def load_processed_messages():
    """Load list of processed message IDs"""
    try:
        if os.path.exists(USER_PROCESSED_FILE):
            with open(USER_PROCESSED_FILE, 'r') as f:
                return set(json.load(f))
    except Exception as e:
        log_message(f"Error loading processed messages: {e}")
    return set()

def save_processed_messages(processed_set):
    """Save list of processed message IDs"""
    try:
        with open(USER_PROCESSED_FILE, 'w') as f:
            json.dump(list(processed_set), f)
        return True
    except Exception as e:
        log_message(f"Error saving processed messages: {e}")
        return False

async def setup_client():
    """Initialize and return Telethon client"""
    try:
        client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
        await client.start(phone=PHONE_NUMBER)
        
        # Verify connection
        me = await client.get_me()
        log_message(f"✅ Connected as @{me.username} ({me.first_name})")
        
        return client
    except Exception as e:
        log_message(f"❌ Failed to connect: {e}")
        return None

async def main():
    """Main monitoring function"""
    log_message("🚀 Starting Enhanced @sgaccident Monitor with Waze-Style Formatting")
    log_message("🔄 Using @pukiboi user account authentication")
    log_message("🎨 Posts will be formatted like Waze accidents")
    
    # Load processed messages
    processed_messages = load_processed_messages()
    log_message(f"📁 Loaded {len(processed_messages)} processed messages")
    
    # Setup client
    client = await setup_client()
    if not client:
        log_message("❌ Could not establish connection")
        return
    
    # Test message
    test_msg = "🎯 Enhanced @sgaccident monitor with Waze formatting is ACTIVE!\n📱 Real-time monitoring started\n🎨 Messages will be formatted with location, time, and maps links"
    if send_telegram_message(test_msg):
        log_message("📧 Startup notification sent")
    
    @client.on(events.NewMessage(chats=SGACCIDENT_CHANNEL_ID))
    async def handler(event):
        try:
            message_id = event.message.id
            
            # Skip if already processed
            if message_id in processed_messages:
                return
            
            # Get message content
            text = event.message.message or ""
            message_date = event.message.date.astimezone(SGT)
            
            log_message(f"📨 New message: {text[:100]}...")
            
            # Format message with Waze-style formatting
            formatted_message = format_sgaccident_message(text, message_date)
            
            # Send formatted message
            if send_telegram_message(formatted_message):
                processed_messages.add(message_id)
                save_processed_messages(processed_messages)
                log_message(f"✅ Formatted and posted message {message_id}")
            else:
                log_message(f"❌ Failed to post message {message_id}")
                
        except Exception as e:
            log_message(f"❌ Error processing message: {e}")
    
    log_message("🎯 Real-time event listener ACTIVE - monitoring @sgaccident")
    log_message("🎨 Messages will be formatted with Waze-style layout")
    log_message("⚡ Waiting for messages... (0-1 second delivery)")
    
    # Keep the script running
    try:
        await client.run_until_disconnected()
    except KeyboardInterrupt:
        log_message("🛑 Manual stop requested")
    except Exception as e:
        log_message(f"💥 Connection lost: {e}")
    finally:
        log_message("🔚 Monitor stopped")

if __name__ == "__main__":
    asyncio.run(main())