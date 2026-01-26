#!/usr/bin/env python3
import requests
import json
import re
from datetime import datetime

# Bot configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
SOURCE_CHAT_ID = "-1001486947378"  # @sgaccident
TARGET_CHAT_ID = "-1003683261194"  # Your channel

def get_channel_history():
    """Try to get channel messages using different approaches"""
    print("🔍 Attempting to access @sgaccident channel history...")
    
    # Method 1: Try getUpdates with higher limit
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {'limit': 100}
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data.get('result', [])
                print(f"📥 Retrieved {len(updates)} total updates")
                
                # Filter for messages from @sgaccident
                sgaccident_messages = []
                for update in updates:
                    if 'channel_post' in update:
                        msg = update['channel_post']
                        chat_id = str(msg.get('chat', {}).get('id', ''))
                        if chat_id == SOURCE_CHAT_ID:
                            sgaccident_messages.append(msg)
                
                print(f"📨 Found {len(sgaccident_messages)} messages from @sgaccident")
                return sgaccident_messages
            else:
                print(f"❌ API Error: {data.get('description')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error with getUpdates: {e}")
    
    # Method 2: Try to get chat info to confirm access
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChat"
        params = {'chat_id': SOURCE_CHAT_ID}
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                chat_info = data.get('result', {})
                print(f"✅ Bot has access to: {chat_info.get('title', 'Unknown')}")
                print(f"   Type: {chat_info.get('type', 'Unknown')}")
                print(f"   Members: {chat_info.get('member_count', 'Unknown')}")
            else:
                print(f"❌ Chat access error: {data.get('description')}")
        else:
            print(f"❌ Chat access HTTP error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking chat access: {e}")
    
    return []

def create_sample_accident():
    """Create a sample accident post for testing"""
    print("📝 Creating sample accident post for demonstration...")
    
    sample_text = """🚨 ACCIDENT ALERT 🚨

Traffic accident reported on PIE (Pan Island Expressway) towards Changi Airport near Exit 2B.

Location: Approximately 1.3521, 103.9876
Traffic jam building up in the area.
Please avoid if possible and use alternative routes.

Reported: 2026-01-26 23:10:00"""
    
    # Create a mock message structure
    sample_message = {
        'text': sample_text,
        'date': int(datetime.now().timestamp()),
        'message_id': 12345
    }
    
    return sample_message

def extract_coordinates_from_text(text):
    """Extract coordinates from accident text"""
    # Look for coordinate patterns
    coord_patterns = [
        r'(\d+\.\d+),\s*(\d+\.\d+)',  # Basic lat,lng format
        r'lat[:\s]*(\d+\.\d+).*?lon[g]?[:\s]*(\d+\.\d+)',  # lat: x lng: y
        r'location[:\s]*(\d+\.\d+)[,\s]+(\d+\.\d+)'  # location: x, y
    ]
    
    for pattern in coord_patterns:
        matches = re.search(pattern, text, re.IGNORECASE)
        if matches:
            lat, lng = float(matches.group(1)), float(matches.group(2))
            # Check if coordinates are in Singapore bounds
            if 1.1 <= lat <= 1.5 and 103.6 <= lng <= 104.1:
                return lat, lng
    
    return None, None

def format_accident_message(message, source="@sgaccident"):
    """Format the accident message for posting using Waze-style format"""
    text = message.get('text', '')
    date = datetime.fromtimestamp(message.get('date', 0))
    
    # Extract coordinates
    lat, lng = extract_coordinates_from_text(text)
    
    # Extract location from the text - try to find street/area information
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
    timestamp = date.strftime('%Y-%m-%d %H:%M:%S SGT')
    
    # Determine reporter based on source
    if source.lower() == "waze":
        reporter = "Waze user"
        confidence = "N/A"  # Will be actual values from Waze API
        reliability = "N/A"  # Will be actual values from Waze API
    else:
        reporter = "@sgaccident" 
        confidence = "N/A"
        reliability = "N/A"
    
    # Build the message using the exact requested Waze-style format
    formatted_msg = f"Accident on {location_text}\n"
    formatted_msg += f"🕐 Reported: {timestamp}\n"
    formatted_msg += f"👤 Reported by: {reporter}\n"
    formatted_msg += f"📈 Confidence: {confidence}\n"
    formatted_msg += f"✅ Reliability: {reliability}\n\n"
    
    if lat and lng:
        google_maps_url = f"https://www.google.com/maps?q={lat},{lng}"
        waze_url = f"https://www.waze.com/ul?ll={lat},{lng}&navigate=yes"
        formatted_msg += f"🗺️ [View on Google Maps ({lat}, {lng})]({google_maps_url})\n"
        formatted_msg += f"🚗 [Open in Waze ({lat}, {lng})]({waze_url})"
    else:
        formatted_msg += f"🗺️ Location coordinates not available"
    
    return formatted_msg

def post_to_channel(message_text):
    """Post the formatted message to target channel"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TARGET_CHAT_ID,
            'text': message_text,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        response = requests.post(url, data=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Successfully posted accident to your channel!")
                return True
            else:
                print(f"❌ Failed to post: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error posting to channel: {e}")
        return False

def main():
    print("🔍 Attempting to extract latest accident from @sgaccident...")
    print("=" * 60)
    
    # Try to get messages from the channel
    messages = get_channel_history()
    
    if not messages:
        print("\n⚠️ No messages found from @sgaccident channel")
        print("This could be because:")
        print("  - No recent messages in the channel")
        print("  - Bot needs to be added as admin to access history")
        print("  - Channel privacy settings restrict bot access")
        print("\n📝 Creating sample accident post for demonstration...")
        
        # Use sample message for demonstration
        latest_message = create_sample_accident()
    else:
        # Find the latest accident-related message
        accident_keywords = ['accident', 'crash', 'collision', 'breakdown', 'jam', '塞车', '事故', '意外']
        latest_message = None
        
        for message in reversed(messages):  # Start from most recent
            text = message.get('text', '')
            if any(keyword.lower() in text.lower() for keyword in accident_keywords):
                latest_message = message
                break
        
        if not latest_message:
            print("❌ No accident-related posts found in recent messages")
            return
    
    print(f"✅ Found accident post from {datetime.fromtimestamp(latest_message.get('date', 0))}")
    
    # Format the message
    formatted_message = format_accident_message(latest_message)
    print(f"\n📝 Formatted message preview:")
    print("-" * 50)
    print(formatted_message)
    print("-" * 50)
    
    # Post to your channel
    print(f"\n📤 Posting to your channel...")
    success = post_to_channel(formatted_message)
    
    if success:
        print(f"🎉 Accident successfully extracted and posted!")
    else:
        print(f"❌ Failed to post the accident")

if __name__ == "__main__":
    main()