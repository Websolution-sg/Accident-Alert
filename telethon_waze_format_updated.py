#!/usr/bin/env python3
"""
User-based Telegram monitoring for @sgaccident channel
Uses user account (@pukiboi) instead of bot API for channel access
"""
import asyncio
import json
import os
import datetime
import re
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

# Session file
SESSION_FILE = "pukiboi_final_session"

# Data files
USER_PROCESSED_FILE = "user_processed_accidents.json"

# Singapore bounds for filtering
SINGAPORE_BOUNDS = {
    "north": 1.4784,
    "south": 1.1496,
    "east": 104.0853,
    "west": 103.6065
}

def log_message(message):
    """Log messages with timestamp (Singapore Time)"""
    timestamp = datetime.datetime.now(SGT).strftime("%Y-%m-%d %H:%M:%S SGT")
    print(f"[{timestamp}] TELETHON: {message}", flush=True)

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
    """Check if text is primarily about Malaysia (not just mentioning it)"""
    if not text:
        return False
    text_lower = text.lower()
    
    # Strong Malaysia indicators (block these)
    strong_malaysia_keywords = ['malaysia', 'kl', 'kuala lumpur', 'selangor', 'penang']
    
    # Johor is special case - could be relevant to Singapore traffic
    # Only block if it's clearly about Malaysian side
    if 'johor' in text_lower:
        # Allow if mentions Singapore or causeway (cross-border traffic)
        if any(sg_keyword in text_lower for sg_keyword in ['singapore', 'causeway', 'woodlands', 'checkpoint', 'customs', 'border']):
            return False
    
    return any(keyword in text_lower for keyword in strong_malaysia_keywords)

def is_accident_related(text):
    """Check if text is related to accidents or traffic incidents"""
    if not text:
        return False
    
    text_lower = text.lower()
    accident_keywords = [
        # Original accident keywords
        'accident', 'crash', 'collision', 'hit', 'injured', 'ambulance', 
        'police', 'traffic police', 'scdf', 'emergency', 'road block',
        'breakdown', 'stalled', 'blocked', 'lane closed',
        
        # Additional traffic/incident keywords commonly used in @sgaccident
        'incident', 'situation', 'congestion', 'traffic', 'jam', 'slow moving', 'slow traffic',
        'vehicle', 'car trouble', 'road works', 'construction', 'closure', 'disruption', 'delay',
        'obstruction', 'hazard', 'alert', 'warning', 'caution', 'avoid', 'alternative route',
        'stationary', 'stuck', 'lane change', 'merge', 'exit', 'ramp', 'slip road'
    ]
    
    return any(keyword in text_lower for keyword in accident_keywords)

def load_user_processed_accidents():
    """Load processed accident IDs"""
    try:
        if os.path.exists(USER_PROCESSED_FILE):
            with open(USER_PROCESSED_FILE, 'r') as f:
                return set(json.load(f))
    except Exception as e:
        log_message(f"Error loading processed accidents: {e}")
    return set()

def save_user_processed_accidents(processed_ids):
    """Save processed accident IDs"""
    try:
        with open(USER_PROCESSED_FILE, 'w') as f:
            json.dump(list(processed_ids), f)
    except Exception as e:
        log_message(f"Error saving processed accidents: {e}")

def format_user_accident_message(original_text, coordinates=None):
    """Format accident message using exact same format as Waze monitoring"""
    # Extract location from text - improved extraction
    lines = original_text.strip().split('\n')
    location_text = "Unknown location"
    
    # Look for location patterns in the text (improved)
    for line in lines:
        line = line.strip()
        # Check for Singapore road/location keywords
        if any(keyword in line.lower() for keyword in [
            'road', 'rd', 'street', 'st', 'avenue', 'ave', 'expressway', 'highway',
            'pie', 'cte', 'aye', 'bke', 'sle', 'tpe', 'kpe', 'ecp', 'mrt', 'lrt',
            'tampines', 'jurong', 'woodlands', 'bedok', 'clementi', 'bishan',
            'ang mo kio', 'toa payoh', 'bukit timah', 'orchard', 'marina']):
            location_text = line
            break
        elif len(line) > 10 and not line.startswith('🚨') and not line.startswith('Traffic') and not line.startswith('#'):
            location_text = line
            break
    
    # If still no good location, use first meaningful line
    if location_text == "Unknown location" and lines:
        for line in lines:
            line = line.strip()
            if len(line) > 5 and not line.startswith('🚨') and not line.startswith('@'):
                location_text = line[:100]  # Limit length
                break
    
    # Clean up location text (remove extra @sgaccident mentions, etc.)
    location_text = location_text.replace('@sgaccident', '').strip()
    if location_text.startswith(':'):
        location_text = location_text[1:].strip()
    
    # Format timestamp with proper SGT timezone (exact match to Waze)
    timestamp = datetime.datetime.now(SGT).strftime('%Y-%m-%d %H:%M:%S SGT')
    
    # Build the message using EXACT same format as Waze
    message = f"Accident on {location_text}\n"
    message += f"🕐 Reported: {timestamp}\n"
    message += f"👤 Reported by: @sgaccident community\n"
    message += f"📈 Confidence: Community verified\n"
    message += f"✅ Reliability: Community verified\n\n"
    
    # Add coordinates if available (exact same precision as Waze)
    if coordinates and len(coordinates) == 2:
        lat, lon = coordinates
        google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        waze_url = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
        message += f"🗺️ [View on Google Maps ({lat:.6f}, {lon:.6f})]({google_maps_url})\n"
        message += f"🚗 [Open in Waze ({lat:.6f}, {lon:.6f})]({waze_url})"
    else:
        message += f"🗺️ Location coordinates not available"
    
    return message

