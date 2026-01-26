#!/usr/bin/env python3
import requests
import json
import re
from datetime import datetime

# Bot configuration
BOT_TOKEN = "8306581686:AAFWGxVmhfvSXU2OCO5DsxyrEkxdBqGvgiQ"
SOURCE_CHAT_ID = "-1001486947378"  # @sgaccident
TARGET_CHAT_ID = "-1003683261194"  # Your channel

def get_latest_accident():
    """Get the latest message from @sgaccident channel"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
        params = {
            'chat_id': SOURCE_CHAT_ID,
            'limit': 100,
            'offset': -100
        }
        
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"❌ Failed to get updates: {response.status_code}")
            return None
            
        data = response.json()
        if not data.get('ok'):
            print(f"❌ API Error: {data.get('description')}")
            return None
            
        # Find the latest accident-related message
        updates = data.get('result', [])
        for update in reversed(updates):  # Start from most recent
            if 'channel_post' in update:
                message = update['channel_post']
                text = message.get('text', '')
                
                # Check if it's an accident-related message
                accident_keywords = ['accident', 'crash', 'collision', 'breakdown', 'jam', '塞车', '事故', '意外']
                if any(keyword.lower() in text.lower() for keyword in accident_keywords):
                    return message
                    
        print("❌ No recent accident posts found")
        return None
        
    except Exception as e:
        print(f"❌ Error getting latest accident: {e}")
        return None

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

def format_accident_message(message):
    """Format the accident message for posting"""
    text = message.get('text', '')
    date = datetime.fromtimestamp(message.get('date', 0))
    
    # Extract coordinates
    lat, lng = extract_coordinates_from_text(text)
    
    # Format the message
    formatted_msg = f"🚨 <b>ACCIDENT ALERT</b> 🚨\n\n"
    formatted_msg += f"📄 <b>Details:</b> {text}\n"
    formatted_msg += f"⏰ <b>Time:</b> {date.strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    if lat and lng:
        google_maps_url = f"https://maps.google.com/?q={lat},{lng}"
        waze_url = f"https://waze.com/ul?ll={lat},{lng}&navigate=yes"
        formatted_msg += f"🗺️ <b>Coordinates:</b> {lat}, {lng}\n"
        formatted_msg += f"🔗 <b>Google Maps:</b> <a href='{google_maps_url}'>Open Location</a>\n"
        formatted_msg += f"🚗 <b>Waze:</b> <a href='{waze_url}'>Navigate</a>\n"
    
    formatted_msg += f"🔗 <b>Source:</b> @sgaccident Channel"
    
    return formatted_msg

def post_to_channel(message_text):
    """Post the formatted message to target channel"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TARGET_CHAT_ID,
            'text': message_text,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
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
            return False
            
    except Exception as e:
        print(f"❌ Error posting to channel: {e}")
        return False

def main():
    print("🔍 Extracting latest accident from @sgaccident...")
    
    # Get the latest accident post
    latest_message = get_latest_accident()
    if not latest_message:
        return
    
    print(f"✅ Found accident post from {datetime.fromtimestamp(latest_message.get('date', 0))}")
    
    # Format the message
    formatted_message = format_accident_message(latest_message)
    print(f"\n📝 Formatted message preview:")
    print("-" * 50)
    print(formatted_message[:200] + "..." if len(formatted_message) > 200 else formatted_message)
    print("-" * 50)
    
    # Post to your channel
    print(f"\n📤 Posting to your channel...")
    success = post_to_channel(formatted_message)
    
    if success:
        print(f"🎉 Latest accident successfully extracted and posted!")
    else:
        print(f"❌ Failed to post the accident")

if __name__ == "__main__":
    main()