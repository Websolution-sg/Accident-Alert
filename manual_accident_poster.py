#!/usr/bin/env python3
import requests
import json
import datetime
import re
import math

# Configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
TARGET_CHAT_ID = "-1003683261194"  # Your channel

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
    
    # Pattern 2: Coordinates in parentheses or different formats
    pattern2 = r'\(?(\d+\.\d+)\s*[,\s]\s*(\d+\.\d+)\)?'
    matches2 = re.finditer(pattern2, text)
    for match in matches2:
        lat, lon = float(match.group(1)), float(match.group(2))
        if is_within_singapore(lat, lon):
            return lat, lon
    
    return None, None

def format_accident_message(original_text, coordinates=None):
    """Format accident message for reposting"""
    message = "🚨 <b>ACCIDENT ALERT</b> 🚨\n\n"
    
    # Add the original message content
    message += f"📄 <b>Details:</b> {original_text}\n"
    
    # Add coordinates if available
    if coordinates and len(coordinates) == 2:
        lat, lon = coordinates
        message += f"🗺️ <b>Coordinates:</b> {lat}, {lon}\n"
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        message += f"🔗 <b>View on Maps:</b> <a href='{maps_url}'>Open Location</a>\n"
    
    message += f"⏰ <b>Time:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    message += f"🔗 <b>Source:</b> @sgaccident Channel"
    
    return message

def send_telegram_message(message):
    """Send message to your target channel"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TARGET_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                log_message("✅ Message posted successfully")
                return True
            else:
                log_message(f"❌ Failed to send: {data.get('description')}")
                return False
        else:
            log_message(f"❌ HTTP error: {response.status_code}")
            return False
    except Exception as e:
        log_message(f"❌ Error sending message: {e}")
        return False

def test_your_channel():
    """Test if bot can post to your channel"""
    log_message("Testing access to your channel...")
    
    try:
        # Test with getChat first
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
        response = requests.get(url, params={'chat_id': TARGET_CHAT_ID}, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                chat_info = data.get('result', {})
                log_message(f"✅ Your channel: {chat_info.get('title', 'Unknown')}")
                
                # Test sending a message
                test_msg = "🔧 <b>Bot Test</b>\n\nTesting manual accident posting system...\n\n⏰ " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if send_telegram_message(test_msg):
                    log_message("✅ Your channel is ready for accident posts!")
                    return True
                else:
                    log_message("❌ Cannot send messages to your channel")
                    return False
            else:
                log_message(f"❌ Cannot access your channel: {data.get('description')}")
                return False
        else:
            log_message(f"❌ HTTP error accessing your channel: {response.status_code}")
            return False
    except Exception as e:
        log_message(f"❌ Error testing your channel: {e}")
        return False

def manual_post_accident(accident_text):
    """Manually post an accident that you've copied from @sgaccident"""
    log_message("Processing manual accident post...")
    
    # Extract coordinates if present
    lat, lon = extract_coordinates_from_text(accident_text)
    
    # Format and send
    formatted_message = format_accident_message(accident_text, (lat, lon) if lat and lon else None)
    
    if send_telegram_message(formatted_message):
        log_message("✅ Accident posted successfully!")
        return True
    else:
        log_message("❌ Failed to post accident")
        return False

def interactive_mode():
    """Interactive mode for manual posting"""
    log_message("🎯 MANUAL ACCIDENT POSTING SYSTEM")
    log_message("Since you can't add bot to @sgaccident, use this for manual posting")
    print()
    print("📋 INSTRUCTIONS:")
    print("1. Visit: https://web.telegram.org/a/#-1001486947378")
    print("2. Copy accident text from @sgaccident")
    print("3. Paste it below when prompted")
    print("4. System will format and post to your channel")
    print()
    
    while True:
        print("=" * 50)
        choice = input("Enter 'p' to post accident, 't' to test channel, or 'q' to quit: ").lower().strip()
        
        if choice == 'q':
            log_message("Goodbye!")
            break
        elif choice == 't':
            test_your_channel()
        elif choice == 'p':
            print("\nPaste the accident text from @sgaccident (press Enter twice when done):")
            lines = []
            while True:
                line = input()
                if line == "" and len(lines) > 0:
                    break
                lines.append(line)
            
            if lines:
                accident_text = "\n".join(lines)
                print(f"\nProcessing: {accident_text[:50]}...")
                manual_post_accident(accident_text)
            else:
                print("No text entered.")
        else:
            print("Invalid choice. Use 'p', 't', or 'q'")

def main():
    """Main function"""
    print("🚨 MANUAL ACCIDENT EXTRACTION TOOL 🚨")
    print("=" * 50)
    print()
    print("⚠️  LIMITATION: Cannot auto-extract from @sgaccident")
    print("   (Bot needs admin access which you don't have)")
    print()
    print("✅ SOLUTION: Manual copy-paste system")
    print("   1. You copy accident text from @sgaccident")
    print("   2. This tool formats and posts to your channel")
    print("   3. Includes coordinates, maps links, timestamps")
    print()
    
    # Test your channel first
    if not test_your_channel():
        log_message("❌ Cannot access your channel. Check bot permissions.")
        return
    
    print()
    print("🎯 Your channel is ready! Starting interactive mode...")
    print()
    
    interactive_mode()

if __name__ == "__main__":
    main()