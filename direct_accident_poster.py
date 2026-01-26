#!/usr/bin/env python3
import requests
import json
import datetime
import re

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
    """Format accident message for posting"""
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
    """Send message to your channel"""
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
                log_message("✅ Accident posted to your channel!")
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

def test_channel_access():
    """Test if bot can access your channel"""
    log_message("Testing bot access to your channel...")
    
    try:
        # Test with a simple message
        test_msg = "🔧 <b>Access Test</b>\n\nBot testing channel access...\n\n⏰ " + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if send_telegram_message(test_msg):
            log_message("✅ Channel access confirmed!")
            return True
        else:
            log_message("❌ Channel access failed")
            return False
    except Exception as e:
        log_message(f"❌ Error testing channel: {e}")
        return False

def post_accident_from_text(accident_text):
    """Process and post accident text"""
    log_message("Processing accident text...")
    
    # Extract coordinates
    lat, lon = extract_coordinates_from_text(accident_text)
    
    if lat and lon:
        log_message(f"Found coordinates: {lat}, {lon}")
    else:
        log_message("No coordinates found in text")
    
    # Format message
    formatted_message = format_accident_message(accident_text, (lat, lon) if lat and lon else None)
    
    # Send to channel
    return send_telegram_message(formatted_message)

def show_bot_setup_instructions():
    """Show instructions for adding bot to channel"""
    print("🤖 BOT SETUP INSTRUCTIONS")
    print("=" * 50)
    print()
    print("Your bot details:")
    print(f"• Bot username: @Accident_try_bot")
    print(f"• Bot ID: 8306581686")
    print()
    print("To add bot to your channel:")
    print("1. Open your channel: https://web.telegram.org/a/#-1003683261194")
    print("2. Click channel info/settings")
    print("3. Go to 'Administrators' or 'Manage Channel'")
    print("4. Click 'Add Administrator'")
    print("5. Search for: @Accident_try_bot")
    print("6. Add the bot with these permissions:")
    print("   ✅ Post Messages")
    print("   ✅ Delete Messages")
    print("   ✅ Edit Messages")
    print("7. Save changes")
    print()
    print("After adding the bot, run this script again!")
    print("=" * 50)

def interactive_mode():
    """Interactive mode for posting accidents"""
    while True:
        print("\n" + "=" * 50)
        choice = input("Enter 'p' to post accident, 't' to test channel, 'h' for help, or 'q' to quit: ").lower().strip()
        
        if choice == 'q':
            log_message("Goodbye!")
            break
        elif choice == 'h':
            show_bot_setup_instructions()
        elif choice == 't':
            test_channel_access()
        elif choice == 'p':
            print("\n📥 Paste accident text from @sgaccident:")
            print("(Type your text and press Enter, then type 'END' and press Enter)")
            
            lines = []
            while True:
                line = input()
                if line.strip().upper() == 'END':
                    break
                lines.append(line)
            
            if lines:
                accident_text = "\n".join(lines).strip()
                if accident_text:
                    print(f"\n🔄 Processing: {accident_text[:50]}...")
                    post_accident_from_text(accident_text)
                else:
                    print("❌ No text entered.")
            else:
                print("❌ No text entered.")
        else:
            print("❌ Invalid choice. Use 'p', 't', 'h', or 'q'")

def main():
    """Main function"""
    print("🚨 DIRECT ACCIDENT POSTING SYSTEM 🚨")
    print("=" * 50)
    print()
    print("This tool posts accidents directly to your channel")
    print("using your @Accident_try_bot")
    print()
    
    # Test channel access first
    if test_channel_access():
        print("\n🎯 Bot access confirmed! Ready to post accidents.")
        interactive_mode()
    else:
        print("\n❌ Bot cannot access your channel yet.")
        show_bot_setup_instructions()

if __name__ == "__main__":
    main()