async def setup_client():
    """Setup and authenticate Telegram client"""
    if not all([API_ID, API_HASH, PHONE_NUMBER]):
        log_message("❌ Missing credentials! Please set API_ID, API_HASH, and PHONE_NUMBER")
        return None
    
    client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
    
    try:
        # Start with phone number - should use existing session
        await client.start(phone=PHONE_NUMBER)
        
        # Verify authentication
        me = await client.get_me()
        log_message(f"✅ Telethon authenticated as: @{me.username or 'pukiboi'} ({me.first_name or 'User'})")
        log_message(f"📱 Phone: {PHONE_NUMBER}")
        return client
    except Exception as e:
        log_message(f"❌ Telethon authentication failed: {e}")
        log_message("💡 You may need to run setup_telethon_session.py first")
        return None

async def monitor_sgaccident_user(client):
    """Monitor @sgaccident channel for accident messages - REAL-TIME with WAZE FORMATTING"""
    log_message("🚨 Starting REAL-TIME monitoring with @pukiboi user account")
    log_message("⚡ 0-1 second delivery - ALL messages converted to Waze format")
    log_message("🎯 FILTERING DISABLED - processing ALL @sgaccident messages")
    
    # Send startup notification
    startup_message = f"""🔄 **Telethon Monitor: Waze Format Conversion** - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**VM Status:** sg-accident-monitor running in us-central1-a
**Method:** User-based real-time monitoring with format conversion
**Process:** Real-time Telethon listener with Waze formatting
**Authentication:** @pukiboi user account connected via Telethon

📡 **Monitoring Setup**
**Source:** @sgaccident (-1001486947378) - 0-1 second real-time access
**Target:** 🇸🇬Sg accidents (-1003683261194)
**Filtering:** ❌ DISABLED - Processing ALL messages
**Format:** 📋 Converted to match Waze monitor format
**Performance:** Real-time delivery with consistent formatting

*Telethon monitor now converts ALL @sgaccident messages to Waze format (NO FILTERING)*"""
    
    try:
        await client.send_message(TARGET_CHANNEL_ID, startup_message, parse_mode='markdown')
        log_message("📢 Telethon Waze format conversion startup notification sent")
    except Exception as e:
        log_message(f"⚠️  Failed to send startup notification: {e}")
    
    message_count = 0
    processed_ids = load_user_processed_accidents()
    
    @client.on(events.NewMessage(chats=SGACCIDENT_CHANNEL_ID))
    async def handler(event):
        nonlocal message_count, processed_ids
        message_count += 1
        
        try:
            message = event.message
            text = message.text or ""
            
            # Log real-time reception
            log_message(f"⚡ REAL-TIME: Message #{message_count} received (ID: {message.id})")
            log_message(f"📝 Content preview: {text[:80]}{'...' if len(text) > 80 else ''}")
            
            # Check if already processed (duplicate prevention)
            if message.id in processed_ids:
                log_message("🔄 Already processed - skipping duplicate")
                return
            
            # FILTERING REMOVED - Process ALL messages from @sgaccident
            log_message("🚦 MESSAGE DETECTED - Converting to Waze format (NO FILTERING)")
            
            # Format message using Waze style
            formatted_message = format_user_accident_message(text)
            
            # Send formatted message
            await client.send_message(
                TARGET_CHANNEL_ID,
                formatted_message,
                parse_mode='markdown'
            )
            
            # Track as processed
            processed_ids.add(message.id)
            save_user_processed_accidents(processed_ids)
            
            log_message(f"✅ Message formatted and sent (Waze style) - Session total: {len(processed_ids)}")
            
        except Exception as e:
            log_message(f"❌ Error processing message: {e}")
    
    log_message("🔥 Real-time event listener ACTIVE - monitoring @sgaccident for ALL messages")
    log_message("⏳ Waiting for messages... (converting ALL to Waze format - NO FILTERING)")
    
    # Keep client running for real-time monitoring
    await client.run_until_disconnected()

async def main():
    """Main function"""
    log_message("🚀 Starting User-Based @sgaccident Monitor")
    log_message("📱 This will use @pukiboi credentials to access @sgaccident")
    
    client = await setup_client()
    if not client:
        return
    
    try:
        # Test channel access
        sgaccident_entity = await client.get_entity(SGACCIDENT_CHANNEL_ID)
        target_entity = await client.get_entity(TARGET_CHANNEL_ID)
        
        log_message(f"✅ Source channel: {sgaccident_entity.title}")
        log_message(f"✅ Target channel: {target_entity.title}")
        
        # Start monitoring
        await monitor_sgaccident_user(client)
        
    except Exception as e:
        log_message(f"❌ Error: {e}")
    finally:
        if client:
            await client.disconnect()

if __name__ == "__main__":
    log_message("🚀 Starting TELETHON User-Based @sgaccident Monitor")
    log_message("🔑 Using @pukiboi credentials via Telethon API")
    
    if API_ID and API_HASH and PHONE_NUMBER:
        asyncio.run(main())
    else:
        log_message("❌ Missing Telethon credentials!")
        log_message("📝 Please configure API_ID, API_HASH, and PHONE_NUMBER")