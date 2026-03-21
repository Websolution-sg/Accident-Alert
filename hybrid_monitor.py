#!/usr/bin/env python3
"""
Simple Telegram monitoring - Forward all accident reports directly
No duplicate checking, no filtering - just post everything from @sgaccident
"""
import asyncio
import json
import datetime
import requests

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
SGACCIDENT_CHANNEL_ID = "-1001486947378"  # @sgaccident
TARGET_CHANNEL_ID = "-1003683261194"      # Your target channel

# Simple tracking for bot API updates only
LAST_UPDATE_FILE = "simple_last_update_id.json"

def log_message(message):
    """Log messages with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] SIMPLE: {message}", flush=True)

def load_last_update_id():
    """Load last update ID for bot API"""
    try:
        with open(LAST_UPDATE_FILE, 'r') as f:
            data = json.load(f)
            return data.get("update_id", 0)
    except:
        return 0

def save_last_update_id(update_id):
    """Save last update ID"""
    try:
        with open(LAST_UPDATE_FILE, 'w') as f:
            json.dump({"update_id": update_id}, f)
    except Exception as e:
        log_message(f"Error saving update ID: {e}")

def send_telegram_message(message_text):
    """Send message to target channel"""
    try:
        response = requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            data={
                'chat_id': TARGET_CHANNEL_ID,
                'text': message_text,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': True
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['result']['message_id']
        else:
            log_message(f"Failed to send message: {response.status_code}")
            return None
    except Exception as e:
        log_message(f"Error sending message: {e}")
        return None

def format_simple_message(text, message_id, chat_title="@sgaccident"):
    """Format using original detailed format - no duplicate checking"""
    # Extract location from text
    lines = text.strip().split('\n')
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
    if chat_title.lower() == "@sgaccident":
        reporter = "@sgaccident user"
    else:
        reporter = chat_title
    
    # Build the message using original detailed format
    message = f"Accident on {location_text}\n"
    message += f"🕐 Reported: {timestamp}\n"
    message += f"👤 Reported by: {reporter}\n"
    message += f"📈 Confidence: N/A\n"
    message += f"✅ Reliability: N/A\n\n"
    
    # Try to extract coordinates from text
    import re
    coord_pattern = r'(\d+\.\d+),\s*(\d+\.\d+)'
    match = re.search(coord_pattern, text)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        google_maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        waze_url = f"https://www.waze.com/ul?ll={lat},{lon}&navigate=yes"
        message += f"🗺️ [View on Google Maps ({lat:.6f}, {lon:.6f})]({google_maps_url})\n"
        message += f"🚗 [Open in Waze ({lat:.6f}, {lon:.6f})]({waze_url})"
    else:
        message += f"🗺️ Location coordinates not available"
    
    return message

def get_bot_updates(last_update_id=0):
    """Get updates from Telegram bot API"""
    try:
        response = requests.get(
            f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates',
            params={
                'offset': last_update_id + 1,
                'limit': 100,
                'timeout': 10
            },
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            log_message(f"Failed to get updates: {response.status_code}")
            return None
    except Exception as e:
        log_message(f"Error getting updates: {e}")
        return None

def process_channel_updates():
    """Process new updates from channels - forward everything directly"""
    last_update_id = load_last_update_id()
    
    updates_data = get_bot_updates(last_update_id)
    if not updates_data or not updates_data.get('result'):
        return
    
    new_messages = 0
    latest_update_id = last_update_id
    
    for update in updates_data['result']:
        try:
            update_id = update['update_id']
            latest_update_id = max(latest_update_id, update_id)
            
            # Check for channel posts
            if 'channel_post' in update:
                message = update['channel_post']
                chat_id = str(message['chat']['id'])
                message_id = message['message_id']
                
                # Check if this is from @sgaccident or similar accident channels
                if chat_id == SGACCIDENT_CHANNEL_ID or 'accident' in message.get('chat', {}).get('title', '').lower():
                    text = message.get('text', '')
                    chat_title = message.get('chat', {}).get('title', 'Unknown')
                    
                    if text and len(text.strip()) > 5:  # Just avoid completely empty messages
                        log_message(f"📨 New message from {chat_title}")
                        log_message(f"📄 Content: {text[:100]}...")
                        
                        # Format and send message directly - NO duplicate checking
                        formatted_msg = format_simple_message(text, message_id, chat_title)
                        sent_id = send_telegram_message(formatted_msg)
                        
                        if sent_id:
                            new_messages += 1
                            log_message(f"✅ Forwarded message (ID: {sent_id})")
                        else:
                            log_message("❌ Failed to forward message")
                        
        except Exception as e:
            log_message(f"Error processing update: {e}")
            continue
    
    # Save progress
    if latest_update_id > last_update_id:
        save_last_update_id(latest_update_id)
    
    if new_messages > 0:
        log_message(f"📊 Forwarded {new_messages} new messages")

async def main():
    """Main monitoring loop"""
    log_message("🚀 Starting Simple Telegram Monitor")
    log_message("📡 Monitoring @sgaccident - NO duplicate checking")
    log_message(f"🎯 Target channel: {TARGET_CHANNEL_ID}")
    
    # Send startup notification
    startup_message = f"""🔄 **Simple Monitor Started** - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Method:** Simple Bot API - Forward Everything
**VM:** sg-accident-monitor (us-central1-a) 
**Target:** 🇸🇬Sg accidents
**Source:** @sgaccident
**Mode:** ✅ NO duplicate checking - ALL messages forwarded
**Status:** ✅ Active and ready

*This version forwards ALL accident reports immediately*"""
    
    send_telegram_message(startup_message)
    log_message("📢 Startup notification sent")
    
    # Main monitoring loop
    while True:
        try:
            process_channel_updates()
            await asyncio.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            log_message("⏹️  Monitoring stopped by user")
            break
        except Exception as e:
            log_message(f"❌ Error in monitoring loop: {e}")
            await asyncio.sleep(60)  # Wait longer if there's an error

if __name__ == "__main__":
    asyncio.run(main())